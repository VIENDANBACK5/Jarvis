import os
import json
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ArchitectureStore:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.store_dir = os.path.join(self.workspace_dir, "backend", "world_model", "storage")
        os.makedirs(self.store_dir, exist_ok=True)

    def save_graph_state(self, dep_graph_data: Dict[str, Any], test_graph_data: Dict[str, Any]):
        """Lưu trữ đông băng cấu trúc đồ thị xuống đĩa dạng tệp tin JSON."""
        dep_path = os.path.join(self.store_dir, "dependency.json")
        test_path = os.path.join(self.store_dir, "test_graph.json")

        try:
            with open(dep_path, "w", encoding="utf-8") as f:
                json.dump(dep_graph_data, f, indent=2)
            with open(test_path, "w", encoding="utf-8") as f:
                json.dump(test_graph_data, f, indent=2)
            logger.info("ArchitectureStore: Saved graphs dependency.json and test_graph.json")
        except Exception as e:
            logger.error(f"ArchitectureStore: Lỗi khi lưu trữ cấu trúc đồ thị: {str(e)}")

    def load_graph_state(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Nạp lại cấu trúc đồ thị từ đĩa."""
        dep_path = os.path.join(self.store_dir, "dependency.json")
        test_path = os.path.join(self.store_dir, "test_graph.json")
        
        dep_data, test_data = {}, {}
        try:
            if os.path.exists(dep_path):
                with open(dep_path, "r", encoding="utf-8") as f:
                    dep_data = json.load(f)
            if os.path.exists(test_path):
                with open(test_path, "r", encoding="utf-8") as f:
                    test_data = json.load(f)
        except Exception as e:
            logger.error(f"ArchitectureStore: Lỗi khi nạp lại đồ thị: {str(e)}")
            
        return dep_data, test_data
