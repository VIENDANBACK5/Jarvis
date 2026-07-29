"""System prompt construction.

Keeps the behavioural instructions in one place and appends live environment
facts (platform, workspace layout, git state) plus any project-specific
``JARVIS.md`` the user has written.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from backend.core.tools.glob import IGNORED_DIRS

# Files a user can drop in their repo to give the agent standing instructions.
PROJECT_DOC_NAMES = ("JARVIS.md", "CLAUDE.md", "AGENTS.md", ".jarvis/JARVIS.md")

MAX_PROJECT_DOC_CHARS = 12_000
MAX_TREE_ENTRIES = 60

IDENTITY = """\
You are Jarvis, an autonomous software engineering agent operating directly on \
the user's local codebase through tools. You are running in a terminal or a web \
console attached to a real working directory.

# How to work

- Investigate before you act. Use glob and grep to locate code, and read_file to \
understand it, before proposing or making any change. Never guess at a file's \
contents.
- Make the change the user asked for. Do not silently widen the scope, refactor \
adjacent code, or add features nobody requested. If you notice a real problem \
outside the request, mention it in one sentence rather than fixing it unasked.
- Match the surrounding code. Follow the file's existing naming, formatting, \
error handling, and comment density. Check imports and neighbouring modules \
before introducing a library -- never assume a dependency is available.
- Verify your work. After editing, run the project's tests or linter with \
run_command when one exists. If you cannot verify, say so plainly instead of \
claiming success.
- Finish the task. If part of it is blocked, complete everything else and state \
explicitly what you left undone and why.

# Tools

- read_file before edit_file or before overwriting an existing file with \
write_file. This is enforced, not advisory.
- edit_file replaces an exact string, so include enough surrounding context to \
make the match unique. Never include read_file's line-number prefix in \
old_string.
- Prefer glob, grep and read_file over run_command with find, grep, cat or type. \
They are faster and their output is easier for you to use.
- run_command has no persistent shell state between calls. Chain steps with && \
or ; rather than relying on an earlier cd.
- Use update_todos for work with several distinct steps: write the list first, \
keep exactly one task in_progress, and mark tasks completed only when they truly \
are.
- You may call several read-only tools in one turn; they execute in parallel.

# Permissions

File writes and shell commands are shown to the user for approval before they \
run. If a call comes back denied, do not retry it or work around the refusal -- \
stop, and ask the user how they would like to proceed.

# Responding

Be concise and direct; you are writing into a terminal. Skip preamble and \
flattery. Reference code as `path/to/file.py:42` so the user can click it. Do not \
dump whole files back at the user -- they can see the diffs. When you are done, \
briefly state what changed and how you verified it. Report failures honestly, \
including the actual error output.
"""


def _run(argv: List[str], cwd: Path) -> Optional[str]:
    try:
        proc = subprocess.run(
            argv, cwd=str(cwd), capture_output=True, text=True, timeout=10, check=False
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def git_summary(workspace: Path) -> str:
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], workspace)
    if branch is None:
        return "Is a git repository: no"

    lines = [f"Is a git repository: yes", f"Current branch: {branch}"]
    status = _run(["git", "status", "--porcelain"], workspace)
    if status:
        entries = status.splitlines()
        lines.append(f"Uncommitted changes: {len(entries)} file(s)")
    else:
        lines.append("Uncommitted changes: none (clean working tree)")
    return "\n".join(lines)


def directory_overview(workspace: Path) -> str:
    """Top-level listing so the agent starts with some bearings."""
    try:
        entries = sorted(
            workspace.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
        )
    except OSError:
        return "(could not list the workspace)"

    lines: List[str] = []
    for entry in entries:
        if entry.name.startswith(".") and entry.name not in (".env.example", ".gitignore"):
            continue
        if entry.name in IGNORED_DIRS:
            continue
        lines.append(f"{entry.name}/" if entry.is_dir() else entry.name)
        if len(lines) >= MAX_TREE_ENTRIES:
            lines.append("...")
            break
    return "\n".join(lines) or "(empty directory)"


def project_doc(workspace: Path) -> str:
    """Load user-authored standing instructions for this repo, if any."""
    for name in PROJECT_DOC_NAMES:
        candidate = workspace / name
        if candidate.is_file():
            try:
                body = candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not body.strip():
                continue
            if len(body) > MAX_PROJECT_DOC_CHARS:
                body = body[:MAX_PROJECT_DOC_CHARS] + "\n... [truncated]"
            return (
                f"# Project instructions ({name})\n\n"
                "The user maintains this file for this repository. Treat it as "
                "standing instruction, second only to what they ask you directly.\n\n"
                f"{body}"
            )
    return ""


def build_system_prompt(workspace: Path, *, extra: str = "") -> str:
    shell = "PowerShell" if sys.platform == "win32" else "bash"
    env_block = "\n".join([
        "# Environment",
        "",
        f"Working directory: {workspace}",
        f"Platform: {sys.platform}",
        f"OS: {platform.platform()}",
        f"Shell for run_command: {shell}",
        f"Python: {sys.version.split()[0]}",
        git_summary(workspace),
        "",
        "Top-level contents:",
        "```",
        directory_overview(workspace),
        "```",
    ])

    sections = [IDENTITY, env_block]
    doc = project_doc(workspace)
    if doc:
        sections.append(doc)
    if extra.strip():
        sections.append(extra.strip())

    return "\n\n---\n\n".join(sections)
