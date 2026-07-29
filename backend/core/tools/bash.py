"""Run a shell command in the workspace.

Uses PowerShell on Windows and ``bash``/``sh`` elsewhere, so commands the model
writes match what the user would type in their own terminal. Every invocation
is gated by the permission broker -- this tool is the agent's most powerful
capability and the one most worth a human glance before it runs.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

from backend.core.tools.base import (
    Permission,
    Tool,
    ToolContext,
    ToolError,
    ToolResult,
    display_path,
    resolve_path,
    truncate,
)

MAX_OUTPUT = 30_000
DEFAULT_TIMEOUT = 120
MAX_TIMEOUT = 600

IS_WINDOWS = sys.platform == "win32"


def shell_argv(command: str) -> List[str]:
    """Build the argv that executes ``command`` in the platform's shell."""
    if IS_WINDOWS:
        exe = shutil.which("powershell") or shutil.which("pwsh")
        if exe:
            return [exe, "-NoProfile", "-NonInteractive", "-Command", command]
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", command]
    exe = shutil.which("bash") or "/bin/sh"
    return [exe, "-c", command]


async def _terminate(proc: asyncio.subprocess.Process) -> None:
    """Kill a process and, on Windows, its children."""
    if proc.returncode is not None:
        return
    if IS_WINDOWS:
        # PowerShell spawns grandchildren that survive a plain kill().
        try:
            await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                    check=False,
                ),
            )
        except Exception:
            pass
    try:
        proc.kill()
    except ProcessLookupError:
        pass
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
    except (asyncio.TimeoutError, ProcessLookupError):
        pass


class BashTool(Tool):
    name = "run_command"
    description = (
        "Run a shell command in the workspace and return its stdout, stderr and "
        "exit code. Use this for tests, linters, builds, package managers and git. "
        "Prefer the dedicated read_file / glob / grep tools over cat, find and grep. "
        "Commands run in the shell's default working directory unless you pass cwd. "
        "Shell state does not persist between calls, so chain with && or ; instead "
        "of relying on a previous cd. Never run interactive commands that wait for "
        "input; they will time out."
    )
    permission = Permission.ASK
    read_only = False

    def __init__(self, default_timeout: int = DEFAULT_TIMEOUT) -> None:
        self.default_timeout = default_timeout

    @property
    def input_schema(self) -> Dict[str, Any]:
        shell = "PowerShell" if IS_WINDOWS else "bash"
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": f"The command to run, in {shell} syntax.",
                },
                "description": {
                    "type": "string",
                    "description": "Short active-voice description, e.g. 'Run the unit tests'.",
                },
                "timeout": {
                    "type": "integer",
                    "description": f"Timeout in seconds (default {self.default_timeout}, max {MAX_TIMEOUT}).",
                    "minimum": 1,
                    "maximum": MAX_TIMEOUT,
                },
                "cwd": {
                    "type": "string",
                    "description": "Directory to run in, relative to the workspace. Defaults to the workspace root.",
                },
            },
            "required": ["command"],
        }

    def preview(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        cmd = (args.get("command") or "").strip().replace("\n", " ")
        if len(cmd) > 90:
            cmd = cmd[:87] + "..."
        return f"Run({cmd})"

    def approval_detail(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        lines = [(args.get("command") or "").strip()]
        if args.get("description"):
            lines.append(f"\n# {args['description']}")
        if args.get("cwd"):
            lines.append(f"# in {args['cwd']}")
        return "\n".join(lines)

    async def run(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        command = (args.get("command") or "").strip()
        if not command:
            raise ToolError("run_command requires a non-empty 'command'.")

        workdir = ctx.workspace
        if args.get("cwd"):
            workdir = resolve_path(args["cwd"], ctx, must_exist=True)
            if not workdir.is_dir():
                raise ToolError(f"cwd '{args['cwd']}' is not a directory.")

        timeout = int(args.get("timeout") or self.default_timeout)
        timeout = max(1, min(timeout, MAX_TIMEOUT))

        env = dict(os.environ)
        # Unbuffered + no colour codes keeps captured output readable to the model.
        env.setdefault("PYTHONUNBUFFERED", "1")
        env["NO_COLOR"] = "1"
        env["TERM"] = "dumb"

        try:
            proc = await asyncio.create_subprocess_exec(
                *shell_argv(command),
                cwd=str(workdir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                env=env,
            )
        except (OSError, ValueError) as exc:
            raise ToolError(f"Could not start the command: {exc}") from exc

        timed_out = False
        try:
            raw_out, raw_err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            timed_out = True
            await _terminate(proc)
            raw_out, raw_err = b"", b""
        except asyncio.CancelledError:
            # The user interrupted the turn -- do not leave the child running.
            await _terminate(proc)
            raise

        stdout = raw_out.decode("utf-8", errors="replace")
        stderr = raw_err.decode("utf-8", errors="replace")
        exit_code = -1 if timed_out else (proc.returncode if proc.returncode is not None else -1)

        if timed_out:
            body = (
                f"Command timed out after {timeout}s and was killed.\n"
                "If it was a long-running or interactive process, raise 'timeout' "
                "or run it non-interactively."
            )
            return ToolResult(
                content=body,
                is_error=True,
                display={
                    "command": command,
                    "exit_code": exit_code,
                    "timed_out": True,
                    "cwd": display_path(workdir, ctx),
                    "stdout": "",
                    "stderr": "",
                },
            )

        parts: List[str] = [f"exit code: {exit_code}"]
        if stdout.strip():
            parts.append(f"stdout:\n{truncate(stdout, MAX_OUTPUT, note='stdout')}")
        if stderr.strip():
            parts.append(f"stderr:\n{truncate(stderr, MAX_OUTPUT, note='stderr')}")
        if not stdout.strip() and not stderr.strip():
            parts.append("(no output)")

        return ToolResult(
            content="\n\n".join(parts),
            is_error=exit_code != 0,
            display={
                "command": command,
                "exit_code": exit_code,
                "timed_out": False,
                "cwd": display_path(workdir, ctx),
                "stdout": stdout,
                "stderr": stderr,
            },
        )
