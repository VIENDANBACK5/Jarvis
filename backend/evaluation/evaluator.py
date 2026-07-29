import logging
from backend.evaluation.patch_quality import PatchQualityAnalyzer

logger = logging.getLogger(__name__)


class MultiObjectiveEvaluator:
    def __init__(self):
        # Trọng số chuẩn của hàm Reward đa mục tiêu
        self.w1 = 0.5  # Success (Pass test rate)
        self.w2 = 0.3  # Quality score of patch
        self.w3 = 0.1  # Cost (Tokens count weight)
        self.w4 = 0.1  # Time weight

    def calculate_reward(
        self,
        success_rate: float,
        patch_content: str,
        token_count: int,
        duration_sec: float
    ) -> float:
        """Tính toán điểm phần thưởng đa mục tiêu tối ưu."""
        # 1. Điểm test suite
        success = float(success_rate)

        # 2. Điểm chất lượng bản vá
        quality = PatchQualityAnalyzer.evaluate_patch(patch_content)

        # 3. Điểm chi phí (Cost) - chuẩn hóa theo ngưỡng 50,000 tokens tối đa
        cost_penalty = min(1.0, token_count / 50000.0)

        # 4. Điểm thời gian (Time) - chuẩn hóa theo ngưỡng 600 giây tối đa
        time_penalty = min(1.0, duration_sec / 600.0)

        # Công thức: Reward = w1*Success + w2*Quality - w3*Cost - w4*Time
        reward = (self.w1 * success) + (self.w2 * quality) - (self.w3 * cost_penalty) - (self.w4 * time_penalty)
        reward = round(max(0.0, min(1.0, reward)), 3)

        logger.info(
            f"MultiObjectiveEvaluator: Success={success:.2f} | Quality={quality:.2f} | "
            f"Cost Penalty={cost_penalty:.2f} | Time Penalty={time_penalty:.2f} | Final Reward={reward:.3f}"
        )
        return reward
