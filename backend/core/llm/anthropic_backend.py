"""Anthropic backend using the official SDK.

Streaming is read for incremental text, then ``get_final_message()`` supplies
the authoritative content blocks. Letting the SDK assemble ``tool_use`` inputs
avoids hand-parsing partial JSON deltas, which is the usual source of subtle
tool-calling bugs.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from backend.core.llm.base import (
    Completion,
    LLMBackend,
    LLMError,
    TextChunk,
    ThinkingChunk,
    TokenUsage,
    ToolCall,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"
MAX_RETRIES = 3
# Overload/rate-limit responses are worth retrying; 4xx generally are not.
RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}


class AnthropicBackend(LLMBackend):
    provider = "anthropic"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 600.0,
    ) -> None:
        try:
            import anthropic  # noqa: PLC0415 - optional dependency
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "The 'anthropic' package is not installed. Run: pip install anthropic"
            ) from exc

        if not api_key:
            raise LLMError(
                "No Anthropic API key. Set ANTHROPIC_API_KEY in your .env "
                "(it must be a real key starting with 'sk-ant-')."
            )

        self._anthropic = anthropic
        self.model = model or DEFAULT_MODEL
        kwargs: Dict[str, Any] = {"api_key": api_key, "timeout": timeout, "max_retries": 0}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = anthropic.AsyncAnthropic(**kwargs)

    # ------------------------------------------------------------------ utils #

    def _system_blocks(self, system: str) -> List[Dict[str, Any]]:
        """Mark the system prompt cacheable.

        The system prompt and tool schemas are identical on every step of a
        turn, so caching them cuts both latency and cost substantially over a
        long multi-tool trajectory.
        """
        if not system:
            return []
        return [{
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }]

    @staticmethod
    def _cacheable_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not tools:
            return []
        prepared = [dict(t) for t in tools]
        # A cache breakpoint on the final tool covers the whole tool block.
        prepared[-1]["cache_control"] = {"type": "ephemeral"}
        return prepared

    def _classify(self, exc: Exception) -> LLMError:
        anthropic = self._anthropic
        status = getattr(exc, "status_code", None)

        if isinstance(exc, getattr(anthropic, "AuthenticationError", ())):
            return LLMError(
                "Anthropic rejected the API key (401). Check ANTHROPIC_API_KEY in "
                "your .env -- a real key starts with 'sk-ant-'.",
                status=401,
            )
        if isinstance(exc, getattr(anthropic, "NotFoundError", ())):
            return LLMError(
                f"Model '{self.model}' was not found (404). Set JARVIS_MODEL to a "
                "model your account can access, e.g. claude-sonnet-5.",
                status=404,
            )
        if isinstance(exc, getattr(anthropic, "RateLimitError", ())):
            return LLMError("Rate limited by Anthropic (429).", retryable=True, status=429)
        if isinstance(exc, getattr(anthropic, "APIConnectionError", ())):
            return LLMError(f"Could not reach Anthropic: {exc}", retryable=True)
        if isinstance(status, int):
            return LLMError(f"Anthropic API error {status}: {exc}",
                            retryable=status in RETRYABLE_STATUS, status=status)
        return LLMError(f"Anthropic request failed: {exc}")

    # ----------------------------------------------------------------- stream #

    async def stream(
        self,
        *,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Any]:
        request: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            request["system"] = self._system_blocks(system)
        if tools:
            request["tools"] = self._cacheable_tools(tools)
        if temperature is not None:
            request["temperature"] = temperature

        last_error: Optional[LLMError] = None

        for attempt in range(MAX_RETRIES):
            emitted_any = False
            try:
                async with self.client.messages.stream(**request) as stream:
                    async for event in stream:
                        etype = getattr(event, "type", "")
                        if etype != "content_block_delta":
                            continue
                        delta = getattr(event, "delta", None)
                        dtype = getattr(delta, "type", "")
                        if dtype == "text_delta":
                            text = getattr(delta, "text", "")
                            if text:
                                emitted_any = True
                                yield TextChunk(text)
                        elif dtype == "thinking_delta":
                            thought = getattr(delta, "thinking", "")
                            if thought:
                                emitted_any = True
                                yield ThinkingChunk(thought)

                    final = await stream.get_final_message()

                yield self._to_completion(final)
                return

            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                err = self._classify(exc)
                last_error = err
                # Retrying after partial output would duplicate text on screen.
                if not err.retryable or emitted_any or attempt == MAX_RETRIES - 1:
                    raise err from exc
                backoff = 2 ** attempt
                logger.warning(
                    "Anthropic call failed (%s); retrying in %ss", err, backoff
                )
                await asyncio.sleep(backoff)

        raise last_error or LLMError("Anthropic request failed.")

    # ------------------------------------------------------------ conversion #

    @staticmethod
    def _to_completion(message: Any) -> Completion:
        blocks: List[Dict[str, Any]] = []
        calls: List[ToolCall] = []
        text_parts: List[str] = []

        for block in getattr(message, "content", []) or []:
            btype = getattr(block, "type", "")
            if btype == "text":
                body = getattr(block, "text", "")
                text_parts.append(body)
                blocks.append({"type": "text", "text": body})
            elif btype == "tool_use":
                args = getattr(block, "input", None)
                args = args if isinstance(args, dict) else {}
                call_id = getattr(block, "id", "")
                name = getattr(block, "name", "")
                calls.append(ToolCall(id=call_id, name=name, args=args))
                blocks.append({
                    "type": "tool_use", "id": call_id, "name": name, "input": args,
                })
            elif btype == "thinking":
                # Preserved verbatim: Anthropic requires thinking blocks to be
                # echoed back unmodified when the turn continues.
                blocks.append({
                    "type": "thinking",
                    "thinking": getattr(block, "thinking", ""),
                    "signature": getattr(block, "signature", ""),
                })
            elif btype == "redacted_thinking":
                blocks.append({
                    "type": "redacted_thinking",
                    "data": getattr(block, "data", ""),
                })

        raw = getattr(message, "usage", None)
        usage = TokenUsage(
            input_tokens=getattr(raw, "input_tokens", 0) or 0,
            output_tokens=getattr(raw, "output_tokens", 0) or 0,
            cache_read=getattr(raw, "cache_read_input_tokens", 0) or 0,
            cache_write=getattr(raw, "cache_creation_input_tokens", 0) or 0,
        )

        return Completion(
            content=blocks,
            tool_calls=calls,
            text="".join(text_parts),
            stop_reason=getattr(message, "stop_reason", "end_turn") or "end_turn",
            usage=usage,
        )

    async def close(self) -> None:
        try:
            await self.client.close()
        except Exception:  # noqa: BLE001
            pass
