import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class EngineeringMemoryReplay:
    def __init__(self, experience_store_dir: str):
        self.store_dir = experience_store_dir
        # Mock database các tri thức hành trình kỹ thuật cũ
        self.experience_db = [
            {
                "topic": "database migration conflict",
                "trajectory": ["LOCATE: migrations/", "INSPECT: version.py", "MODIFY: migrations/version.py", "VERIFY: pytest migrations"],
                "reward": 0.95
            },
            {
                "topic": "async iterator handling timeout",
                "trajectory": ["LOCATE: backend/async_helpers.py", "INSPECT: iterator.py", "MODIFY: backend/async_helpers.py", "VERIFY: pytest async_tests"],
                "reward": 0.92
            }
        ]

    def retrieve_journey(self, new_issue: str) -> Dict[str, Any]:
        """Truy hồi hành trình kỹ thuật tương tự dựa trên so khớp ngữ nghĩa (Semantic matching)."""
        logger.info(f"MemoryReplay: Bắt đầu tìm kiếm hành trình cho issue: '{new_issue}'")
        
        best_match = None
        highest_similarity = 0.0

        issue_lower = new_issue.lower()

        for exp in self.experience_db:
            # So khớp ngữ nghĩa từ khóa đại diện (semantic overlap mapping)
            overlap_words = set(exp["topic"].split()).intersection(set(issue_lower.split()))
            similarity = len(overlap_words) / max(1, len(set(exp["topic"].split())))
            
            # Nếu có trùng các từ đặc thù async/migration/database
            if "async" in issue_lower and "async" in exp["topic"]:
                similarity += 0.5
            if "migration" in issue_lower and "migration" in exp["topic"]:
                similarity += 0.5

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = exp

        if best_match and highest_similarity > 0.3:
            logger.info(f"MemoryReplay: Đã tìm thấy hành trình tương tự: '{best_match['topic']}' | Độ tương đồng: {highest_similarity:.2f}")
            return {
                "matched_topic": best_match["topic"],
                "trajectory": best_match["trajectory"],
                "confidence": round(highest_similarity, 3)
            }
            
        logger.info("MemoryReplay: Không tìm thấy hành trình cũ phù hợp.")
        return {
            "matched_topic": "generic task",
            "trajectory": ["LOCATE: code/", "INSPECT: files", "MODIFY: codebase", "VERIFY: pytest tests"],
            "confidence": 0.1
        }
