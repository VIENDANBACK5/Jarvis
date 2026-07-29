"""Task list the agent maintains while working.

Holding the plan in a structured list rather than prose gives the user a live
view of what the agent thinks it is doing, and gives the model a place to record
progress across a long multi-step turn.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.core.tools.base import (
    Permission,
    Tool,
    ToolContext,
    ToolError,
    ToolResult,
)

STATUSES = ("pending", "in_progress", "completed")
MARKS = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}


class TodoTool(Tool):
    name = "update_todos"
    description = (
        "Record and update your task list for the current piece of work. Send the "
        "complete list every time -- it replaces the previous one. Use this for "
        "multi-step work: create the list up front, mark exactly one task "
        "in_progress before you start it, and mark it completed as soon as it is "
        "genuinely done. Skip it for single-step requests."
    )
    permission = Permission.ALLOW
    read_only = True

    def __init__(self) -> None:
        self.todos: List[Dict[str, str]] = []

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "description": "The full task list, in order.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Imperative description, e.g. 'Add the retry helper'.",
                            },
                            "status": {
                                "type": "string",
                                "enum": list(STATUSES),
                            },
                        },
                        "required": ["content", "status"],
                    },
                }
            },
            "required": ["todos"],
        }

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        items = args.get("todos") or []
        done = sum(1 for t in items if isinstance(t, dict) and t.get("status") == "completed")
        return f"Todos({done}/{len(items)} done)"

    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        raw = args.get("todos")
        if not isinstance(raw, list):
            raise ToolError("'todos' must be an array of {content, status} objects.")

        cleaned: List[Dict[str, str]] = []
        for entry in raw:
            if not isinstance(entry, dict):
                raise ToolError("Each todo must be an object with 'content' and 'status'.")
            content = str(entry.get("content") or "").strip()
            status = str(entry.get("status") or "pending").strip()
            if not content:
                raise ToolError("A todo's 'content' must not be empty.")
            if status not in STATUSES:
                raise ToolError(
                    f"Invalid status '{status}' for '{content}'. "
                    f"Use one of: {', '.join(STATUSES)}."
                )
            cleaned.append({"content": content, "status": status})

        active = [t for t in cleaned if t["status"] == "in_progress"]
        if len(active) > 1:
            raise ToolError(
                f"{len(active)} tasks are marked in_progress. Keep exactly one "
                "in_progress at a time so progress stays legible."
            )

        self.todos = cleaned
        done = sum(1 for t in cleaned if t["status"] == "completed")
        rendered = "\n".join(f"{MARKS[t['status']]} {t['content']}" for t in cleaned)

        return ToolResult(
            content=(
                f"Task list updated ({done}/{len(cleaned)} complete):\n{rendered}"
                if cleaned
                else "Task list cleared."
            ),
            display={"todos": cleaned, "completed": done, "total": len(cleaned)},
        )
