"""The core tool-use loop of Jarvis Agent.

Executes turns driven by LLM tool calls against real workspace tools and shell,
gated by user permission checks and emitting normalized events for CLI & Web UI.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from backend.core.events import (
    AgentEvent,
    EventType,
    error as ev_error,
    interrupted as ev_interrupted,
    text_delta as ev_text_delta,
    thinking_delta as ev_thinking_delta,
    tool_end as ev_tool_end,
    tool_start as ev_tool_start,
    turn_complete as ev_turn_complete,
)
from backend.core.llm.base import Completion, LLMBackend, TextChunk, ThinkingChunk, ToolCall
from backend.core.permissions import Decision, PermissionBroker
from backend.core.prompt import build_system_prompt
from backend.core.session import AgentSession
from backend.core.tools.base import ToolResult
from backend.core.tools.registry import ToolBox

logger = logging.getLogger(__name__)


class AgentLoop:
    """Manages multi-step tool-execution turns for an AgentSession."""

    def __init__(
        self,
        session: AgentSession,
        llm: LLMBackend,
        tools: ToolBox,
        permissions: PermissionBroker,
        max_steps: int = 25,
    ) -> None:
        self.session = session
        self.llm = llm
        self.tools = tools
        self.permissions = permissions
        self.max_steps = max_steps
        self._interrupt_event = asyncio.Event()

    def interrupt(self) -> None:
        """Signal the agent to stop the current turn at the next boundary."""
        self._interrupt_event.set()

    async def run_turn(self, user_text: str) -> AsyncIterator[AgentEvent]:
        """Execute a full turn, streaming text, tool calls, and results."""
        self._interrupt_event.clear()

        if user_text:
            self.session.add_user_message(user_text)
            yield AgentEvent(type=EventType.NOTICE, data={"text": user_text})

        system_prompt = build_system_prompt(self.session.workspace)
        tool_schemas = self.tools.schemas()

        for step in range(1, self.max_steps + 1):
            if self._interrupt_event.is_set():
                yield ev_interrupted()
                return

            # Stream from LLM
            collected_text = ""
            completion: Optional[Completion] = None

            try:
                async for event in self.llm.stream(
                    system=system_prompt,
                    messages=self.session.messages,
                    tools=tool_schemas,
                ):
                    if self._interrupt_event.is_set():
                        yield ev_interrupted()
                        return

                    if isinstance(event, TextChunk):
                        collected_text += event.text
                        yield ev_text_delta(event.text)
                    elif isinstance(event, ThinkingChunk):
                        yield ev_thinking_delta(event.text)
                    elif isinstance(event, Completion):
                        completion = event

            except Exception as exc:
                logger.error(f"Error streaming from LLM in step {step}: {exc}", exc_info=True)
                yield ev_error(str(exc))
                return

            if not completion:
                yield ev_error("No completion received from LLM")
                return

            # Record token usage
            if completion.usage:
                self.session.usage.add(
                    model=self.llm.model,
                    input_tokens=getattr(completion.usage, "input_tokens", 0),
                    output_tokens=getattr(completion.usage, "output_tokens", 0),
                    cache_read=getattr(completion.usage, "cache_read", 0),
                    cache_write=getattr(completion.usage, "cache_write", 0),
                )

            # Append assistant message to history
            self.session.add_assistant_message(completion.content)

            # If no tool calls, the turn is complete
            if not completion.tool_calls:
                yield ev_turn_complete("end_turn", step)
                return

            # Execute tool calls
            tool_results_blocks = []

            for call in completion.tool_calls:
                if self._interrupt_event.is_set():
                    yield ev_interrupted()
                    return

                tool_obj = self.tools.get(call.name)
                if not tool_obj:
                    err_msg = f"Unknown tool: {call.name}"
                    yield ev_tool_end(call.id, call.name, is_error=True, content=err_msg)
                    continue

                yield ev_tool_start(call.id, call.name, "", call.args)

                # Check permission
                if self.permissions.needs_approval(tool_obj, call.args):
                    decision = await self.permissions.request(tool_obj, call.args, "", f"Tool call: {call.name}")
                    if decision == Decision.DENY:
                        res_content = "Error: Permission denied by user."
                        yield ev_tool_end(call.id, call.name, is_error=True, content=res_content)
                        tool_results_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": call.id,
                            "content": res_content,
                            "is_error": True
                        })
                        continue

                # Execute tool
                ctx = self.session.tool_ctx
                try:
                    res: ToolResult = await tool_obj.run(call.args, ctx)

                    out_str = res.content if isinstance(res.content, str) else str(res.content)
                    yield ev_tool_end(call.id, call.name, is_error=res.is_error, content=out_str)

                    tool_results_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": out_str,
                        "is_error": res.is_error
                    })

                except Exception as tool_exc:
                    err_msg = f"Error executing tool {call.name}: {tool_exc}"
                    yield ev_tool_end(call.id, call.name, is_error=True, content=err_msg)
                    tool_results_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": err_msg,
                        "is_error": True
                    })

            # Append tool results turn to message history
            self.session.add_tool_results(tool_results_blocks)

        yield ev_turn_complete("max_steps_reached", self.max_steps)
