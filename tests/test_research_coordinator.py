import os
import json
import pytest
from unittest.mock import patch, MagicMock
from backend.autonomy.research.proposal import ArchitectureProposal
from backend.autonomy.research.research_coordinator import ResearchCoordinator


@patch("backend.evaluation.repo_manager.RepoManager.backup_checkpoint")
@patch("backend.evaluation.repo_manager.RepoManager.restore_checkpoint")
def test_research_coordinator_success(mock_restore, mock_backup, tmp_path):
    mock_backup.return_value = True
    mock_restore.return_value = True

    coordinator = ResearchCoordinator(str(tmp_path / "ws"), str(tmp_path / "research"))

    proposal = ArchitectureProposal(
        experiment_id="EXP-SUCCESS",
        target_filepath="backend/graph/planner.py",
        baseline_version="v1",
        problem_pattern="wrong_tool_selection",
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

    # 1. Thí nghiệm có reward delta cao (0.15 >= 0.10 expected_gain) -> Accept & Merge
    success = coordinator.evaluate_and_evolve(proposal, simulated_reward_delta=0.15)
    assert success is True

    with open(coordinator.experiments_path, "r") as f:
        data = json.load(f)
    assert data[0]["experiment_id"] == "EXP-SUCCESS"
    assert data[0]["status"] == "success"


@patch("backend.evaluation.repo_manager.RepoManager.backup_checkpoint")
@patch("backend.evaluation.repo_manager.RepoManager.restore_checkpoint")
def test_research_coordinator_failure(mock_restore, mock_backup, tmp_path):
    mock_backup.return_value = True
    mock_restore.return_value = True

    coordinator = ResearchCoordinator(str(tmp_path / "ws"), str(tmp_path / "research"))

    proposal = ArchitectureProposal(
        experiment_id="EXP-FAILURE",
        target_filepath="backend/graph/planner.py",
        baseline_version="v1",
        problem_pattern="wrong_tool_selection",
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

    # 2. Thí nghiệm có reward delta thấp (0.02 < 0.10 expected_gain) -> Reject & Rollback
    success = coordinator.evaluate_and_evolve(proposal, simulated_reward_delta=0.02)
    assert success is False

    with open(coordinator.failed_hyp_path, "r") as f:
        data = json.load(f)
    assert data[0]["hypothesis"] == proposal.hypothesis
    assert data[0]["reason"] == "reward delta below expected gain"
