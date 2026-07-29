"""OpenAI-compatible backend using the official `openai` SDK or httpx.

Translates normalized Anthropic-style message schema to/from OpenAI format
so that Open-Source endpoints (Ollama, vLLM), OpenAI, Gemini, and proxy routers work seamlessly.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from backend.core.llm.base import (
    Completion,
    LLMBackend,
    LLMError,
    TextChunk,
    TokenUsage,
    ToolCall,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
MAX_RETRIES = 3
RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}


class OpenAIBackend(LLMBackend):
    provider = "openai"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 600.0,
    ) -> None:
        try:
            import openai
        except ImportError as exc:
            raise LLMError("The 'openai' package is not installed. Run: pip install openai") from exc

        self.model = model or DEFAULT_MODEL
        self.base_url = base_url
        self._openai = openai
        kwargs: Dict[str, Any] = {"api_key": api_key or "none", "timeout": timeout, "max_retries": 0}
        if base_url:
            kwargs["base_url"] = base_url

        self._client = openai.AsyncOpenAI(**kwargs)

    def _classify(self, exc: Exception) -> LLMError:
        """Map SDK exceptions onto LLMError, marking only transient ones retryable."""
        openai = self._openai
        where = self.base_url or "the OpenAI API"
        status = getattr(exc, "status_code", None)

        if isinstance(exc, getattr(openai, "AuthenticationError", ())):
            return LLMError(
                f"{where} rejected the API key (401). Check OPENAI_API_KEY in your .env.",
                status=401,
            )
        if isinstance(exc, getattr(openai, "NotFoundError", ())):
            return LLMError(
                f"Model '{self.model}' is not available at {where} (404). "
                "Set JARVIS_MODEL to a model this endpoint serves.",
                status=404,
            )
        if isinstance(exc, getattr(openai, "RateLimitError", ())):
            return LLMError(f"Rate limited by {where} (429).", retryable=True, status=429)
        if isinstance(exc, getattr(openai, "APIConnectionError", ())):
            return LLMError(f"Could not reach {where}: {exc}", retryable=True)
        if isinstance(status, int):
            return LLMError(
                f"{where} returned {status}: {exc}",
                retryable=status in RETRYABLE_STATUS,
                status=status,
            )
        return LLMError(f"Request to {where} failed: {type(exc).__name__}: {exc}")

    async def stream(
        self,
        *,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Any]:
        # Convert Anthropic message format to OpenAI format
        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if isinstance(content, str):
                oai_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Handle blocks (text, tool_use, tool_result)
                text_parts = []
                tool_calls = []
                for block in content:
                    btype = block.get("type")
                    if btype == "text":
                        text_parts.append(block.get("text", ""))
                    elif btype == "tool_use":
                        tool_calls.append({
                            "id": block.get("id"),
                            "type": "function",
                            "function": {
                                "name": block.get("name"),
                                "arguments": json.dumps(block.get("input", {}))
                            }
                        })
                    elif btype == "tool_result":
                        oai_messages.append({
                            "role": "tool",
                            "tool_call_id": block.get("tool_use_id"),
                            "content": str(block.get("content", ""))
                        })

                if text_parts or tool_calls:
                    # Empty string content is rejected by some gateways when
                    # tool_calls are present; omit it rather than send "".
                    m: Dict[str, Any] = {"role": role, "content": "\n".join(text_parts) or None}
                    if tool_calls:
                        m["tool_calls"] = tool_calls
                    oai_messages.append(m)

        # Convert Anthropic tool schemas to OpenAI tool schemas
        oai_tools = None
        if tools:
            oai_tools = []
            for t in tools:
                oai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.get("name"),
                        "description": t.get("description", ""),
                        "parameters": t.get("input_schema", {})
                    }
                })

        params: Dict[str, Any] = {
            "model": self.model,
            "messages": oai_messages,
            "stream": True,
            "max_tokens": max_tokens,
        }
        if oai_tools:
            params["tools"] = oai_tools
        if temperature is not None:
            params["temperature"] = temperature
        if not self.base_url:
            # Only OpenAI proper is guaranteed to accept this; third-party
            # gateways often 400 on unknown parameters, so don't send it there.
            params["stream_options"] = {"include_usage": True}

        last_error: Optional[LLMError] = None
        for attempt in range(MAX_RETRIES):
            emitted_any = False
            try:
                response = await self._client.chat.completions.create(**params)
                accumulated_text = ""
                collected_tool_calls: Dict[int, Dict[str, Any]] = {}
                usage = TokenUsage()
                stop_reason = "end_turn"

                async for chunk in response:
                    raw_usage = getattr(chunk, "usage", None)
                    if raw_usage is not None:
                        usage = TokenUsage(
                            input_tokens=getattr(raw_usage, "prompt_tokens", 0) or 0,
                            output_tokens=getattr(raw_usage, "completion_tokens", 0) or 0,
                        )
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]

                    finish = getattr(choice, "finish_reason", None)
                    if finish in ("length", "max_tokens"):
                        stop_reason = "max_tokens"

                    delta = choice.delta
                    if delta is None:
                        continue

                    if delta.content:
                        emitted_any = True
                        accumulated_text += delta.content
                        yield TextChunk(text=delta.content)

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index or 0
                            slot = collected_tool_calls.setdefault(
                                idx, {"id": "", "name": "", "args": ""}
                            )
                            if tc.id:
                                slot["id"] = tc.id
                            if tc.function is None:
                                continue
                            if tc.function.name:
                                slot["name"] = tc.function.name
                            if tc.function.arguments:
                                slot["args"] += tc.function.arguments

                # Finalize ToolCalls
                final_tool_calls = []
                content_blocks: List[Dict[str, Any]] = []
                if accumulated_text:
                    content_blocks.append({"type": "text", "text": accumulated_text})

                for idx in sorted(collected_tool_calls.keys()):
                    tdata = collected_tool_calls[idx]
                    if not tdata["name"]:
                        continue
                    raw_args = (tdata["args"] or "").strip() or "{}"
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        # Surface the bad payload so the tool layer can reject it
                        # with a message the model can act on. Silently passing
                        # {} would make the call look valid but behave wrongly.
                        logger.warning(
                            "Un-parseable arguments for %s: %r", tdata["name"], raw_args
                        )
                        args = {"__malformed_arguments__": raw_args}
                    if not isinstance(args, dict):
                        args = {"__malformed_arguments__": raw_args}

                    tc_obj = ToolCall(
                        id=tdata["id"] or f"call_{idx}", name=tdata["name"], args=args
                    )
                    final_tool_calls.append(tc_obj)
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc_obj.id,
                        "name": tc_obj.name,
                        "input": tc_obj.args
                    })

                yield Completion(
                    content=content_blocks,
                    tool_calls=final_tool_calls,
                    text=accumulated_text,
                    stop_reason="tool_use" if final_tool_calls else stop_reason,
                    usage=usage
                )
                return

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                err = self._classify(exc)
                last_error = err
                # Never retry a permanent failure, and never retry once text has
                # already been shown to the user -- that would duplicate output.
                if not err.retryable or emitted_any or attempt == MAX_RETRIES - 1:
                    raise err from exc
                backoff = 2 ** attempt
                logger.warning("LLM call failed (%s); retrying in %ss", err, backoff)
                await asyncio.sleep(backoff)

        raise last_error or LLMError("OpenAI-compatible request failed.")

    async def close(self) -> None:
        await self._client.close()
