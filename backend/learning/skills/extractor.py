import logging
import re
from typing import Dict, Any, List

from backend.learning.experience import Experience
from backend.learning.trajectory.normalizer import TrajectoryNormalizer

logger = logging.getLogger(__name__)


class SkillExtractor:
    @staticmethod
    def extract_skill(experience: Experience) -> Dict[str, Any]:
        """Trích xuất kỹ năng ứng viên từ Experience và quỹ đạo hành động."""
        # 1. Tạo tên kỹ năng từ goal
        goal_cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', experience.goal.lower())
        words = goal_cleaned.split()
        skill_name = "_".join(words[:3]) if words else "generic_fix"
        
        # 2. Tạo trigger tags
        trigger_tags = list(set(words[:5]))
        
        # 3. Chuẩn hóa procedure từ trajectory
        trajectory = experience.trajectory or []
        normalized_actions = TrajectoryNormalizer.normalize_actions(trajectory)
        
        # Xóa các bước trùng lặp liên tiếp để quy trình gọn hơn
        procedure = []
        for action in normalized_actions:
            if not procedure or procedure[-1] != action:
                procedure.append(action)

        if not procedure:
            procedure = ["LOCATE", "INSPECT", "MODIFY", "VERIFY"]

        skill_candidate = {
            "name": skill_name,
            "trigger_tags": trigger_tags,
            "procedure": procedure,
            "success_rate": 1.0,
            "usage_count": 1,
            "reward": experience.reward or 0.8
        }
        
        logger.info(f"SkillExtractor: Extracted skill candidate '{skill_name}' with {len(procedure)} steps.")
        return skill_candidate
