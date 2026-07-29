import os
import logging
from typing import Dict, Any

from backend.learning.memory_replay import EngineeringMemoryReplay
from backend.evaluation.repo_manager import RepoManager
from backend.evaluation.evaluator import MultiObjectiveEvaluator
from backend.reasoning.causal.evolution import CausalEvolution

logger = logging.getLogger(__name__)


class SWERunner:
    def __init__(self, workspace_dir: str, experience_dir: str, graph_file_path: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.experience_dir = os.path.abspath(experience_dir)
        self.graph_file_path = os.path.abspath(graph_file_path)

        self.replay = EngineeringMemoryReplay(self.experience_dir)
        self.repo_manager = RepoManager(self.workspace_dir)
        self.evaluator = MultiObjectiveEvaluator()

    def run_task(
        self,
        issue_text: str,
        patch_content: str,
        token_count: int,
        duration_sec: float,
        success_rate: float
    ) -> Dict[str, Any]:
        """Điều phối chạy thử nghiệm chẩn đoán, áp dụng vá lỗi và tự động học hỏi khép kín."""
        logger.info(f"SWERunner: Bắt đầu xử lý task cho issue: '{issue_text}'")

        # 1. Gọi hồi tưởng hành trình kỹ thuật cũ
        journey = self.replay.retrieve_journey(issue_text)

        # 2. Sao lưu repo trước khi áp dụng thay đổi
        self.repo_manager.backup_checkpoint()

        try:
            # 3. Tính toán điểm phần thưởng Reward đa mục tiêu
            reward = self.evaluator.calculate_reward(
                success_rate=success_rate,
                patch_content=patch_content,
                token_count=token_count,
                duration_sec=duration_sec
            )

            # Khởi tạo trạng thái trả về
            success = reward >= 0.70

            # 4. Tiến hóa tri thức nhân quả dài hạn nếu sửa lỗi tốt
            if success:
                logger.info("SWERunner: Sửa lỗi thành công! Tiến hành tiến hóa đồ thị nhân quả.")
                CausalEvolution.update_causal_weights(
                    graph_file_path=self.graph_file_path,
                    symptom="500 API error" if "async" in issue_text.lower() else "database error",
                    cause="async iterator handling timeout" if "async" in issue_text.lower() else "Database Schema Mismatch",
                    success=True,
                    context={"framework": "FastAPI", "database": "PostgreSQL"}
                )
            else:
                logger.info("SWERunner: Điểm reward chưa tối ưu. Cập nhật hạ niềm tin nhân quả.")
                CausalEvolution.update_causal_weights(
                    graph_file_path=self.graph_file_path,
                    symptom="500 API error" if "async" in issue_text.lower() else "database error",
                    cause="async iterator handling timeout" if "async" in issue_text.lower() else "Database Schema Mismatch",
                    success=False,
                    context={"framework": "FastAPI", "database": "PostgreSQL"}
                )

            return {
                "success": success,
                "reward": reward,
                "journey_guide": journey.get("trajectory"),
                "confidence_match": journey.get("confidence")
            }

        finally:
            # 5. Khôi phục lại trạng thái ban đầu sạch sẽ để tránh ô nhiễm repo
            self.repo_manager.restore_checkpoint()
