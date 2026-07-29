"""Search file contents by regex.

Shells out to ripgrep when it is on PATH (much faster on large trees) and falls
back to a pure-Python walk otherwise, so the tool behaves the same on a machine
without rg installed.
"""

from __future__ import annotations

import asyncio
import fnmatch
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.tools.base import (
    Permission,
    Tool,
    ToolContext,
    ToolError,
    ToolResult,
    looks_binary,
    resolve_path,
    truncate,
)
from backend.core.tools.glob import IGNORED_DIRS, walk_files

MAX_MATCHES = 200
MAX_OUTPUT = 30_000


class GrepTool(Tool):
    name = "grep"
    description = (
        "Search file contents with a regular expression and return matching "
        "lines with their file and line number. Filter the file set with the "
        "'glob' argument, e.g. '*.py'. Use output_mode='files_with_matches' when "
        "you only need which files match. Prefer this over run_command with grep."
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
                    "description": "Regular expression to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search. Defaults to the workspace root.",
                },
                "glob": {
                    "type": "string",
                    "description": "Only search files matching this glob, e.g. '*.py'.",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Ignore case when matching.",
                    "default": False,
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                    "description": "'content' returns matching lines (default), "
                                   "'files_with_matches' returns paths only, "
                                   "'count' returns per-file match counts.",
                    "default": "content",
                },
                "context": {
                    "type": "integer",
                    "description": "Lines of context to show before and after each match.",
                    "minimum": 0,
                    "maximum": 20,
                },
            },
            "required": ["pattern"],
        }

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        extra = f", glob={args['glob']}" if args.get("glob") else ""
        return f"Grep({args.get('pattern', '?')}{extra})"

    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        pattern = args.get("pattern") or ""
        if not pattern:
            raise ToolError("grep requires a non-empty 'pattern'.")

        try:
            flags = re.IGNORECASE if args.get("case_insensitive") else 0
            regex = re.compile(pattern, flags)
        except re.error as exc:
            raise ToolError(f"Invalid regular expression '{pattern}': {exc}") from exc

        root = ctx.workspace
        if args.get("path"):
            root = resolve_path(args["path"], ctx, must_exist=True)

        mode = args.get("output_mode") or "content"
        if mode not in ("content", "files_with_matches", "count"):
            raise ToolError(
                f"Unknown output_mode '{mode}'. Use content, files_with_matches or count."
            )

        rg = shutil.which("rg")
        if rg and root.is_dir():
            result = await self._ripgrep(rg, pattern, root, args, mode, ctx)
            if result is not None:
                return result

        return self._python_search(regex, root, args, mode, ctx)

    # ---------------------------------------------------------------- ripgrep #

    async def _ripgrep(
        self,
        rg: str,
        pattern: str,
        root: Path,
        args: Dict[str, Any],
        mode: str,
        ctx: ToolContext,
    ) -> Optional[ToolResult]:
        argv: List[str] = [rg, "--no-heading", "--line-number", "--color", "never"]
        if args.get("case_insensitive"):
            argv.append("-i")
        if mode == "files_with_matches":
            argv.append("--files-with-matches")
        elif mode == "count":
            argv.append("--count")
        elif args.get("context"):
            argv += ["-C", str(int(args["context"]))]
        if args.get("glob"):
            argv += ["--glob", args["glob"]]
        for ignored in sorted(IGNORED_DIRS):
            argv += ["--glob", f"!{ignored}/**"]
        argv += ["--max-count", str(MAX_MATCHES), "-e", pattern, str(root)]

        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )
            raw_out, raw_err = await asyncio.wait_for(proc.communicate(), timeout=60)
        except (OSError, asyncio.TimeoutError):
            return None  # fall back to the Python implementation

        # rg exits 1 for "no matches" and 2 for real errors.
        if proc.returncode not in (0, 1):
            return None

        out = raw_out.decode("utf-8", errors="replace")
        lines = [
            self._relativise(ln, root, ctx) for ln in out.splitlines() if ln.strip()
        ]

        if not lines:
            return ToolResult(
                content=f"No matches for '{pattern}'.",
                display={"pattern": pattern, "count": 0, "matches": []},
            )

        header = f"{len(lines)} " + (
            "file(s) with matches" if mode == "files_with_matches" else "match(es)"
        )
        return ToolResult(
            content=f"{header} for '{pattern}':\n"
                    + truncate("\n".join(lines), MAX_OUTPUT, note="matches"),
            display={"pattern": pattern, "count": len(lines), "matches": lines},
        )

    @staticmethod
    def _relativise(line: str, root: Path, ctx: ToolContext) -> str:
        """Rewrite absolute paths in rg output as workspace-relative."""
        prefix = str(ctx.workspace) + os.sep
        if line.startswith(prefix):
            return line[len(prefix):].replace(os.sep, "/")
        return line

    # ----------------------------------------------------------- pure Python #

    def _python_search(
        self,
        regex: re.Pattern,
        root: Path,
        args: Dict[str, Any],
        mode: str,
        ctx: ToolContext,
    ) -> ToolResult:
        file_glob = args.get("glob")
        context_n = int(args.get("context") or 0)

        candidates = [root] if root.is_file() else list(walk_files(root))

        hits: List[str] = []
        per_file: Dict[str, int] = {}
        total = 0

        for path in candidates:
            if file_glob and not (
                fnmatch.fnmatch(path.name, file_glob)
                or fnmatch.fnmatch(str(path).replace(os.sep, "/"), file_glob)
            ):
                continue
            if looks_binary(path):
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            lines = content.splitlines()
            matched_here = [i for i, ln in enumerate(lines) if regex.search(ln)]
            if not matched_here:
                continue

            try:
                label = str(path.relative_to(ctx.workspace)).replace(os.sep, "/")
            except ValueError:
                label = str(path)

            per_file[label] = len(matched_here)
            total += len(matched_here)

            if mode == "files_with_matches":
                hits.append(label)
            elif mode == "count":
                hits.append(f"{label}:{len(matched_here)}")
            else:
                shown: set = set()
                for idx in matched_here:
                    lo = max(0, idx - context_n)
                    hi = min(len(lines), idx + context_n + 1)
                    for j in range(lo, hi):
                        if j in shown:
                            continue
                        shown.add(j)
                        sep = ":" if j == idx else "-"
                        hits.append(f"{label}{sep}{j + 1}{sep}{lines[j]}")
                    if len(hits) >= MAX_MATCHES:
                        break

            if len(hits) >= MAX_MATCHES:
                hits.append(f"[stopped after {MAX_MATCHES} results]")
                break

        if not hits:
            return ToolResult(
                content=f"No matches for '{regex.pattern}'.",
                display={"pattern": regex.pattern, "count": 0, "matches": []},
            )

        noun = "file(s) with matches" if mode == "files_with_matches" else "match(es)"
        count = len(per_file) if mode == "files_with_matches" else total
        return ToolResult(
            content=f"{count} {noun} for '{regex.pattern}':\n"
                    + truncate("\n".join(hits), MAX_OUTPUT, note="matches"),
            display={"pattern": regex.pattern, "count": count, "matches": hits},
        )
