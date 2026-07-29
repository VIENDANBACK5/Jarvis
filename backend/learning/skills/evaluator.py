import math
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SkillEvaluator:
    @staticmethod
    def calculate_confidence(skill: Dict[str, Any]) -> float:
        """Tính toán chỉ số tin cậy của kỹ năng dựa trên hiệu năng thực tế."""
        reward = float(skill.get("reward", 0.5))
        usage_count = int(skill.get("usage_count", 1))
        success_rate = float(skill.get("success_rate", 1.0))

        # Công thức: Confidence = reward * log(usage_count + 1) * success_rate
        confidence = reward * math.log(usage_count + 1) * success_rate
        return round(confidence, 3)

    @staticmethod
    def evaluate_ab_test(has_skill_reward: float, no_skill_reward: float) -> bool:
        """Giả lập A/B testing: Xác minh chạy có dùng skill tốt hơn không dùng skill."""
        improved = has_skill_reward > no_skill_reward
        logger.info(
            f"SkillEvaluator: A/B Testing | With Skill Reward: {has_skill_reward:.3f} | "
            f"Without Skill Reward: {no_skill_reward:.3f} | Better: {improved}"
        )
        return improved
