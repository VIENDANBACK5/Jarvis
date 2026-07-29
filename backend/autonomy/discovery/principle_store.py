import os
import json
import logging
from typing import List

from backend.autonomy.discovery.theory_discovery import EngineeringPrinciple

logger = logging.getLogger(__name__)


class PrincipleStore:
    def __init__(self, storage_dir: str):
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.file_path = os.path.join(self.storage_dir, "principles.json")

    def save_principles(self, principles: List[EngineeringPrinciple]):
        """Lưu trữ đông băng danh sách nguyên lý thiết kế hệ thống xuống đĩa."""
        try:
            data = [p.model_dump() for p in principles]
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("PrincipleStore: Saved principles to principles.json")
        except Exception as e:
            logger.error(f"PrincipleStore: Lỗi khi lưu nguyên lý: {str(e)}")

    def load_principles(self) -> List[EngineeringPrinciple]:
        """Nạp lại danh sách nguyên lý thiết kế từ đĩa."""
        if not os.path.exists(self.file_path):
            return []

        principles = []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                principles.append(EngineeringPrinciple(**item))
        except Exception as e:
            logger.error(f"PrincipleStore: Lỗi khi nạp lại nguyên lý: {str(e)}")
            
        return principles
