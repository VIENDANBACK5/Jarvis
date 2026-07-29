import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class EvidenceGatherer:
    def __init__(self, trajectory_dir: str):
        self.trajectory_dir = os.path.abspath(trajectory_dir)

    def gather_evidence(self, error_category: str) -> Dict[str, Any]:
        """Gom bằng chứng định lượng từ Trajectory Database cho một nhóm lỗi chỉ định."""
        evidence = {
            "error_category": error_category,
            "failed_tasks_count": 0,
            "patterns": []
        }

        if not os.path.exists(self.trajectory_dir):
            return evidence

        unique_errors = set()
        for filename in os.listdir(self.trajectory_dir):
            if filename.startswith("task_") and filename.endswith(".json"):
                filepath = os.path.join(self.trajectory_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        events = json.load(f)
                    
                    for evt in events:
                        if evt.get("event_type") == "observation" and "error" in evt.get("outputs", {}):
                            outputs = evt["outputs"]
                            if outputs.get("category") == error_category:
                                evidence["failed_tasks_count"] += 1
                                # Gom tin nhắn lỗi làm pattern
                                err_msg = outputs.get("error", "unknown error")
                                unique_errors.add(err_msg[:60]) # Giới hạn độ dài để gom nhóm
                except Exception as e:
                    logger.error(f"Lỗi khi đọc trajectory file {filename}: {str(e)}")

        evidence["patterns"] = list(unique_errors)[:5]  # Giới hạn 5 patterns đại diện
        logger.info(
            f"EvidenceGatherer: Gathered evidence for {error_category} | "
            f"Failed tasks: {evidence['failed_tasks_count']} | Unique patterns: {len(evidence['patterns'])}"
        )
        return evidence
