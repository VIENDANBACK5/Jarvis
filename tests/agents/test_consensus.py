import pytest
from backend.agents.state.blackboard import AgentDecisionEvent
from backend.agents.topology.consensus import ConsensusEngine


def test_evidence_weighted_consensus():
    engine = ConsensusEngine()

    event_architect = AgentDecisionEvent(
        agent="Architect",
        action="hypothesis",
        evidence=["Single log match"],  # 1 evidence
        confidence=0.90,
        reason="Initial guess"
    )

    event_reviewer = AgentDecisionEvent(
        agent="Reviewer",
        action="hypothesis",
        evidence=["Log 1", "Log 2", "Stacktrace line 40", "AST match", "Test fail"],  # 5 evidence items
        confidence=0.85,
        reason="Deep static analysis"
    )

    best_event = engine.resolve_consensus([event_architect, event_reviewer])

    # Reviewer thu thập được nhiều evidence chất lượng hơn nên giành chiến thắng đồng thuận
    assert best_event.agent == "Reviewer"
