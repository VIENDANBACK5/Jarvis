import logging
from typing import List, Dict, Any

from backend.reasoning.hypothesis.tree import HypothesisTree, HypothesisNode
from backend.reasoning.diagnosis.diagnostic_experiment import DiagnosticExperiment

logger = logging.getLogger(__name__)


class EvidenceUpdater:
    @staticmethod
    def execute_and_update(
        tree: HypothesisTree,
        experiment: DiagnosticExperiment,
        simulated_outcome: str
    ) -> List[str]:
        """Thực thi chẩn đoán lỗi trong sandbox và cập nhật niềm tin xác suất của Hypothesis Tree."""
        new_evidence = []
        is_confirmed = experiment.success_condition.lower() in simulated_outcome.lower()

        logger.info(
            f"EvidenceUpdater: Chạy phép thử '{experiment.hypothesis}' | "
            f"Outcome: '{simulated_outcome}' | Confirmed: {is_confirmed}"
        )

        target_node = None
        for node in tree.hypotheses:
            if node.name.lower() == experiment.hypothesis.lower():
                target_node = node
                break

        if target_node:
            if is_confirmed:
                # Tăng xác suất Bayesian có trọng số
                target_node.probability = min(0.95, target_node.probability * 1.5)
                msg = f"Evidence: Xác nhận giả thuyết '{experiment.hypothesis}' qua thực nghiệm."
                new_evidence.append(msg)
                target_node.evidence_matched.append(msg)
            else:
                # Hạ xác suất Bayesian về sát 0.0
                target_node.probability = max(0.05, target_node.probability * 0.2)
                msg = f"Evidence: Bác bỏ giả thuyết '{experiment.hypothesis}' qua thực nghiệm."
                new_evidence.append(msg)
                target_node.evidence_matched.append(msg)

        # Chuẩn hóa lại xác suất tổng của cây bằng 1.0
        total_p = sum(hyp.probability for hyp in tree.hypotheses)
        if total_p > 0:
            for hyp in tree.hypotheses:
                hyp.probability = round(hyp.probability / total_p, 3)

        return new_evidence
