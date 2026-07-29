"""Exact-string replacement editing.

String replacement rather than line numbers or diffs: line numbers drift as
soon as an earlier edit lands, and model-authored unified diffs fail on
whitespace and context mismatches. Requiring a unique literal snippet makes an
edit either unambiguous or a hard error the model can see and fix.
"""

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
from backend.core.tools.write import unified_diff

MAX_PREVIEW = 8000


class EditTool(Tool):
    name = "edit_file"
    description = (
        "Replace an exact string in a file. old_string must appear EXACTLY once "
        "unless replace_all is true -- include enough surrounding context to make "
        "it unique. Reproduce the file's existing text and indentation verbatim "
        "and never include the line-number prefix that read_file adds. You must "
        "read_file the target before editing it."
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
                    "description": "File to edit, absolute or relative to the workspace.",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to find, including indentation.",
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement text. Use an empty string to delete.",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace every occurrence instead of requiring exactly one.",
                    "default": False,
                },
            },
            "required": ["path", "old_string", "new_string"],
        }

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        suffix = ", replace_all" if args.get("replace_all") else ""
        return f"Edit({args.get('path', '?')}{suffix})"

    def approval_detail(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        try:
            path = resolve_path(args.get("path", ""), ctx, must_exist=True)
            before = path.read_text(encoding="utf-8", errors="replace")
            after = self._apply(before, args, path, ctx)
        except ToolError as exc:
            return f"(edit cannot be applied: {exc})"
        diff = unified_diff(before, after, display_path(path, ctx))
        return truncate(diff or "(no textual change)", MAX_PREVIEW, note="diff")

    def _apply(
        self, before: str, args: Dict[str, Any], path, ctx: ToolContext
    ) -> str:
        old = args.get("old_string")
        new = args.get("new_string")

        if old is None or new is None:
            raise ToolError("edit_file requires both 'old_string' and 'new_string'.")
        if not isinstance(old, str) or not isinstance(new, str):
            raise ToolError("'old_string' and 'new_string' must be strings.")
        if old == new:
            raise ToolError("'old_string' and 'new_string' are identical -- nothing to do.")
        if old == "":
            raise ToolError(
                "'old_string' must not be empty. Use write_file to create a new file."
            )

        label = display_path(path, ctx)
        occurrences = before.count(old)

        if occurrences == 0:
            hint = ""
            # A common failure: the model copies read_file's "12\t" prefix back in.
            stripped = "\n".join(
                seg.split("\t", 1)[1] if "\t" in seg and seg.split("\t", 1)[0].isdigit() else seg
                for seg in old.splitlines()
            )
            if stripped != old and stripped and before.count(stripped) > 0:
                hint = (
                    " It looks like you included read_file's line-number prefix "
                    "(e.g. '42\\t'). Send only the raw file text."
                )
            raise ToolError(
                f"old_string was not found in {label}.{hint} "
                "Re-read the file and copy the exact text, including whitespace."
            )

        if occurrences > 1 and not args.get("replace_all"):
            raise ToolError(
                f"old_string appears {occurrences} times in {label}, so the edit is "
                "ambiguous. Add surrounding context to make it unique, or pass "
                "replace_all=true to change every occurrence."
            )

        if args.get("replace_all"):
            return before.replace(old, new)
        return before.replace(old, new, 1)

    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        path = resolve_path(args.get("path", ""), ctx, must_exist=True)
        label = display_path(path, ctx)

        if path.is_dir():
            raise ToolError(f"{label} is a directory, not a file.")
        if looks_binary(path):
            raise ToolError(f"Cannot edit binary file {label}.")
        if not ctx.has_read(path):
            raise ToolError(
                f"You have not read {label} in this session. Call read_file on it "
                "before editing so your old_string matches the real content."
            )
        if ctx.stale(path):
            raise ToolError(
                f"{label} has changed on disk since you read it. Read it again "
                "before editing to avoid clobbering those changes."
            )

        before = path.read_text(encoding="utf-8", errors="replace")
        after = self._apply(before, args, path, ctx)

        try:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(after)
        except OSError as exc:
            raise ToolError(f"Could not write {label}: {exc}") from exc

        ctx.mark_read(path)

        replaced = (
            before.count(args["old_string"]) if args.get("replace_all") else 1
        )
        diff = unified_diff(before, after, label)
        added = sum(1 for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
        removed = sum(1 for ln in diff.splitlines() if ln.startswith("-") and not ln.startswith("---"))

        return ToolResult(
            content=(
                f"Edited {label}: {replaced} replacement(s), "
                f"+{added}/-{removed} lines."
            ),
            display={
                "path": label,
                "replacements": replaced,
                "added": added,
                "removed": removed,
                "diff": diff,
            },
        )
