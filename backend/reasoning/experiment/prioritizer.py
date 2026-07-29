import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ExperimentPrioritizer:
    @staticmethod
    def prioritize_experiments(experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Xếp hạng ưu thế các phép thử chẩn đoán dựa trên tỷ số ROI thực nghiệm."""
        ranked = []
        for exp in experiments:
            probability = float(exp.get("probability", 0.5))
            impact = float(exp.get("impact", 1.0))
            cost = float(exp.get("cost", 1.0))
            
            if cost <= 0:
                cost = 1.0
                
            # Công thức: Value = (P(success) * Impact) / Cost
            value = (probability * impact) / cost
            exp_copy = exp.copy()
            exp_copy["value"] = round(value, 3)
            ranked.append(exp_copy)

        # Sắp xếp theo giá trị thực nghiệm giảm dần
        ranked.sort(key=lambda x: x["value"], reverse=True)
        logger.info(f"ExperimentPrioritizer: Prioritized {len(ranked)} diagnostic experiments.")
        return ranked
