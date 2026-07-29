import argparse
import sys
import logging
from backend.runtime.session import InteractiveSession
from backend.cli.tui import TerminalUI

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_interactive_cli():
    parser = argparse.ArgumentParser(description="Jarvis Interactive CLI Agent (Claude Code / Aider Style)")
    parser.add_argument("--repo", type=str, default=".", help="Path to target repository")
    parser.add_argument("--task", type=str, help="Engineering task or issue to resolve")

    args = parser.parse_args()

    task_goal = args.task
    if not task_goal:
        print("\n🤖 Welcome to Jarvis Interactive Agent Session.")
        print("Type your engineering task (e.g. 'Fix login timeout bug'):")
        try:
            task_goal = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession cancelled.")
            return

    if not task_goal:
        print("Empty task provided. Exiting.")
        return

    TerminalUI.render_header(task_goal)

    session = InteractiveSession(workspace_dir=args.repo)

    def on_step(step_info):
        TerminalUI.render_step(step_info)

    result = session.start_task(
        task_goal=task_goal,
        target_file="main.py",
        patch_code="[PATCH] Fix authentication timeout in auth middleware",
        on_step_callback=on_step
    )

    if result["solved"]:
        print("\n========================================================")
        print("📊 JARVIS EXECUTION RESULT & WORKSPACE SUMMARY")
        print("========================================================")
        print(f"Task Goal  : {task_goal}")
        print(f"Status     : {result['status']}")
        print(f"Steps Run  : {result['steps_count']}")
        print("\nExecution History:")
        print(result.get("history_summary", "No history available."))
        print("========================================================\n")

        TerminalUI.render_diff(result["patch"])
        approved = TerminalUI.prompt_approval()
        if approved:
            session.approve_patch()
            print("\n✅ Task completed and patch APPROVED successfully!")
        else:
            print("\n❌ Task patch REJECTED by user. Session ended.")
    else:
        print("\n⚠️ Agent failed to resolve task. Review stacktrace and try again.")


if __name__ == "__main__":
    run_interactive_cli()
