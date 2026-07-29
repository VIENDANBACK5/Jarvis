import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class HypothesisRanker:
    @staticmethod
    def rank_hypotheses(hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Xếp hạng các giả thuyết cải tiến dựa trên tỷ số ROI = Expected Gain / Complexity."""
        ranked = []
        for hyp in hypotheses:
            expected_gain = hyp.get("expected_gain", hyp.get("confidence", 0.5))
            # Mức độ phức tạp: 1.0 (thấp), 2.0 (vừa), 3.0 (cao). Mặc định là 1.0
            complexity = float(hyp.get("complexity_effort", 1.0))
            if complexity <= 0:
                complexity = 1.0
                
            roi = expected_gain / complexity
            hyp_copy = hyp.copy()
            hyp_copy["roi"] = round(roi, 3)
            ranked.append(hyp_copy)

        # Sắp xếp theo ROI giảm dần
        ranked.sort(key=lambda x: x["roi"], reverse=True)
        logger.info(f"HypothesisRanker: Ranked {len(ranked)} hypotheses by ROI.")
        return ranked
