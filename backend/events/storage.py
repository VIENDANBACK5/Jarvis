import os
import json
import logging
from typing import List, Dict, Any

from backend.events.stream import EventStream

logger = logging.getLogger(__name__)


class TrajectoryStorage:
    def __init__(self, trajectory_dir: str):
        self.trajectory_dir = os.path.abspath(trajectory_dir)
        os.makedirs(self.trajectory_dir, exist_ok=True)

    def save_trajectory(self, task_id: str, stream: EventStream) -> str:
        """Lưu trữ luồng sự kiện của task_id thành file JSON trajectory."""
        filepath = os.path.join(self.trajectory_dir, f"task_{task_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(stream.to_dict_list(), f, indent=2, ensure_ascii=False)
            logger.info(f"TrajectoryStorage: Saved trajectory for {task_id} to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Lỗi khi lưu trajectory file cho task {task_id}: {str(e)}")
            return ""

    def load_trajectory(self, task_id: str, stream: EventStream) -> bool:
        """Nạp lại luồng sự kiện của task_id từ file JSON trajectory."""
        filepath = os.path.join(self.trajectory_dir, f"task_{task_id}.json")
        if not os.path.exists(filepath):
            logger.warning(f"Không tìm thấy trajectory file tại: {filepath}")
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                dict_list = json.load(f)
            stream.load_from_dict_list(dict_list)
            logger.info(f"TrajectoryStorage: Loaded trajectory for {task_id} from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi đọc file trajectory cho task {task_id}: {str(e)}")
            return False
