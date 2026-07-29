import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class AutonomyOptimizer:
    def __init__(self, threshold: float = 0.02):
        self.threshold = threshold

    def decide_on_proposal(self, old_reward: float, new_reward: float) -> Tuple[bool, str]:
        """Quyết định chấp nhận hay từ chối đề xuất cải tiến dựa trên Reward Delta."""
        delta = new_reward - old_reward
        logger.info(f"AutonomyOptimizer: Old Reward: {old_reward:.4f} | New Reward: {new_reward:.4f} | Delta: {delta:.4f}")

        if delta >= self.threshold:
            msg = (
                f"Đồng ý tích hợp (Accept): Hiệu năng tăng vượt ngưỡng cải tiến "
                f"(Delta: {delta:.4f} >= Threshold: {self.threshold:.4f}). Tiến hành merge nhánh."
            )
            return True, msg
        else:
            msg = (
                f"Từ chối tích hợp (Reject): Hiệu năng cải tiến không đáng kể hoặc bị suy giảm "
                f"(Delta: {delta:.4f} < Threshold: {self.threshold:.4f}). Tiến hành revert."
            )
            return False, msg
