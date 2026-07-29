import logging
from typing import Dict, Any

from backend.autonomy.evaluation.benchmark import BenchmarkRunner
from backend.self_modify.proposal import SelfModificationProposal

logger = logging.getLogger(__name__)


class SelfModificationEvaluator:
    def __init__(self, workspace_dir: str):
        self.runner = BenchmarkRunner(workspace_dir)

    async def evaluate_change(self, proposal: SelfModificationProposal, test_target: str = "tests/test_openai_api.py") -> float:
        """Đo lường hiệu năng của thay đổi đề xuất bằng cách chạy Quick Evaluation."""
        logger.info(f"SelfModificationEvaluator: Đang đánh giá đề xuất {proposal.proposal_id}...")
        
        # Gọi benchmark runner đo đạc
        reward = await self.runner.run_quick_evaluation(test_target)
        logger.info(f"SelfModificationEvaluator: Reward đo được: {reward:.4f}")
        return reward
