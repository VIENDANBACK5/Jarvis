import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FailureMiner:
    def __init__(self, trajectory_dir: str):
        self.trajectory_dir = os.path.abspath(trajectory_dir)

    def mine_failures(self) -> Dict[str, Any]:
        """Quét Trajectory Database và bóc tách các mẫu lỗi để tìm bottlenecks chính."""
        stats = {
            "total_tasks_scanned": 0,
            "total_failures": 0,
            "categories": {},
            "most_common_failure": "none"
        }

        if not os.path.exists(self.trajectory_dir):
            logger.warning(f"FailureMiner: Thư mục trajectory không tồn tại: {self.trajectory_dir}")
            return stats

        for filename in os.listdir(self.trajectory_dir):
            if filename.startswith("task_") and filename.endswith(".json"):
                stats["total_tasks_scanned"] += 1
                filepath = os.path.join(self.trajectory_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        events = json.load(f)
                    
                    for evt in events:
                        # Rà soát xem hành động có ghi nhận lỗi không
                        if evt.get("event_type") == "observation" and "error" in evt.get("outputs", {}):
                            stats["total_failures"] += 1
                            err_cat = evt["outputs"].get("category", "unknown_error")
                            stats["categories"][err_cat] = stats["categories"].get(err_cat, 0) + 1
                except Exception as e:
                    logger.error(f"Lỗi khi quét trajectory file {filename}: {str(e)}")

        if stats["categories"]:
            stats["most_common_failure"] = max(stats["categories"], key=stats["categories"].get)
            
        logger.info(
            f"FailureMiner: Scanned {stats['total_tasks_scanned']} tasks | "
            f"Found {stats['total_failures']} failures | Most common: {stats['most_common_failure']}"
        )
        return stats
