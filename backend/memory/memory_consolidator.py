import math
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    def __init__(self, decay_rate: float = 0.05):
        self.decay_rate = decay_rate

    def calculate_memory_score(
        self,
        reward: float,
        success_rate: float,
        age_days: float
    ) -> float:
        """Tính toán điểm memory_score = reward * success_rate * recency_decay."""
        recency_decay = math.exp(-self.decay_rate * age_days)
        return reward * success_rate * recency_decay

    def consolidate(
        self,
        experiences: List[Dict[str, Any]],
        score_threshold: float = 0.30
    ) -> List[Dict[str, Any]]:
        """Lọc bỏ các tri thức rác hoặc quá cũ không còn giá trị."""
        consolidated = []
        for exp in experiences:
            reward = exp.get("reward", 0.5)
            success_rate = exp.get("success_rate", 1.0)
            age_days = exp.get("age_days", 0.0)

            score = self.calculate_memory_score(reward, success_rate, age_days)
            if score >= score_threshold:
                exp_copy = dict(exp)
                exp_copy["memory_score"] = round(score, 3)
                consolidated.append(exp_copy)

        logger.info(f"MemoryConsolidator: Filtered {len(experiences)} down to {len(consolidated)} active memories.")
        return consolidated
