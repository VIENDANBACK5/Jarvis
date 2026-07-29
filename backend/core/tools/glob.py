"""Find files by glob pattern."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Set

from backend.core.tools.base import (
    Permission,
    Tool,
    ToolContext,
    ToolError,
    ToolResult,
    resolve_path,
)

# Directories that are never worth walking for a coding agent.
IGNORED_DIRS: Set[str] = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "dist", "build", ".next", ".nuxt", "target", ".idea", ".vscode",
    ".gradle", "coverage", ".cache", "site-packages", ".jarvis", ".eggs",
}

MAX_RESULTS = 300


def walk_files(root: Path, *, follow_symlinks: bool = False) -> Iterator[Path]:
    """Yield every non-ignored file under ``root``."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dirnames[:] = [
            d for d in dirnames if d not in IGNORED_DIRS and not d.endswith(".egg-info")
        ]
        for name in filenames:
            yield Path(dirpath) / name


class GlobTool(Tool):
    name = "glob"
    description = (
        "Find files whose path matches a glob pattern, newest first. Supports "
        "'*' within a path segment and '**' across segments, e.g. '**/*.py', "
        "'src/**/test_*.py'. Build and dependency directories such as .git, "
        "node_modules and __pycache__ are skipped. Use this to discover files "
        "when you do not know exact paths."
    )
    permission = Permission.ALLOW
    read_only = True

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern, e.g. '**/*.py' or 'backend/**/*.json'.",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in. Defaults to the workspace root.",
                },
            },
            "required": ["pattern"],
        }

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        where = args.get("path")
        return f"Glob({args.get('pattern', '?')}{f' in {where}' if where else ''})"

    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        pattern = (args.get("pattern") or "").strip()
        if not pattern:
            raise ToolError("glob requires a non-empty 'pattern'.")

        root = ctx.workspace
        if args.get("path"):
            root = resolve_path(args["path"], ctx, must_exist=True)
            if not root.is_dir():
                raise ToolError(f"'{args['path']}' is not a directory.")

        normalised = pattern.replace(os.sep, "/").lstrip("./")

        matches: List[Path] = []
        for candidate in walk_files(root):
            rel = str(candidate.relative_to(root)).replace(os.sep, "/")
            # fnmatch treats '*' as crossing '/', so '**/x' and '*.py' both work
            # against the full relative path; also match on the bare filename so
            # a pattern like '*.py' finds nested files the way users expect.
            if fnmatch.fnmatch(rel, normalised) or fnmatch.fnmatch(candidate.name, normalised):
                matches.append(candidate)

        if not matches:
            return ToolResult(
                content=(
                    f"No files matched '{pattern}'. Try a broader pattern such as "
                    f"'**/{os.path.basename(normalised) or '*'}'."
                ),
                display={"pattern": pattern, "count": 0, "files": []},
            )

        def mtime(p: Path) -> float:
            try:
                return p.stat().st_mtime
            except OSError:
                return 0.0

        matches.sort(key=mtime, reverse=True)
        truncated = len(matches) > MAX_RESULTS
        shown = matches[:MAX_RESULTS]

        rels = [
            str(p.relative_to(ctx.workspace)).replace(os.sep, "/")
            if ctx.workspace in p.parents or p.parent == ctx.workspace
            else str(p)
            for p in shown
        ]

        body = "\n".join(rels)
        if truncated:
            body += f"\n\n[{len(matches) - MAX_RESULTS} more matches not shown]"

        return ToolResult(
            content=f"{len(matches)} file(s) matched '{pattern}':\n{body}",
            display={"pattern": pattern, "count": len(matches), "files": rels},
        )
