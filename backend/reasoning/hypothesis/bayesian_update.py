import logging
from typing import List

from backend.reasoning.hypothesis.tree import HypothesisTree, HypothesisNode

logger = logging.getLogger(__name__)


class BayesianUpdater:
    @staticmethod
    def update_probabilities(tree: HypothesisTree, evidence_statements: List[str]):
        """Cập nhật xác suất có điều kiện P(H|E) cho các giả thuyết dựa trên các bằng chứng thu thập được."""
        if not evidence_statements:
            return

        for env in evidence_statements:
            env_lower = env.lower()
            likelihoods = []
            
            # 1. Tính toán Likelihood P(E|H) cho từng giả thuyết
            for hyp in tree.hypotheses:
                hyp_name = hyp.name.lower()
                
                # Định nghĩa mức độ tin cậy của bằng chứng tương ứng với giả thuyết
                if "migration" in env_lower and ("migration" in hyp_name or "database" in hyp_name):
                    likelihood = 0.85
                    hyp.evidence_matched.append(env)
                elif "test" in env_lower and "test" in hyp_name:
                    likelihood = 0.75
                    hyp.evidence_matched.append(env)
                elif "dependency" in env_lower and "dependency" in hyp_name:
                    likelihood = 0.80
                    hyp.evidence_matched.append(env)
                else:
                    likelihood = 0.20  # Likelihood nền mặc định
                
                likelihoods.append(likelihood)

            # 2. Tính toán P(E) = tổng (P(E|Hi) * P(Hi))
            p_e = sum(likelihoods[i] * tree.hypotheses[i].probability for i in range(len(tree.hypotheses)))
            
            if p_e > 0:
                # 3. Áp dụng công thức Bayesian: P(Hi|E) = (P(E|Hi) * P(Hi)) / P(E)
                for i, hyp in enumerate(tree.hypotheses):
                    hyp.probability = (likelihoods[i] * hyp.probability) / p_e
            
        # 4. Chuẩn hóa lại tổng xác suất bằng 1.0
        total_p = sum(hyp.probability for hyp in tree.hypotheses)
        if total_p > 0:
            for hyp in tree.hypotheses:
                hyp.probability = round(hyp.probability / total_p, 3)

        logger.info("BayesianUpdater: Hoàn tất cập nhật xác suất chẩn đoán lỗi.")
