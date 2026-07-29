"""Session state: conversation history, workspace, and cost accounting."""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.tools.base import ToolContext

logger = logging.getLogger(__name__)

# Rough USD per million tokens. Used for a live cost readout only; treat the
# numbers as indicative, not billing-accurate.
PRICING: Dict[str, Dict[str, float]] = {
    "opus":   {"input": 5.00,  "output": 25.00, "cache_read": 0.50,  "cache_write": 6.25},
    "sonnet": {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    "haiku":  {"input": 0.80,  "output": 4.00,  "cache_read": 0.08,  "cache_write": 1.00},
    "default": {"input": 3.00, "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
}


def pricing_for(model: str) -> Dict[str, float]:
    lowered = (model or "").lower()
    for key in ("opus", "sonnet", "haiku"):
        if key in lowered:
            return PRICING[key]
    return PRICING["default"]


class Usage:
    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read = 0
        self.cache_write = 0
        self.cost_usd = 0.0
        self.requests = 0

    def add(
        self,
        model: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read: int = 0,
        cache_write: int = 0,
    ) -> float:
        rates = pricing_for(model)
        delta = (
            input_tokens * rates["input"]
            + output_tokens * rates["output"]
            + cache_read * rates["cache_read"]
            + cache_write * rates["cache_write"]
        ) / 1_000_000
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cache_read += cache_read
        self.cache_write += cache_write
        self.cost_usd += delta
        self.requests += 1
        return delta

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read": self.cache_read,
            "cache_write": self.cache_write,
            "cost_usd": round(self.cost_usd, 6),
            "requests": self.requests,
        }


class AgentSession:
    """One conversation against one workspace.

    ``messages`` is the provider-neutral history in Anthropic's content-block
    shape; the OpenAI-compatible backend translates it on the way out.
    """

    def __init__(
        self,
        workspace: Path | str,
        *,
        model: str = "",
        session_id: Optional[str] = None,
    ) -> None:
        self.session_id = session_id or f"sess-{uuid.uuid4().hex[:12]}"
        self.workspace = Path(workspace).expanduser().resolve()
        self.model = model
        self.created_at = time.time()
        self.messages: List[Dict[str, Any]] = []
        self.usage = Usage()
        self.todos: List[Dict[str, str]] = []
        self.tool_ctx = ToolContext(workspace=self.workspace, cwd=self.workspace)

    # ------------------------------------------------------------- history #

    def add_user_message(self, text: str) -> None:
        self.messages.append({
            "role": "user",
            "content": [{"type": "text", "text": text}],
        })

    def add_assistant_message(self, content: List[Dict[str, Any]]) -> None:
        if content:
            self.messages.append({"role": "assistant", "content": content})

    def add_tool_results(self, results: List[Dict[str, Any]]) -> None:
        """Tool results are a single user-role message holding tool_result blocks."""
        if results:
            self.messages.append({"role": "user", "content": results})

    def clear(self) -> None:
        self.messages.clear()
        self.todos.clear()
        self.tool_ctx.read_files.clear()

    # ---------------------------------------------------------- compaction #

    def estimated_tokens(self) -> int:
        """Cheap character-based estimate; avoids a tokenizer dependency."""
        total = 0
        for message in self.messages:
            content = message.get("content")
            if isinstance(content, str):
                total += len(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        total += len(json.dumps(block, default=str))
        return total // 4

    def compact(self, keep_recent: int = 6) -> int:
        """Drop the middle of a long history, keeping the opening and the tail.

        Crude but safe: the first user message carries the task, the tail carries
        current state. Messages are removed in whole role-turns and we never cut
        between an assistant tool_use and its matching tool_result, which would
        make the history invalid.
        """
        if len(self.messages) <= keep_recent + 2:
            return 0

        head = self.messages[:1]
        tail_start = len(self.messages) - keep_recent

        # Never start the tail on a tool_result orphaned from its tool_use.
        while tail_start < len(self.messages):
            first = self.messages[tail_start]
            blocks = first.get("content")
            has_orphan_result = isinstance(blocks, list) and any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks
            )
            if has_orphan_result:
                tail_start += 1
            else:
                break

        dropped = self.messages[1:tail_start]
        if not dropped:
            return 0

        summary = {
            "role": "user",
            "content": [{
                "type": "text",
                "text": (
                    f"[Earlier conversation trimmed to save context: "
                    f"{len(dropped)} message(s) removed. Re-read any file you need "
                    f"rather than relying on memory of its contents.]"
                ),
            }],
        }
        self.messages = head + [summary] + self.messages[tail_start:]
        logger.info("Compacted session %s: dropped %d messages", self.session_id, len(dropped))
        return len(dropped)

    # ------------------------------------------------------------ persistence #

    def state_dir(self) -> Path:
        return self.workspace / ".jarvis" / "sessions"

    def save(self) -> Optional[Path]:
        try:
            directory = self.state_dir()
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"{self.session_id}.json"
            path.write_text(
                json.dumps(
                    {
                        "session_id": self.session_id,
                        "workspace": str(self.workspace),
                        "model": self.model,
                        "created_at": self.created_at,
                        "messages": self.messages,
                        "usage": self.usage.to_dict(),
                        "todos": self.todos,
                    },
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
            return path
        except OSError as exc:
            logger.warning("Could not save session %s: %s", self.session_id, exc)
            return None

    @classmethod
    def load(cls, path: Path | str) -> "AgentSession":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        session = cls(
            workspace=data["workspace"],
            model=data.get("model", ""),
            session_id=data.get("session_id"),
        )
        session.messages = data.get("messages", [])
        session.todos = data.get("todos", [])
        session.created_at = data.get("created_at", time.time())
        stored = data.get("usage") or {}
        session.usage.input_tokens = stored.get("input_tokens", 0)
        session.usage.output_tokens = stored.get("output_tokens", 0)
        session.usage.cost_usd = stored.get("cost_usd", 0.0)
        return session
