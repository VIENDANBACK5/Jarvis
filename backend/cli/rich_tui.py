import sys
from typing import Dict, Any, List
from backend.runtime.event import RuntimeEvent


class RichTerminalUI:
    def __init__(self):
        self.mission_goal: str = ""
        self.checklist: List[Dict[str, Any]] = [
            {"name": "Scan repository AST", "status": "PENDING"},
            {"name": "Retrieve online memory", "status": "PENDING"},
            {"name": "Synthesize patch", "status": "PENDING"},
            {"name": "Adversarial review", "status": "PENDING"},
            {"name": "Sandbox pytest execution", "status": "PENDING"}
        ]

    def render_banner(self, task_goal: str):
        self.mission_goal = task_goal
        print("\n" + "=" * 60)
        print("  JARVIS ENGINEERING AGENT (Rich Terminal UI - Level 9.5+)")
        print("=" * 60)
        print(f"  Target Goal: {task_goal}")
        print("-" * 60 + "\n")

    def handle_event(self, event: RuntimeEvent):
        """Streaming Event Handler cho Rich Terminal UI."""
        event_type = event.event_type
        detail = event.payload.get("detail", "")

        if event_type == "TASK_CREATED":
            print(f"  [STATUS] 🚀 Mission Started: {detail}")
        elif event_type == "SEARCH_COMPLETED":
            self.checklist[0]["status"] = "DONE"
            print(f"  [STATUS] 🔍 {detail}")
        elif event_type == "FILE_READ":
            self.checklist[1]["status"] = "DONE"
            print(f"  [STATUS] 📖 {detail}")
        elif event_type == "PATCH_GENERATED":
            self.checklist[2]["status"] = "DONE"
            print(f"  [STATUS] ✏️ {detail}")
        elif event_type == "TEST_PASSED":
            self.checklist[3]["status"] = "DONE"
            self.checklist[4]["status"] = "DONE"
            print(f"  [STATUS] ✅ {detail}")
        elif event_type == "MISSION_COMPLETED":
            print(f"  [STATUS] 🎉 Mission Completed: {detail}\n")

    def render_checklist(self):
        print("-" * 60)
        print("  MISSION CHECKLIST STATUS")
        print("-" * 60)
        for idx, item in enumerate(self.checklist, 1):
            mark = "✓" if item["status"] == "DONE" else "○"
            print(f"  {idx}. [{mark}] {item['name']}")
        print("-" * 60 + "\n")
