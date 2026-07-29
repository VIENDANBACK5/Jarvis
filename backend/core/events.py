"""Event taxonomy shared by the CLI and the web UI.

The agent loop is a generator of these. Both front-ends consume the same
stream, so anything the CLI can show the UI can show too.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    TURN_STARTED = "turn_started"
    # Assistant prose, streamed token by token.
    TEXT_DELTA = "text_delta"
    TEXT_DONE = "text_done"
    # Model's chain of thought, when the model emits it.
    THINKING_DELTA = "thinking_delta"
    # A tool the model wants to call / has called.
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    # Permission gate.
    PERMISSION_REQUEST = "permission_request"
    PERMISSION_RESOLVED = "permission_resolved"
    # Task list snapshot.
    TODOS = "todos"
    # Bookkeeping.
    USAGE = "usage"
    TURN_COMPLETE = "turn_complete"
    ERROR = "error"
    INTERRUPTED = "interrupted"
    NOTICE = "notice"


@dataclass
class AgentEvent:
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["type"] = self.type.value
        return payload


# --------------------------------------------------------------------------- #
# Constructors -- keeps event payload keys consistent across the codebase.
# --------------------------------------------------------------------------- #

def turn_started(step_budget: int) -> AgentEvent:
    return AgentEvent(EventType.TURN_STARTED, {"max_steps": step_budget})


def text_delta(text: str) -> AgentEvent:
    return AgentEvent(EventType.TEXT_DELTA, {"text": text})


def thinking_delta(text: str) -> AgentEvent:
    return AgentEvent(EventType.THINKING_DELTA, {"text": text})


def text_done(text: str) -> AgentEvent:
    return AgentEvent(EventType.TEXT_DONE, {"text": text})


def tool_start(call_id: str, name: str, preview: str, args: Dict[str, Any]) -> AgentEvent:
    return AgentEvent(
        EventType.TOOL_START,
        {"id": call_id, "name": name, "preview": preview, "args": args},
    )


def tool_end(
    call_id: str,
    name: str,
    *,
    is_error: bool,
    content: str,
    display: Optional[Dict[str, Any]] = None,
    duration_ms: int = 0,
) -> AgentEvent:
    return AgentEvent(
        EventType.TOOL_END,
        {
            "id": call_id,
            "name": name,
            "is_error": is_error,
            "content": content,
            "display": display or {},
            "duration_ms": duration_ms,
        },
    )


def permission_request(
    request_id: str,
    tool: str,
    preview: str,
    detail: str,
    args: Dict[str, Any],
) -> AgentEvent:
    return AgentEvent(
        EventType.PERMISSION_REQUEST,
        {
            "request_id": request_id,
            "tool": tool,
            "preview": preview,
            "detail": detail,
            "args": args,
        },
    )


def permission_resolved(request_id: str, decision: str, tool: str) -> AgentEvent:
    return AgentEvent(
        EventType.PERMISSION_RESOLVED,
        {"request_id": request_id, "decision": decision, "tool": tool},
    )


def todos(items: List[Dict[str, str]]) -> AgentEvent:
    return AgentEvent(EventType.TODOS, {"todos": items})


def usage(
    input_tokens: int,
    output_tokens: int,
    cache_read: int = 0,
    cache_write: int = 0,
    cost_usd: float = 0.0,
    totals: Optional[Dict[str, Any]] = None,
) -> AgentEvent:
    return AgentEvent(
        EventType.USAGE,
        {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read": cache_read,
            "cache_write": cache_write,
            "cost_usd": cost_usd,
            "totals": totals or {},
        },
    )


def turn_complete(reason: str, steps: int) -> AgentEvent:
    return AgentEvent(EventType.TURN_COMPLETE, {"reason": reason, "steps": steps})


def error(message: str, *, recoverable: bool = True) -> AgentEvent:
    return AgentEvent(EventType.ERROR, {"message": message, "recoverable": recoverable})


def interrupted() -> AgentEvent:
    return AgentEvent(EventType.INTERRUPTED, {})


def notice(message: str) -> AgentEvent:
    return AgentEvent(EventType.NOTICE, {"message": message})
