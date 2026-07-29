import os
import uuid
import logging
from typing import Dict, Any, Optional

from backend.runtime.runtime_loop import AgentRuntimeLoop

logger = logging.getLogger(__name__)


class InteractiveSession:
    def __init__(self, workspace_dir: str = "."):
        self.session_id = f"session-{str(uuid.uuid4())[:8]}"
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.runtime_loop = AgentRuntimeLoop(self.workspace_dir)
        self.state = "IDLE"
        self.current_result: Optional[Dict[str, Any]] = None

    def start_task(
        self,
        task_goal: str,
        target_file: str = "main.py",
        patch_code: str = "[PATCH] Interactive fix",
        on_step_callback = None
    ) -> Dict[str, Any]:
        """Bắt đầu một phiên làm việc tương tác giải quyết tác vụ."""
        self.state = "RUNNING"
        logger.info(f"InteractiveSession [{self.session_id}]: Started task -> {task_goal}")
        
        result = self.runtime_loop.run_loop(
            task_goal=task_goal,
            target_file=target_file,
            patch_code=patch_code,
            on_step_callback=on_step_callback
        )
        self.current_result = result
        self.state = "WAITING_APPROVAL" if result["solved"] else "FAILED"
        return result

    def approve_patch(self) -> bool:
        """Chấp nhận bản vá đề xuất và hoàn tất phiên làm việc."""
        if self.state == "WAITING_APPROVAL":
            self.state = "COMPLETED"
            logger.info(f"InteractiveSession [{self.session_id}]: Patch approved by user.")
            return True
        return False

    def save_session(self, storage_dir: str = ".") -> str:
        """Lưu đĩa cứng trạng thái phiên làm việc (.jarvis/sessions/<session_id>.json)."""
        import json
        save_dir = os.path.join(storage_dir, ".jarvis", "sessions")
        os.makedirs(save_dir, exist_ok=True)
        session_file = os.path.join(save_dir, f"{self.session_id}.json")
        
        data = {
            "session_id": self.session_id,
            "state": self.state,
            "workspace_dir": self.workspace_dir,
            "current_result": self.current_result
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"InteractiveSession: Saved session to {session_file}")
        return session_file

    @classmethod
    def load_session(cls, session_file: str) -> "InteractiveSession":
        """Khôi phục phiên làm việc đã lưu từ đĩa cứng (jarvis resume)."""
        import json
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = cls(workspace_dir=data.get("workspace_dir", "."))
        session.session_id = data.get("session_id", session.session_id)
        session.state = data.get("state", "IDLE")
        session.current_result = data.get("current_result")
        logger.info(f"InteractiveSession: Loaded session {session.session_id} from {session_file}")
        return session
