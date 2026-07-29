import os
import json
import logging
from typing import Dict, Any, List

from backend.autonomy.research.proposal import ArchitectureProposal
from backend.evaluation.repo_manager import RepoManager

logger = logging.getLogger(__name__)


class ResearchCoordinator:
    def __init__(self, workspace_dir: str, research_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.research_dir = os.path.abspath(research_dir)
        os.makedirs(self.research_dir, exist_ok=True)
        
        self.repo_manager = RepoManager(self.workspace_dir)
        self.failed_hyp_path = os.path.join(self.research_dir, "failed_hypothesis.json")
        self.experiments_path = os.path.join(self.research_dir, "experiments.json")

    def run_safety_judge(self, proposal: ArchitectureProposal) -> bool:
        """Thẩm định an toàn mã nguồn để loại bỏ các rủi ro nguy hiểm."""
        target_path = proposal.target_filepath.replace("\\", "/")
        
        # 1. Chặn các file lõi nhạy cảm
        blacklist = ["backend/sandbox/", "backend/security/", "backend/executor/"]
        if any(black in target_path for black in blacklist):
            logger.warning(f"SafetyJudge: Từ chối đề xuất sửa đổi tệp bảo mật hệ thống: {target_path}")
            return False

        # 2. Chặn mức rủi ro High Risk
        if proposal.risk_level == "HIGH":
            logger.warning("SafetyJudge: Từ chối đề xuất có mức độ rủi ro kiến trúc cao (HIGH).")
            return False

        logger.info("SafetyJudge: Đề xuất vượt qua kiểm tra an toàn thành công.")
        return True

    def check_duplicate_hypothesis(self, proposal: ArchitectureProposal) -> bool:
        """Kiểm tra xem giả thuyết đã từng thử nghiệm và thất bại trong quá khứ hay chưa."""
        if not os.path.exists(self.failed_hyp_path):
            return False

        try:
            with open(self.failed_hyp_path, "r", encoding="utf-8") as f:
                failed_hyps = json.load(f)
            
            for item in failed_hyps:
                if item.get("hypothesis") == proposal.hypothesis:
                    logger.info(f"ResearchMemory: Phát hiện giả thuyết trùng lặp đã thất bại trước đó: '{proposal.hypothesis}'")
                    return True
        except Exception as e:
            logger.error(f"ResearchMemory: Lỗi đọc failed hypothesis: {str(e)}")

        return False

    def evaluate_and_evolve(
        self,
        proposal: ArchitectureProposal,
        simulated_reward_delta: float
    ) -> bool:
        """Chạy kiểm thử thực nghiệm đề xuất tiến hóa và ra quyết định sáp nhập (Accept/Reject)."""
        logger.info(f"ResearchCoordinator: Tiến hành thẩm định đề xuất thực nghiệm {proposal.experiment_id}")

        # 1. Thẩm định qua Safety Judge
        if not self.run_safety_judge(proposal):
            return False

        # 2. Kiểm tra trùng lặp giả thuyết trong Research Memory
        if self.check_duplicate_hypothesis(proposal):
            return False

        # 3. Sao lưu repo an toàn
        self.repo_manager.backup_checkpoint()

        try:
            # Mô phỏng tính toán Reward Delta (có áp dụng patch)
            # Tiêu chí: reward_delta vượt ngưỡng gain yêu cầu
            success = simulated_reward_delta >= proposal.expected_gain

            if success:
                logger.info(f"ResearchCoordinator: Thực nghiệm THÀNH CÔNG! Sáp nhập thay đổi. Delta: {simulated_reward_delta}")
                self._save_experiment(proposal, simulated_reward_delta, "success")
                return True
            else:
                logger.info(f"ResearchCoordinator: Thực nghiệm THẤT BẠI. Từ chối sáp nhập và rollback. Delta: {simulated_reward_delta}")
                self._save_failed_hypothesis(proposal, simulated_reward_delta)
                return False

        finally:
            # 4. Phục hồi repo để đảm bảo an toàn nếu thực nghiệm thất bại
            if not success:
                self.repo_manager.restore_checkpoint()

    def _save_experiment(self, proposal: ArchitectureProposal, delta: float, status: str):
        """Ghi nhận thực nghiệm thành công vào bộ nhớ."""
        experiments = []
        if os.path.exists(self.experiments_path):
            try:
                with open(self.experiments_path, "r", encoding="utf-8") as f:
                    experiments = json.load(f)
            except:
                pass

        experiments.append({
            "experiment_id": proposal.experiment_id,
            "hypothesis": proposal.hypothesis,
            "delta": delta,
            "status": status,
            "target": proposal.target_filepath
        })

        with open(self.experiments_path, "w", encoding="utf-8") as f:
            json.dump(experiments, f, indent=2)

    def _save_failed_hypothesis(self, proposal: ArchitectureProposal, delta: float):
        """Ghi nhận giả thuyết thất bại để ngăn lặp lại."""
        failed_hyps = []
        if os.path.exists(self.failed_hyp_path):
            try:
                with open(self.failed_hyp_path, "r", encoding="utf-8") as f:
                    failed_hyps = json.load(f)
            except:
                pass

        failed_hyps.append({
            "hypothesis": proposal.hypothesis,
            "delta": delta,
            "reason": "reward delta below expected gain",
            "target": proposal.target_filepath
        })

        with open(self.failed_hyp_path, "w", encoding="utf-8") as f:
            json.dump(failed_hyps, f, indent=2)
