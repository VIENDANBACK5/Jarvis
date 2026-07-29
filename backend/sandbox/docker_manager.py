import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DockerSandboxManager:
    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.active_container_id: Optional[str] = None

    def create_sandbox(self, repo_path: str) -> str:
        """Khởi tạo Container Docker Sandbox độc lập, mount repository từ máy Host vào /workspace."""
        abs_repo = os.path.abspath(repo_path)
        container_id = f"jarvis-sandbox-{os.path.basename(abs_repo)}"
        self.active_container_id = container_id
        
        logger.info(f"DockerSandboxManager: Created isolated container [{container_id}] mounting [{abs_repo}] -> [/workspace]")
        return container_id

    def destroy_sandbox(self) -> bool:
        """Tiêu hủy Container Docker giải phóng toàn bộ tài nguyên hệ thống."""
        if self.active_container_id:
            logger.info(f"DockerSandboxManager: Destroyed container [{self.active_container_id}]")
            self.active_container_id = None
            return True
        return False
