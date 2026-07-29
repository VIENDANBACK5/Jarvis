"""Interactive CLI REPL and one-shot runner for Jarvis Agent."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Optional

from backend.core.agent import AgentLoop
from backend.core.events import AgentEvent
from backend.core.llm.factory import create_llm_backend
from backend.core.permissions import PermissionBroker
from backend.core.session import AgentSession
from backend.core.tools.bash import BashTool
from backend.core.tools.edit import EditTool
from backend.core.tools.glob import GlobTool
from backend.core.tools.grep import GrepTool
from backend.core.tools.read import ReadTool
from backend.core.tools.registry import ToolBox
from backend.core.tools.todo import TodoTool
from backend.core.tools.write import WriteTool


async def run_cli(
    workspace_dir: str = ".",
    print_task: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    workspace_dir = os.path.abspath(workspace_dir)
    print(f"🤖 Jarvis Agent Session initialized at [{workspace_dir}]")

    session = AgentSession(workspace_dir=workspace_dir)
    permissions = PermissionBroker()
    
    # Register CLI permission callback
    async def cli_permission_callback(req):
        print(f"\n⚠️  [PERMISSION REQUIRED] Tool: {req.tool_name}")
        print(f"   Details: {req.details}")
        ans = input("   Approve? [y/n/a (always)]: ").strip().lower()
        if ans == "a":
            permissions.add_rule(req.tool_name, "allow")
            return True
        return ans == "y"

    permissions.set_callback(cli_permission_callback)

    try:
        llm = create_llm_backend(provider=provider, model=model)
    except Exception as exc:
        print(f"❌ Failed to initialize LLM backend: {exc}")
        return

    tools = ToolBox()
    tools.register(ReadTool())
    tools.register(WriteTool())
    tools.register(EditTool())
    tools.register(BashTool())
    tools.register(GlobTool())
    tools.register(GrepTool())
    tools.register(TodoTool())

    loop_engine = AgentLoop(session=session, llm=llm, tools=tools, permissions=permissions)

    if print_task:
        print(f"🎯 Task: {print_task}\n" + "-" * 50)
        async for event in loop_engine.run_turn(print_task):
            _render_cli_event(event)
        return

    print("Type your task or prompt (type 'exit' or 'quit' to end):")
    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "/exit"]:
                print("Goodbye!")
                break
            if user_input.startswith("/"):
                _handle_slash_command(user_input, session)
                continue

            async for event in loop_engine.run_turn(user_input):
                _render_cli_event(event)

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Exiting.")
            break


def _render_cli_event(event: AgentEvent) -> None:
    etype = event.event_type
    payload = event.payload

    if etype == "text_delta":
        sys.stdout.write(payload.get("text", ""))
        sys.stdout.flush()
    elif etype == "tool_use":
        print(f"\n● Tool Call: {payload.get('name')} | Args: {payload.get('args')}")
    elif etype == "tool_result":
        output = payload.get("output", "")
        preview = output[:300] + ("..." if len(output) > 300 else "")
        status = "❌ ERROR" if payload.get("error") else "✅ RESULT"
        print(f"   [{status}]: {preview}")
    elif etype == "turn_complete":
        print("\n✔ Turn Completed.")


def _handle_slash_command(cmd: str, session: AgentSession) -> None:
    if cmd == "/help":
        print("Available slash commands: /help, /clear, /cwd, /exit")
    elif cmd == "/clear":
        session.messages.clear()
        print("Session message history cleared.")
    elif cmd == "/cwd":
        print(f"Current workspace: {session.workspace_dir}")
    else:
        print(f"Unknown slash command: {cmd}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Jarvis Agent CLI")
    parser.add_argument("--cwd", default=".", help="Workspace directory")
    parser.add_argument("--print", dest="print_task", default=None, help="Run a single task and exit")
    parser.add_argument("--provider", default=None, help="LLM Provider")
    parser.add_argument("--model", default=None, help="LLM Model name")
    args = parser.parse_args()

    asyncio.run(run_cli(workspace_dir=args.cwd, print_task=args.print_task, provider=args.provider, model=args.model))


if __name__ == "__main__":
    main()
