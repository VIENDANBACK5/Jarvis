import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Experience(BaseModel):
    task_id: str
    goal: str
    environment: Dict[str, str] = Field(default_factory=dict)
    trajectory: List[Dict[str, Any]] = Field(default_factory=list)
    failure: Optional[Dict[str, str]] = None  # {"category": "...", "root_cause": "..."}
    final_solution: Optional[Dict[str, str]] = None  # {"patch": "..."}
    reward: float = 0.0


class ExperienceStore:
    def __init__(self, store_dir: str):
        self.store_dir = os.path.abspath(store_dir)
        os.makedirs(self.store_dir, exist_ok=True)

    def save_experience(self, exp: Experience) -> str:
        """Lưu trữ đối tượng Experience dạng JSON vào thư mục store_dir."""
        filepath = os.path.join(self.store_dir, f"exp_{exp.task_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(exp.model_dump(), f, indent=2, ensure_ascii=False)
            logger.info(f"ExperienceStore: Đã lưu trữ kinh nghiệm của task {exp.task_id} tại {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Lỗi khi lưu trữ Experience cho task {exp.task_id}: {str(e)}")
            return ""

    def load_experience(self, task_id: str) -> Optional[Experience]:
        """Nạp lại kinh nghiệm của task_id từ file JSON."""
        filepath = os.path.join(self.store_dir, f"exp_{task_id}.json")
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Experience(**data)
        except Exception as e:
            logger.error(f"Lỗi khi đọc file Experience cho task {task_id}: {str(e)}")
            return None
