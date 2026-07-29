"""Create or overwrite a file."""

from __future__ import annotations

import difflib
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

MAX_PREVIEW = 8000


def unified_diff(before: str, after: str, label: str) -> str:
    """Git-style unified diff between two blobs of text."""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{label}",
            tofile=f"b/{label}",
            n=3,
        )
    )


class WriteTool(Tool):
    name = "write_file"
    description = (
        "Write content to a file, creating it if needed and overwriting it "
        "entirely if it already exists. Parent directories are created "
        "automatically. To overwrite an existing file you must read_file it "
        "first. Prefer edit_file for changes to existing files -- use this for "
        "new files or full rewrites."
    )
    permission = Permission.ASK
    read_only = False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to write, absolute or relative to the workspace.",
                },
                "content": {
                    "type": "string",
                    "description": "Full text content of the file.",
                },
            },
            "required": ["path", "content"],
        }

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        return f"Write({args.get('path', '?')})"

    def approval_detail(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        content = args.get("content") or ""
        try:
            path = resolve_path(args.get("path", ""), ctx)
        except ToolError:
            return truncate(content, MAX_PREVIEW, note="content")

        label = display_path(path, ctx)
        if path.exists() and not looks_binary(path):
            before = path.read_text(encoding="utf-8", errors="replace")
            diff = unified_diff(before, content, label)
            return truncate(diff or "(no textual change)", MAX_PREVIEW, note="diff")

        numbered = "\n".join(
            f"{i}\t{line}" for i, line in enumerate(content.splitlines(), 1)
        )
        return f"new file {label}\n{truncate(numbered, MAX_PREVIEW, note='content')}"

    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        if "content" not in args:
            raise ToolError("write_file requires a 'content' argument.")

        content = args["content"]
        if not isinstance(content, str):
            raise ToolError("'content' must be a string.")

        path = resolve_path(args.get("path", ""), ctx)

        if path.is_dir():
            raise ToolError(f"{display_path(path, ctx)} is a directory.")

        existed = path.exists()
        before = ""
        if existed:
            if looks_binary(path):
                raise ToolError(
                    f"Refusing to overwrite binary file {display_path(path, ctx)}."
                )
            if not ctx.has_read(path):
                raise ToolError(
                    f"{display_path(path, ctx)} already exists and has not been read "
                    "in this session. Call read_file on it first so you do not "
                    "destroy content you have not seen."
                )
            before = path.read_text(encoding="utf-8", errors="replace")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # newline="" keeps the content's own line endings intact.
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)
        except OSError as exc:
            raise ToolError(f"Could not write {display_path(path, ctx)}: {exc}") from exc

        ctx.mark_read(path)

        label = display_path(path, ctx)
        line_count = len(content.splitlines())
        verb = "Updated" if existed else "Created"
        diff = unified_diff(before, content, label) if existed else ""

        return ToolResult(
            content=f"{verb} {label} ({line_count} lines).",
            display={
                "path": label,
                "created": not existed,
                "lines": line_count,
                "diff": diff,
                "content": content,
            },
        )
