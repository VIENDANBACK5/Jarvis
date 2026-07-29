import os
import uuid
import logging
from typing import Dict, Optional

from backend.config import get_settings
from backend.sandbox.docker_runtime import DockerSandbox

logger = logging.getLogger(__name__)


class SandboxManager:
    def __init__(self):
        self._sandboxes: Dict[str, DockerSandbox] = {}

    async def get_or_create(
        self,
        sandbox_id: Optional[str] = None,
        image: str = "python:3.11-slim",
        workspace_dir: Optional[str] = None
    ) -> DockerSandbox:
        """Lấy sandbox hiện có hoặc khởi tạo một sandbox container mới."""
        settings = get_settings()

        if not sandbox_id:
            sandbox_id = f"jarvis-sandbox-{uuid.uuid4().hex[:8]}"

        if sandbox_id in self._sandboxes:
            sandbox = self._sandboxes[sandbox_id]
            if not sandbox.is_running:
                logger.info(f"Khởi động lại sandbox container: {sandbox_id}")
                await sandbox.start()
            return sandbox

        # Mặc định mount thư mục gốc của dự án nếu không chỉ định workspace_dir
        if not workspace_dir:
            workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        logger.info(f"Tạo mới Sandbox: {sandbox_id} với image: {image}, workspace: {workspace_dir}")
        sandbox = DockerSandbox(
            container_name=sandbox_id,
            image=image,
            cpu_limit=2.0,
            memory_limit="4g",
            network_mode="bridge",
            workspace_dir=workspace_dir
        )

        success = await sandbox.start()
        if not success:
            raise RuntimeError(f"Không thể khởi chạy Sandbox container '{sandbox_id}'.")

        self._sandboxes[sandbox_id] = sandbox
        return sandbox

    async def destroy(self, sandbox_id: str) -> bool:
        """Dừng và thu hồi container sandbox theo ID."""
        if sandbox_id in self._sandboxes:
            sandbox = self._sandboxes[sandbox_id]
            await sandbox.stop()
            del self._sandboxes[sandbox_id]
            return True
        return False

    async def destroy_all(self):
        """Dừng và giải phóng toàn bộ các sandbox đang chạy ngầm."""
        logger.info("Đang thu hồi tất cả sandbox...")
        sandbox_ids = list(self._sandboxes.keys())
        for sid in sandbox_ids:
            await self.destroy(sid)


# Singleton manager instance
_sandbox_manager = SandboxManager()


def get_sandbox_manager() -> SandboxManager:
    return _sandbox_manager
