import os
import json
import logging
from typing import Dict, Any, List, Optional

from backend.sandbox import get_sandbox_manager
from backend.tools.git import GitCheckpointManager
from backend.execution.engine import ExecutionEngine
from backend.editing.diff_analyzer import DiffAnalyzer

logger = logging.getLogger(__name__)


class SWEBenchEvaluator:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.execution_engine = ExecutionEngine(self.workspace_dir)

    async def evaluate_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Đánh giá Agent Jarvis trên một task instance của SWE-bench.
        
        Mỗi instance chứa:
        - instance_id: ID duy nhất của issue
        - repo: tên repository
        - base_commit: commit hash gốc trước khi sửa lỗi
        - problem_statement: mô tả lỗi / issue github
        - test_patch: patch của bài test kiểm tra lỗi đã sửa hay chưa
        """
        instance_id = instance.get("instance_id", "unknown")
        repo = instance.get("repo", "unknown")
        base_commit = instance.get("base_commit", "")
        problem_statement = instance.get("problem_statement", "")
        test_patch = instance.get("test_patch", "")

        logger.info(f"Khởi động đánh giá SWE-bench cho instance: {instance_id} ({repo})")

        # 1. Khởi tạo Git manager trên workspace đánh giá
        git_manager = GitCheckpointManager(self.workspace_dir)
        if not await git_manager.is_git_repo():
            raise RuntimeError(f"Workspace {self.workspace_dir} không phải Git repository để checkout commit.")

        # 2. Checkout mã nguồn về base_commit (giả lập môi trường lỗi chưa sửa)
        logger.info(f"Checkout repo về base commit: {base_commit}")
        checkout_code, _, checkout_err = await git_manager._run_git(["checkout", "-f", base_commit])
        if checkout_code != 0:
            return {
                "instance_id": instance_id,
                "status": "failed_setup",
                "error": f"Không thể checkout commit {base_commit}: {checkout_err}"
            }

        # Tạo checkpoint để lưu trạng thái sạch ban đầu
        checkpoint_hash = await git_manager.create_checkpoint(f"SWE-bench Base: {instance_id}")

        # 3. Chạy luồng sửa lỗi của Jarvis (ExecutionEngine + Self-healing)
        logger.info("Kích hoạt Agent Jarvis giải quyết issue...")
        
        # Giả lập lệnh chạy test chính để xác thực (thông thường là chạy pytest)
        test_command = "pytest"
        
        # Chạy động cơ thực thi
        result = await self.execution_engine.run_and_heal_code_task(
            task_desc=problem_statement,
            test_command=test_command
        )

        # 4. Trích xuất bản vá do Agent tạo ra và so sánh
        final_diff = ""
        if result["status"] == "success":
            final_diff = await git_manager.get_diff(checkpoint_hash)
            logger.info("Agent đã sinh bản vá thành công!")
        else:
            logger.error("Agent thất bại trong việc sửa lỗi.")

        # 5. Phục hồi lại nhánh gốc (sau khi đã trích xuất diff) để dọn dẹp workspace
        await git_manager._run_git(["checkout", "main"])

        return {
            "instance_id": instance_id,
            "status": "completed" if result["status"] == "success" else "failed_execution",
            "agent_success": result["status"] == "success",
            "retries": result["retries"],
            "patch_diff": final_diff,
            "error": result["error"]
        }

    async def run_suite(self, instances_file: str) -> List[Dict[str, Any]]:
        """Chạy đánh giá trên toàn bộ bộ dữ liệu JSON chứa nhiều issues."""
        if not os.path.exists(instances_file):
            logger.error(f"Không tìm thấy file dữ liệu: {instances_file}")
            return []

        with open(instances_file, "r", encoding="utf-8") as f:
            instances = json.load(f)

        results = []
        for inst in instances:
            res = await self.evaluate_instance(inst)
            results.append(res)

        return results
