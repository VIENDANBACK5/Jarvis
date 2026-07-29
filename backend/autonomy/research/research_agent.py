import os
import json
import logging
from typing import Dict, Any, List

from backend.autonomy.research.proposal import ArchitectureProposal

logger = logging.getLogger(__name__)


class ResearchAgent:
    def __init__(self, paper_db_path: str):
        self.paper_db_path = os.path.abspath(paper_db_path)
        # Mock database các tài liệu khoa học chuẩn
        self.default_papers = [
            {
                "id": "react_2022",
                "title": "ReAct: Synergizing Reasoning and Acting in Language Models",
                "claims": [
                    {
                        "statement": "interleaving reasoning and acting reduces hallucinated actions",
                        "applicable_failure": ["wrong_tool_selection", "planning_failure"],
                        "confidence": 0.86
                    }
                ]
            },
            {
                "id": "self_refine_2023",
                "title": "Self-Refine: Iterative Refinement with Feedback",
                "claims": [
                    {
                        "statement": "iterative feedback loops improve code editing success",
                        "applicable_failure": ["code_patch_fail", "syntax_error"],
                        "confidence": 0.90
                    }
                ]
            }
        ]
        self._ensure_paper_db()

    def _ensure_paper_db(self):
        """Khởi tạo database paper mặc định nếu chưa tồn tại."""
        if not os.path.exists(self.paper_db_path):
            os.makedirs(os.path.dirname(self.paper_db_path), exist_ok=True)
            with open(self.paper_db_path, "w", encoding="utf-8") as f:
                json.dump(self.default_papers, f, indent=2)

    def conduct_research(
        self,
        failure_pattern: str,
        failure_count: int,
        target_filepath: str
    ) -> ArchitectureProposal:
        """Thực hiện nghiên cứu từ tài liệu khoa học xác thực và sinh đề xuất cải tiến kiến trúc."""
        logger.info(f"ResearchAgent: Phân tích mẫu lỗi '{failure_pattern}' | Tần suất: {failure_count}")

        # 1. Quét tìm paper claims trong database
        matched_claim = None
        matched_paper = None
        try:
            with open(self.paper_db_path, "r", encoding="utf-8") as f:
                papers = json.load(f)
            
            for paper in papers:
                for claim in paper.get("claims", []):
                    if any(err in failure_pattern.lower() for err in claim.get("applicable_failure", [])):
                        matched_claim = claim
                        matched_paper = paper
                        break
        except Exception as e:
            logger.error(f"ResearchAgent: Lỗi truy vấn paper db: {str(e)}")

        # 2. Xây dựng thông tin related_research
        if matched_claim and matched_paper:
            related_research = f"Paper: '{matched_paper['title']}' | Claim: {matched_claim['statement']}"
            confidence = matched_claim["confidence"]
        else:
            related_research = "Paper: Generic Agent Engineering guidelines | Claim: Standard modular prompting"
            confidence = 0.5

        # 3. Tạo đề xuất thực nghiệm chẩn đoán định dạng đầy đủ
        proposal = ArchitectureProposal(
            experiment_id=f"EXP-2026-RESEARCH-{failure_pattern.upper().replace(' ', '_')[:10]}",
            target_filepath=target_filepath,
            baseline_version="baseline_v1.0",
            problem_pattern=failure_pattern,
            evidence={
                "failure_count": failure_count,
                "benchmark_metric": "reward < 0.70"
            },
            hypothesis=f"Applying ReAct style prompts will solve {failure_pattern} failures.",
            null_hypothesis=f"No improvement on {failure_pattern} failures compared with baseline.",
            experiment_plan={
                "metrics": ["success_rate", "token_cost"],
                "cost_limit": 50000
            },
            success_criteria={
                "reward_delta": ">0.05",
                "cost_increase": "<10%"
            },
            confidence_calibration=confidence,
            related_research=related_research,
            proposed_patch="[PROMPT UPDATE] interleaving reasoning steps before action calling.",
            expected_gain=0.15,
            risk_level="LOW" if "prompt" in target_filepath else "MEDIUM",
            reversible=True,
            rollback_cost="LOW"
        )

        logger.info(f"ResearchAgent: Sinh đề xuất thành công. Exp ID: {proposal.experiment_id}")
        return proposal
