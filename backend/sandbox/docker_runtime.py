import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DockerSandbox:
    def __init__(
        self,
        container_name: str,
        image: str = "python:3.11-slim",
        cpu_limit: float = 2.0,
        memory_limit: str = "4g",
        network_mode: str = "bridge",
        workspace_dir: Optional[str] = None
    ):
        self.container_name = container_name
        self.image = image
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
        self.network_mode = network_mode
        self.workspace_dir = workspace_dir
        self.is_running = False

    async def start(self) -> bool:
        """Khởi động container Docker làm sandbox trong trạng thái chạy ngầm."""
        if self.is_running:
            logger.warning(f"Sandbox container '{self.container_name}' đang chạy rồi.")
            return True

        # Lệnh khởi chạy container chạy ngầm (tail -f /dev/null để giữ container hoạt động)
        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            f"--cpus={self.cpu_limit}",
            f"--memory={self.memory_limit}",
            f"--network={self.network_mode}",
            "--restart", "no"
        ]

        # Gắn thư mục làm việc (workspace mount) nếu có
        if self.workspace_dir:
            # Mount workspace của host vào thư mục /workspace trong container
            cmd.extend(["-v", f"{self.workspace_dir}:/workspace"])
            cmd.extend(["-w", "/workspace"])

        cmd.extend([self.image, "tail", "-f", "/dev/null"])

        try:
            logger.info(f"Đang khởi động Docker Sandbox: {' '.join(cmd)}")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                self.is_running = True
                logger.info(f"Sandbox container '{self.container_name}' đã khởi chạy thành công.")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Lỗi khởi chạy Docker Sandbox: {error_msg}")
                # Nếu container đã tồn tại từ trước, thử xóa đi và chạy lại
                if "already in use" in error_msg or "Conflict" in error_msg:
                    logger.info("Đang dọn dẹp container cũ trùng tên...")
                    await self.stop()
                    return await self.start()
                return False
        except Exception as e:
            logger.error(f"Ngoại lệ khi khởi chạy Sandbox container: {str(e)}")
            return False

    async def execute(self, cmd_string: str, timeout: int = 300) -> Dict[str, Any]:
        """Thực thi một câu lệnh bên trong Sandbox container."""
        if not self.is_running:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Sandbox container không hoạt động. Hãy start() trước.",
                "timeout": False
            }

        # Sử dụng docker exec để chạy lệnh
        exec_cmd = ["docker", "exec", self.container_name, "sh", "-c", cmd_string]

        try:
            logger.info(f"Đang thực thi trong Sandbox '{self.container_name}': {cmd_string}")
            proc = await asyncio.create_subprocess_exec(
                *exec_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                # Chạy kèm timeout kiểm soát
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                return {
                    "exit_code": proc.returncode,
                    "stdout": stdout.decode(errors="replace"),
                    "stderr": stderr.decode(errors="replace"),
                    "timeout": False
                }
            except asyncio.TimeoutError:
                # Kill subprocess của docker exec nếu bị timeout
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
                logger.warning(f"Lệnh thực thi bị quá thời gian cho phép ({timeout}s) trong Sandbox.")
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Lệnh bị hủy do vượt quá giới hạn thời gian ({timeout}s).",
                    "timeout": True
                }

        except Exception as e:
            logger.error(f"Ngoại lệ khi thực thi lệnh trong Sandbox: {str(e)}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Ngoại lệ hệ thống: {str(e)}",
                "timeout": False
            }

    async def stop(self) -> bool:
        """Dừng và dọn dẹp container sandbox."""
        logger.info(f"Đang dọn dẹp Sandbox '{self.container_name}'...")
        
        # Stop container
        stop_proc = await asyncio.create_subprocess_exec(
            "docker", "stop", self.container_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await stop_proc.wait()

        # Remove container
        rm_proc = await asyncio.create_subprocess_exec(
            "docker", "rm", self.container_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await rm_proc.wait()

        self.is_running = False
        logger.info(f"Sandbox container '{self.container_name}' đã được dọn dẹp.")
        return True
