import pytest
from backend.agents.state.blackboard import EngineeringContext
from backend.agents.topology.reviewer_agent import ReviewerAgent


def test_reviewer_adversarial_security_reject():
    reviewer = ReviewerAgent()
    context = EngineeringContext(
        task_issue="Execute user code safely",
        proposed_patch="def run(code): return eval(code)"
    )

    context = reviewer.audit_patch(context)

    # Reviewer độc lập phải bắt được hàm nguy hiểm eval() và reject bản vá
    assert context.review_status == "rejected"
    assert "Security Violation" in context.review_reason
