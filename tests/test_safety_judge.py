import pytest
from backend.autonomy.research.proposal import ArchitectureProposal
from backend.autonomy.research.research_coordinator import ResearchCoordinator


def test_safety_judge(tmp_path):
    coordinator = ResearchCoordinator(str(tmp_path / "ws"), str(tmp_path / "research"))

    # 1. Đề xuất có file target trong blacklist -> Reject
    proposal_blacklisted = ArchitectureProposal(
        experiment_id="EXP-1",
        target_filepath="backend/sandbox/executor.py",
        baseline_version="v1",
        problem_pattern="planning_error",
        evidence={},
        hypothesis="H1",
        null_hypothesis="H0",
        experiment_plan={},
        success_criteria={},
        related_research="None",
        proposed_patch="patch",
        expected_gain=0.10,
        risk_level="LOW"
    )
    assert coordinator.run_safety_judge(proposal_blacklisted) is False

    # 2. Đề xuất có risk level HIGH -> Reject
    proposal_high_risk = ArchitectureProposal(
        experiment_id="EXP-2",
        target_filepath="backend/graph/coordinator.py",
        baseline_version="v1",
        problem_pattern="planning_error",
        evidence={},
        hypothesis="H1",
        null_hypothesis="H0",
        experiment_plan={},
        success_criteria={},
        related_research="None",
        proposed_patch="patch",
        expected_gain=0.10,
        risk_level="HIGH"
    )
    assert coordinator.run_safety_judge(proposal_high_risk) is False

    # 3. Đề xuất an toàn -> Allow
    proposal_safe = ArchitectureProposal(
        experiment_id="EXP-3",
        target_filepath="backend/graph/planner.py",
        baseline_version="v1",
        problem_pattern="planning_error",
        evidence={},
        hypothesis="H1",
        null_hypothesis="H0",
        experiment_plan={},
        success_criteria={},
        related_research="None",
        proposed_patch="patch",
        expected_gain=0.10,
        risk_level="MEDIUM"
    )
    assert coordinator.run_safety_judge(proposal_safe) is True
