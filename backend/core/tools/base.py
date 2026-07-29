"""Foundation types for Jarvis agent tools.

Every tool the agent can call implements :class:`Tool`. The agent loop never
touches the filesystem or the shell directly -- it only dispatches through the
:class:`~backend.core.tools.registry.ToolBox`, which means path confinement and
the permission gate are enforced in exactly one place.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class ToolError(Exception):
    """Raised when a tool cannot run. The message is fed back to the model.

    These are *expected* failures (bad path, file not found, ambiguous edit) --
    the model is meant to read the message and correct itself, so keep the text
    specific and actionable.
    """


class Permission(str, Enum):
    """Whether invoking a tool needs the user's blessing."""

    ALLOW = "allow"  # read-only, runs without prompting
    ASK = "ask"      # mutates the workspace or runs commands


@dataclass
class ToolContext:
    """Per-session state shared by every tool invocation."""

    workspace: Path
    cwd: Path
    # Absolute path -> mtime observed at read time. Backs the "must read before
    # you edit" rule and lets us detect files that changed under the agent.
    read_files: Dict[str, float] = field(default_factory=dict)

    def mark_read(self, path: Path) -> None:
        try:
            self.read_files[str(path.resolve())] = path.stat().st_mtime
        except OSError:
            pass

    def has_read(self, path: Path) -> bool:
        return str(path.resolve()) in self.read_files

    def stale(self, path: Path) -> bool:
        """True if the file changed on disk since the agent last read it."""
        key = str(path.resolve())
        seen = self.read_files.get(key)
        if seen is None:
            return False
        try:
            return path.stat().st_mtime > seen
        except OSError:
            return False


@dataclass
class ToolResult:
    """Outcome of a tool call.

    ``content`` is what enters the model's context and is truncated for that
    purpose. ``display`` carries the untruncated / structured payload used to
    render rich cards in the web UI, and never enters the context.
    """

    content: str
    is_error: bool = False
    display: Optional[Dict[str, Any]] = None


class Tool(ABC):
    name: str = ""
    description: str = ""
    permission: Permission = Permission.ASK
    # Read-only tools are dispatched concurrently within a single model turn.
    read_only: bool = False

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema for the tool's arguments, sent to the model."""

    @abstractmethod
    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        ...

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        """One-line summary shown in transcripts, e.g. ``Read(src/app.py)``."""
        return f"{self.name}({args})"

    def approval_detail(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        """Body of the permission prompt -- a diff, a command, whatever the
        user needs in order to answer yes or no. Empty means preview() suffices.
        """
        return ""


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def resolve_path(raw: str, ctx: ToolContext, *, must_exist: bool = False) -> Path:
    """Resolve a user/model-supplied path and confine it to the workspace.

    Relative paths resolve against the session cwd. Anything that lands outside
    the workspace root -- via ``..``, an absolute path, or a symlink -- is
    rejected. This is the single chokepoint for path safety.
    """
    if not raw or not str(raw).strip():
        raise ToolError("Path must not be empty.")

    candidate = Path(str(raw).strip()).expanduser()
    if not candidate.is_absolute():
        candidate = ctx.cwd / candidate

    # strict=False so we can resolve paths for files we are about to create.
    resolved = candidate.resolve(strict=False)
    root = ctx.workspace.resolve(strict=False)

    if resolved != root and root not in resolved.parents:
        raise ToolError(
            f"Path '{raw}' resolves outside the workspace root ({root}). "
            "The agent may only touch files inside the workspace."
        )

    # Never let the agent corrupt git's object store.
    parts = resolved.relative_to(root).parts if resolved != root else ()
    if ".git" in parts:
        raise ToolError("Refusing to operate inside the .git directory.")

    if must_exist and not resolved.exists():
        raise ToolError(f"File not found: {display_path(resolved, ctx)}")

    return resolved


def display_path(path: Path, ctx: ToolContext) -> str:
    """Workspace-relative path for display, falling back to absolute."""
    try:
        return str(path.resolve().relative_to(ctx.workspace.resolve())).replace(os.sep, "/")
    except (ValueError, OSError):
        return str(path)


def truncate(text: str, limit: int, *, note: str = "output") -> str:
    """Clamp tool output so a single call cannot blow up the context window."""
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    head = int(limit * 0.7)
    tail = limit - head
    return (
        f"{text[:head]}\n\n"
        f"... [{omitted} characters of {note} truncated] ...\n\n"
        f"{text[-tail:]}"
    )


BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".tiff",
    ".pdf", ".zip", ".gz", ".tar", ".bz2", ".xz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".class",
    ".pyc", ".pyo", ".wasm", ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".woff", ".woff2", ".ttf", ".eot", ".otf", ".db", ".sqlite", ".sqlite3",
}


def looks_binary(path: Path) -> bool:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return True
    try:
        with open(path, "rb") as fh:
            return b"\0" in fh.read(8192)
    except OSError:
        return False
