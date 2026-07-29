import os
import json
import pytest
from backend.autonomy.research.proposal import ArchitectureProposal
from backend.autonomy.research.research_coordinator import ResearchCoordinator


def test_research_memory(tmp_path):
    research_dir = tmp_path / "research"
    os.makedirs(research_dir)
    
    coordinator = ResearchCoordinator(str(tmp_path / "ws"), str(research_dir))

    # Ghi nhận một giả thuyết thất bại giả lập vào file failed_hypothesis.json
    failed_data = [
        {
            "hypothesis": "Adding tool validation step reduces invalid calls",
            "delta": -0.02,
            "reason": "reward delta below expected gain"
        }
    ]
    with open(coordinator.failed_hyp_path, "w", encoding="utf-8") as f:
        json.dump(failed_data, f)

    # Đề xuất có giả thuyết trùng lặp -> Reject
    proposal_dup = ArchitectureProposal(
        experiment_id="EXP-1",
        target_filepath="backend/graph/planner.py",
        baseline_version="v1",
        problem_pattern="planning_error",
        evidence={},
        hypothesis="Adding tool validation step reduces invalid calls",
        null_hypothesis="H0",
        experiment_plan={},
        success_criteria={},
        related_research="None",
        proposed_patch="patch",
        expected_gain=0.10,
        risk_level="MEDIUM"
    )
    
    assert coordinator.check_duplicate_hypothesis(proposal_dup) is True

    # Đề xuất giả thuyết mới -> Allow (False indicating not duplicate)
    proposal_new = ArchitectureProposal(
        experiment_id="EXP-2",
        target_filepath="backend/graph/planner.py",
        baseline_version="v1",
        problem_pattern="planning_error",
        evidence={},
        hypothesis="A completely new hypothesis statement",
        null_hypothesis="H0",
        experiment_plan={},
        success_criteria={},
        related_research="None",
        proposed_patch="patch",
        expected_gain=0.10,
        risk_level="MEDIUM"
    )
    assert coordinator.check_duplicate_hypothesis(proposal_new) is False
