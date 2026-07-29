import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class HierarchicalPlanner:
    def __init__(self):
        self.sub_goals: List[Dict[str, Any]] = []

    def decompose_task(self, task_goal: str) -> List[Dict[str, Any]]:
        """Phân rã tác vụ lớn thành các sub-goals chiến lược nhỏ gọn."""
        self.sub_goals = [
            {"id": 1, "goal": "Scan repository and parse AST symbols", "completed": False},
            {"id": 2, "goal": "Retrieve online experiences and generate hypothesis", "completed": False},
            {"id": 3, "goal": "Synthesize patch in target file", "completed": False},
            {"id": 4, "goal": "Adversarial review and static security audit", "completed": False},
            {"id": 5, "goal": "Sandbox pytest verification", "completed": False}
        ]
        logger.info(f"HierarchicalPlanner: Decomposed task into {len(self.sub_goals)} sub-goals.")
        return self.sub_goals

    def replan_on_rejection(self, rejection_reason: str) -> List[Dict[str, Any]]:
        """Tái lập kế hoạch (Re-plan) khi Reviewer từ chối bản vá thay vì làm lại mù quáng."""
        logger.warning(f"HierarchicalPlanner: Re-planning triggered due to rejection: {rejection_reason}")
        # Reset step 3 (Patch) & step 4 (Review) để suy luận lại giả thuyết
        self.sub_goals[2]["completed"] = False
        self.sub_goals[3]["completed"] = False
        return self.sub_goals
