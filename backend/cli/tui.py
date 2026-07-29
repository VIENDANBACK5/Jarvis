import sys
from typing import Dict, Any
from backend.runtime.event import RuntimeEvent


class TerminalUI:
    def __init__(self):
        self.plan_checklist = [
            {"id": 1, "name": "Scan repository", "status": "PENDING"},
            {"id": 2, "name": "Identify target files", "status": "PENDING"},
            {"id": 3, "name": "Synthesize patch", "status": "PENDING"},
            {"id": 4, "name": "Adversarial review", "status": "PENDING"},
            {"id": 5, "name": "Sandbox pytest", "status": "PENDING"}
        ]

    def handle_event(self, event: RuntimeEvent):
        """Subscriber callback lắng nghe và render sự kiện theo thời gian thực (Streaming Event Renderer)."""
        detail = event.payload.get("detail", "")
        event_type = event.event_type

        if event_type == "TASK_CREATED":
            print(f"  [STREAM] 🚀 Task Created: {detail}")
        elif event_type == "SEARCH_COMPLETED":
            self.plan_checklist[0]["status"] = "DONE"
            print(f"  [STREAM] 🔍 {detail}")
        elif event_type == "FILE_READ":
            self.plan_checklist[1]["status"] = "DONE"
            print(f"  [STREAM] 📖 {detail}")
        elif event_type == "PATCH_GENERATED":
            self.plan_checklist[2]["status"] = "DONE"
            print(f"  [STREAM] ✏️ {detail}")
        elif event_type == "TEST_PASSED":
            self.plan_checklist[3]["status"] = "DONE"
            self.plan_checklist[4]["status"] = "DONE"
            print(f"  [STREAM] ✅ {detail}")
        elif event_type == "MISSION_COMPLETED":
            print(f"  [STREAM] 🎉 {detail}\n")

    def render_checklist(self):
        print("\n--------------------------------------------------------")
        print("📋 MISSION PLAN CHECKLIST")
        print("--------------------------------------------------------")
        for item in self.plan_checklist:
            icon = "✓" if item["status"] == "DONE" else "○"
            print(f"  {item['id']} {icon} {item['name']}")
        print("--------------------------------------------------------\n")

    @staticmethod
    def render_header(task_goal: str):
        print("\n========================================================")
        print("[JARVIS] STREAMING TERMINAL UI (Claude Code Style)")
        print("========================================================")
        print(f"🎯 TASK : {task_goal}")
        print("--------------------------------------------------------\n")

    @staticmethod
    def render_step(step_info: Dict[str, Any]):
        action = step_info.get("action", "")
        detail = step_info.get("detail", "")
        print(f"  ✓ [{action}] {detail}")

    @staticmethod
    def render_diff(patch_code: str):
        print("\n--------------------------------------------------------")
        print("📝 PROPOSED CODE DIFF PREVIEW")
        print("--------------------------------------------------------")
        for line in patch_code.splitlines():
            if line.startswith("+"):
                print(f"\033[32m{line}\033[0m")
            elif line.startswith("-"):
                print(f"\033[31m{line}\033[0m")
            else:
                print(line)
        print("--------------------------------------------------------")

    @staticmethod
    def prompt_approval() -> bool:
        print("\nDo you approve and apply this patch? [Y/n]: ", end="")
        try:
            choice = input().strip().lower()
            return choice in ["", "y", "yes"]
        except (KeyboardInterrupt, EOFError):
            return False
