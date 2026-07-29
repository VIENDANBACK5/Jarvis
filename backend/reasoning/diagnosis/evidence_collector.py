import os
import logging
from typing import Dict, Any, List

from backend.world_model.analysis.impact_predictor import ImpactPredictor
from backend.learning.experience import ExperienceStore

logger = logging.getLogger(__name__)


class EvidenceCollector:
    def __init__(self, workspace_dir: str, experience_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.predictor = ImpactPredictor(self.workspace_dir)
        self.exp_store = ExperienceStore(experience_dir)

    def collect_evidence(self, error_filepath: str, error_message: str) -> List[str]:
        """Tổng hợp bằng chứng cấu trúc tĩnh từ World Model và lịch sử kinh nghiệm."""
        evidence = []
        
        # 1. Thu thập thông tin từ World Model
        if error_filepath:
            full_path = os.path.abspath(os.path.join(self.workspace_dir, error_filepath))
            if os.path.exists(full_path):
                impact_data = self.predictor.calculate_impact_score(full_path)
                
                # Bằng chứng về độ bao phủ test
                tests_count = len(impact_data.get("affected_tests", []))
                evidence.append(f"World Model: File có {tests_count} file tests bao phủ.")
                
                # Bằng chứng về độ phụ thuộc import
                dep_count = len(impact_data.get("affected_modules", []))
                evidence.append(f"World Model: File có {dep_count} tệp tin import phụ thuộc.")
                
                # Bằng chứng về mức độ rủi ro sửa đổi
                evidence.append(f"World Model: Mức độ rủi ro sửa đổi tệp tin này là {impact_data.get('risk_level')}.")

        # 2. Truy hồi lịch sử từ Experience Memory
        import os as py_os
        similar_failures = 0
        if py_os.path.exists(self.exp_store.store_dir):
            for filename in py_os.listdir(self.exp_store.store_dir):
                if filename.startswith("exp_") and filename.endswith(".json"):
                    task_id = filename[4:-5]
                    exp = self.exp_store.load_experience(task_id)
                    if exp and exp.reward and exp.reward < 0.6:  # Kinh nghiệm thất bại trước đây
                        if error_message.lower() in exp.goal.lower():
                            similar_failures += 1
                            
        if similar_failures > 0:
            evidence.append(f"Experience Store: Ghi nhận {similar_failures} lần lỗi tương tự trong quá khứ.")
            
        logger.info(f"EvidenceCollector: Collected {len(evidence)} evidence statements.")
        return evidence
