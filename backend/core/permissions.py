"""The permission gate.

Read-only tools run freely. Anything that writes to disk or executes a command
stops here and waits for a human answer, which arrives either from the CLI's
stdin prompt or from an HTTP POST out of the web UI. Both paths resolve the
same :class:`asyncio.Future`, so the agent loop does not care which front-end
is attached.
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import logging
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.tools.base import Permission, Tool

logger = logging.getLogger(__name__)

SETTINGS_FILE = Path(".jarvis") / "settings.json"


class Decision(str, Enum):
    ALLOW_ONCE = "allow_once"
    ALLOW_ALWAYS = "allow_always"
    DENY = "deny"


class PermissionRequest:
    def __init__(self, tool: Tool, args: Dict[str, Any], preview: str, detail: str):
        self.id = f"perm-{uuid.uuid4().hex[:12]}"
        self.tool = tool
        self.args = args
        self.preview = preview
        self.detail = detail
        # Constructed from inside the running loop, so get_running_loop is safe
        # and avoids the deprecated implicit-loop behaviour of get_event_loop.
        self.future: asyncio.Future[Decision] = asyncio.get_running_loop().create_future()

    def resolve(self, decision: Decision) -> bool:
        if self.future.done():
            return False
        self.future.set_result(decision)
        return True


class PermissionBroker:
    """Decides whether a tool call may proceed.

    ``auto_approve`` bypasses prompting entirely -- useful for headless runs and
    tests, but it lets the agent modify files and run commands unattended.
    """

    def __init__(
        self,
        workspace: Path,
        *,
        auto_approve: bool = False,
        persist: bool = True,
    ) -> None:
        self.workspace = Path(workspace)
        self.auto_approve = auto_approve
        self.persist = persist
        self.rules: List[str] = []
        self.pending: Dict[str, PermissionRequest] = {}
        # Set by whichever front-end is attached; receives a PermissionRequest
        # and is responsible for eventually calling resolve().
        self.on_request = None
        self._load_rules()

    # ------------------------------------------------------------- rules I/O #

    @property
    def settings_path(self) -> Path:
        return self.workspace / SETTINGS_FILE

    def _load_rules(self) -> None:
        path = self.settings_path
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            loaded = data.get("allow", [])
            if isinstance(loaded, list):
                self.rules = [str(r) for r in loaded]
                logger.info("Loaded %d permission rule(s) from %s", len(self.rules), path)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable %s: %s", path, exc)

    def _save_rules(self) -> None:
        if not self.persist:
            return
        path = self.settings_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            existing: Dict[str, Any] = {}
            if path.exists():
                try:
                    existing = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    existing = {}
            existing["allow"] = sorted(set(self.rules))
            path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not persist permission rules to %s: %s", path, exc)

    # --------------------------------------------------------------- matching #

    @staticmethod
    def rule_for(tool: Tool, args: Dict[str, Any]) -> str:
        """The rule string an 'always allow' answer should persist.

        Commands are keyed on their first token so approving ``pytest -q`` also
        covers ``pytest tests/`` -- approving a whole binary, not one string.
        File tools are keyed on the tool name alone.
        """
        if tool.name == "run_command":
            command = str(args.get("command", "")).strip()
            head = command.split()[0] if command.split() else command
            return f"run_command({head}*)"
        return f"{tool.name}(*)"

    def matches(self, tool: Tool, args: Dict[str, Any]) -> bool:
        target = self.rule_for(tool, args)
        for rule in self.rules:
            if rule == target or fnmatch.fnmatch(target, rule):
                return True
            # A bare tool name allows every call to that tool.
            if rule == tool.name or rule == f"{tool.name}(*)":
                return True
        return False

    def add_rule(self, tool: Tool, args: Dict[str, Any]) -> str:
        rule = self.rule_for(tool, args)
        if rule not in self.rules:
            self.rules.append(rule)
            self._save_rules()
        return rule

    # ------------------------------------------------------------ the gateway #

    def needs_approval(self, tool: Tool, args: Dict[str, Any]) -> bool:
        if tool.permission == Permission.ALLOW:
            return False
        if self.auto_approve:
            return False
        return not self.matches(tool, args)

    async def request(
        self, tool: Tool, args: Dict[str, Any], preview: str, detail: str
    ) -> Decision:
        """Ask the attached front-end and wait for an answer.

        With no front-end attached we deny rather than assume consent -- a
        misconfigured server must not silently gain write access.
        """
        req = PermissionRequest(tool, args, preview, detail)
        self.pending[req.id] = req

        if self.on_request is None:
            self.pending.pop(req.id, None)
            logger.error("No permission handler attached; denying %s", tool.name)
            return Decision.DENY

        try:
            result = self.on_request(req)
            if asyncio.iscoroutine(result):
                await result
            decision = await req.future
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Permission handler failed")
            decision = Decision.DENY
            logger.error("Denying %s because the handler errored: %s", tool.name, exc)
        finally:
            self.pending.pop(req.id, None)

        if decision == Decision.ALLOW_ALWAYS:
            self.add_rule(tool, args)

        return decision

    # ------------------------------------------------- two-phase (generator) #
    #
    # The agent loop is an async generator, so it cannot answer a callback --
    # it needs to *yield* the prompt to its consumer and then await the reply.
    # These two methods split request() at that seam.

    def open_request(
        self, tool: Tool, args: Dict[str, Any], preview: str, detail: str
    ) -> PermissionRequest:
        """Register a pending prompt. Must be called from inside the event loop."""
        req = PermissionRequest(tool, args, preview, detail)
        self.pending[req.id] = req
        return req

    async def await_decision(self, req: PermissionRequest) -> Decision:
        """Block until some front-end calls :meth:`resolve` for this request."""
        try:
            decision = await req.future
        except asyncio.CancelledError:
            req.resolve(Decision.DENY)
            raise
        finally:
            self.pending.pop(req.id, None)

        if decision == Decision.ALLOW_ALWAYS:
            self.add_rule(req.tool, req.args)
        return decision

    def resolve(self, request_id: str, decision: Decision) -> bool:
        """Called by the HTTP layer when the UI answers a prompt."""
        req = self.pending.get(request_id)
        if req is None:
            return False
        return req.resolve(decision)

    def cancel_all(self) -> None:
        """Deny everything outstanding, e.g. when a turn is interrupted."""
        for req in list(self.pending.values()):
            req.resolve(Decision.DENY)
        self.pending.clear()
