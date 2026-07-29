"""Read a file from the workspace."""

from __future__ import annotations

from typing import Any, Dict

from backend.core.tools.base import (
    Permission,
    Tool,
    ToolContext,
    ToolError,
    ToolResult,
    display_path,
    looks_binary,
    resolve_path,
    truncate,
)

MAX_CHARS = 60_000
DEFAULT_LINE_LIMIT = 2000
MAX_LINE_WIDTH = 2000


class ReadTool(Tool):
    name = "read_file"
    description = (
        "Read the contents of a file in the workspace. Output is prefixed with "
        "line numbers, which you should use when constructing edits (do NOT "
        "include the line-number prefix in edit strings). Use offset and limit "
        "to page through large files. Always read a file before editing it."
    )
    permission = Permission.ALLOW
    read_only = True

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file, absolute or relative to the workspace.",
                },
                "offset": {
                    "type": "integer",
                    "description": "1-based line number to start reading from.",
                    "minimum": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": f"Maximum number of lines to read (default {DEFAULT_LINE_LIMIT}).",
                    "minimum": 1,
                },
            },
            "required": ["path"],
        }

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        target = args.get("path", "?")
        offset, limit = args.get("offset"), args.get("limit")
        if offset or limit:
            return f"Read({target}, offset={offset or 1}, limit={limit or DEFAULT_LINE_LIMIT})"
        return f"Read({target})"

    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        path = resolve_path(args.get("path", ""), ctx, must_exist=True)

        if path.is_dir():
            raise ToolError(
                f"{display_path(path, ctx)} is a directory, not a file. "
                "Use glob or grep to explore directories."
            )
        if looks_binary(path):
            size = path.stat().st_size
            raise ToolError(
                f"{display_path(path, ctx)} appears to be a binary file "
                f"({size} bytes) and cannot be read as text."
            )

        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ToolError(f"Could not read {display_path(path, ctx)}: {exc}") from exc

        ctx.mark_read(path)

        if not raw:
            return ToolResult(
                content=f"{display_path(path, ctx)} exists but is empty (0 bytes).",
                display={"path": display_path(path, ctx), "lines": 0, "empty": True},
            )

        lines = raw.splitlines()
        total = len(lines)
        offset = max(1, int(args.get("offset") or 1))
        limit = int(args.get("limit") or DEFAULT_LINE_LIMIT)

        if offset > total:
            raise ToolError(
                f"offset {offset} is past the end of {display_path(path, ctx)} "
                f"({total} lines)."
            )

        window = lines[offset - 1 : offset - 1 + limit]
        numbered = []
        for idx, line in enumerate(window, start=offset):
            if len(line) > MAX_LINE_WIDTH:
                line = line[:MAX_LINE_WIDTH] + f"... [line truncated, {len(line)} chars]"
            numbered.append(f"{idx}\t{line}")

        body = "\n".join(numbered)
        shown_to = offset - 1 + len(window)
        footer = ""
        if shown_to < total:
            footer = (
                f"\n\n[showing lines {offset}-{shown_to} of {total}; "
                f"continue with offset={shown_to + 1}]"
            )

        return ToolResult(
            content=truncate(body, MAX_CHARS, note="file content") + footer,
            display={
                "path": display_path(path, ctx),
                "lines": total,
                "from": offset,
                "to": shown_to,
                "content": body,
            },
        )
