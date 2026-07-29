import pytest
from backend.autonomy.research.proposal import ArchitectureProposal


def test_proposal_schema():
    proposal = ArchitectureProposal(
        experiment_id="EXP-2026-PLANNER-042",
        target_filepath="backend/graph/planner.py",
        baseline_version="planner_v12",
        problem_pattern="wrong_tool_selection",
        evidence={
            "failure_count": 35,
            "affected_tasks": ["SWE-12", "SWE-44"]
        },
        hypothesis="Adding tool validation step reduces invalid calls",
        null_hypothesis="No improvement compared with baseline",
        experiment_plan={
            "metrics": ["success_rate", "cost"],
            "cost_limit": 5000
        },
        success_criteria={
            "reward_delta": ">0.05",
            "cost_increase": "<10%",
            "regression": "none"
        },
        confidence_calibration=0.86,
        related_research="ReAct 2022 Paper",
        proposed_patch="[patch content]",
        expected_gain=0.15,
        risk_level="MEDIUM",
        reversible=True,
        rollback_cost="LOW"
    )

    assert proposal.experiment_id == "EXP-2026-PLANNER-042"
    assert proposal.reversible is True
    assert proposal.rollback_cost == "LOW"
