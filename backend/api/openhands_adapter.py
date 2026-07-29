import time
import logging
from typing import Dict, Any, List

from backend.runtime.event import RuntimeEvent

logger = logging.getLogger(__name__)


class OpenHandsEventAdapter:
    """Bộ ánh xạ chuyển đổi sự kiện hai chiều giữa OpenHands Event Protocol và Jarvis EventBus."""

    @staticmethod
    def jarvis_event_to_openhands(event: RuntimeEvent) -> Dict[str, Any]:
        """Chuyển đổi RuntimeEvent của Jarvis sang cấu trúc Observation chuẩn OpenHands."""
        event_type = event.event_type
        payload = event.payload
        detail = payload.get("detail", "")

        if event_type == "TASK_CREATED":
            return {
                "observation": "agent_state_changed",
                "content": f"Agent State: RUNNING. {detail}",
                "extras": {"state": "RUNNING"}
            }
        elif event_type == "SEARCH_COMPLETED":
            return {
                "observation": "run",
                "content": f"Search Completed: {detail}",
                "extras": {"command": "search", "output": detail}
            }
        elif event_type == "FILE_READ":
            return {
                "observation": "read",
                "content": f"Read File: {detail}",
                "extras": {"path": payload.get("filepath", "main.py")}
            }
        elif event_type == "PATCH_GENERATED":
            return {
                "observation": "edit",
                "content": f"Generated Patch: {detail}",
                "extras": {"diff": payload.get("patch", "")}
            }
        elif event_type == "TEST_PASSED":
            return {
                "observation": "run",
                "content": f"Pytest Execution Passed: {detail}",
                "extras": {"passed": True}
            }
        elif event_type == "MISSION_COMPLETED":
            return {
                "observation": "agent_state_changed",
                "content": f"Agent State: COMPLETED. {detail}",
                "extras": {"state": "COMPLETED"}
            }
        else:
            return {
                "observation": "null",
                "content": detail,
                "extras": {}
            }

    @staticmethod
    def openhands_action_to_jarvis(action_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Chuyển đổi Action từ OpenHands Frontend sang lệnh yêu cầu Jarvis."""
        action_name = action_dict.get("action", "")
        args = action_dict.get("args", {})

        if action_name == "read":
            return {"tool": "read_file", "kwargs": {"filepath": args.get("path", "main.py")}}
        elif action_name == "edit":
            return {"tool": "edit_file", "kwargs": {"filepath": args.get("path", "main.py"), "patch": args.get("content", "")}}
        elif action_name == "run":
            return {"tool": "pytest", "kwargs": {"test_file": args.get("command", "main.py")}}
        else:
            return {"tool": "search", "kwargs": {"query": action_name}}
