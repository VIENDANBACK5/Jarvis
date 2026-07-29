import pytest
from backend.agents.state.blackboard import EngineeringContext, AgentDecisionEvent


def test_blackboard_event_sourcing():
    context = EngineeringContext(task_issue="Fix DB error")
    
    context.record_event(
        agent="Architect",
        action="plan",
        evidence=["AST parsed"],
        confidence=0.85,
        reason="Target file identified"
    )

    assert len(context.events) == 1
    assert context.events[0].agent == "Architect"
    assert context.events[0].action == "plan"
    assert context.events[0].confidence == 0.85
