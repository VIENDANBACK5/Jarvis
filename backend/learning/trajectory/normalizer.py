import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TrajectoryNormalizer:
    @staticmethod
    def normalize_actions(trajectory: List[Dict[str, Any]]) -> List[str]:
        """Ánh xạ các hành động thô (raw actions) thành các nhãn ngữ nghĩa trừu tượng."""
        normalized = []
        for evt in trajectory:
            if evt.get("event_type") == "action":
                action_name = evt.get("action_name", "")
                
                # Ánh xạ theo nhóm ngữ nghĩa
                if action_name in ["search_code", "list_files"]:
                    normalized.append("LOCATE")
                elif action_name in ["open_file", "view_file"]:
                    normalized.append("INSPECT")
                elif action_name in ["edit_file", "replace_file_content", "multi_replace_file_content"]:
                    normalized.append("MODIFY")
                elif action_name in ["run_test"]:
                    normalized.append("VERIFY")
                else:
                    normalized.append("ACT")
                    
        return normalized
