import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ActionStep(Dict[str, Any]):
    """Đại diện cho một bước Hành động - Quan sát trong vòng lặp Runtime Loop."""
    pass


class ActionHistoryTracker:
    def __init__(self):
        self.steps: List[Dict[str, Any]] = []

    def record_step(self, action: str, target: str, observation: str, status: str = "SUCCESS"):
        """Ghi nhận một bước hành động mới vào lịch sử phiên làm việc."""
        step = {
            "step_id": len(self.steps) + 1,
            "action": action,
            "target": target,
            "observation": observation,
            "status": status
        }
        self.steps.append(step)
        logger.info(f"ActionHistoryTracker [Step {step['step_id']}]: {action} -> {target} [{status}]")

    def get_summary(self) -> str:
        """Tóm tắt lịch sử vết hành động phục vụ cho suy luận của LLM ở bước tiếp theo."""
        if not self.steps:
            return "Chưa có hành động nào được thực thi."
        
        lines = []
        for s in self.steps:
            lines.append(f"Step {s['step_id']}: [{s['action']}] target='{s['target']}' -> status={s['status']}")
        return "\n".join(lines)
