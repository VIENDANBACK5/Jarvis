import logging
from typing import Tuple

from backend.autonomy.experiment.branch_manager import BranchManager
from backend.self_modify.proposal import SelfModificationProposal

logger = logging.getLogger(__name__)


class SelfModificationMerger:
    def __init__(self, workspace_dir: str):
        self.branch_manager = BranchManager(workspace_dir)

    async def execute_integration(
        self,
        proposal: SelfModificationProposal,
        judge_approved: bool,
        old_reward: float,
        new_reward: float,
        branch_name: str,
        threshold: float = 0.02
    ) -> Tuple[bool, str]:
        """Tích hợp merge thay đổi hoặc hoàn nguyên tịnh tiến dựa trên phán quyết của Judge và Evaluator."""
        if not judge_approved:
            await self.branch_manager.rollback_and_cleanup(branch_name)
            return False, "Bác bỏ tích hợp: Đề xuất bị từ chối bởi Independent Judge Agent do rủi ro an toàn."

        delta = new_reward - old_reward
        if delta >= threshold:
            # Tiến hành merge nhánh thử nghiệm
            success = await self.branch_manager.checkout_main_and_merge(branch_name)
            if success:
                msg = f"Tích hợp thành công: Merge thay đổi từ {branch_name} (Delta: {delta:.4f} >= Threshold: {threshold})"
                return True, msg
            else:
                await self.branch_manager.rollback_and_cleanup(branch_name)
                return False, "Lỗi khi merge nhánh phụ vào main."
        else:
            await self.branch_manager.rollback_and_cleanup(branch_name)
            msg = f"Từ chối tích hợp: Hiệu năng kém (Delta: {delta:.4f} < Threshold: {threshold})"
            return False, msg
