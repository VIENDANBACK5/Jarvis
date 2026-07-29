import os
import json
import logging
from typing import List, Dict, Any, Tuple

from backend.learning.experience import Experience, ExperienceStore

logger = logging.getLogger(__name__)


class ExperienceRetriever:
    def __init__(self, store_dir: str):
        self.store = ExperienceStore(store_dir)

    def retrieve_similar_experiences(self, goal: str, limit: int = 3) -> List[Experience]:
        """Truy hồi danh sách các trải nghiệm tương tự nhất trong quá khứ dựa trên goal."""
        matched: List[Tuple[float, Experience]] = []
        
        # Đọc tất cả các file JSON trong thư mục kinh nghiệm
        store_dir = self.store.store_dir
        if not os.path.exists(store_dir):
            return []

        goal_words = set(goal.lower().split())
        if not goal_words:
            return []

        for filename in os.listdir(store_dir):
            if filename.startswith("exp_") and filename.endswith(".json"):
                task_id = filename[4:-5]
                exp = self.store.load_experience(task_id)
                if exp:
                    # Tính Jaccard similarity đơn giản giữa các từ của hai goal
                    exp_words = set(exp.goal.lower().split())
                    intersection = goal_words.intersection(exp_words)
                    union = goal_words.union(exp_words)
                    similarity = len(intersection) / len(union) if union else 0.0
                    
                    if similarity > 0.0:
                        matched.append((similarity, exp))

        # Sắp xếp theo độ tương đồng giảm dần, sau đó theo điểm thưởng (reward) giảm dần
        matched.sort(key=lambda x: (x[0], x[1].reward), reverse=True)
        return [item[1] for item in matched[:limit]]
