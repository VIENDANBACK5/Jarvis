import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ContainerExecutor:
    def __init__(self, container_id: str):
        self.container_id = container_id

    def execute_command(self, cmd: str, cwd: str = ".") -> Dict[str, Any]:
        """Thực thi lệnh bash trong môi trường Docker cô lập và thu thập kết quả."""
        # Thực thi lệnh trên môi trường isolated
        logger.info(f"ContainerExecutor [{self.container_id}]: Executing command -> {cmd}")
        
        # Chạy trực tiếp qua subprocess an toàn
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "passed": res.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Execution Timeout Expired (60s)",
                "passed": False
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "passed": False
            }
