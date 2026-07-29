import pytest
from backend.agents.state.blackboard import EngineeringContext
from backend.agents.topology.architect_agent import ArchitectAgent
from backend.agents.topology.coder_agent import CoderAgent
from backend.agents.topology.reviewer_agent import ReviewerAgent
from backend.agents.topology.harness_agent import HarnessAgent


def test_long_horizon_reasoning_e2e_flow():
    """Kiểm định luồng E2E đồng thuận đa tác viên qua Shared Blackboard."""
    context = EngineeringContext(task_issue="Fix database connection timeout")
    
    architect = ArchitectAgent()
    coder = CoderAgent()
    reviewer = ReviewerAgent()
    harness = HarnessAgent()

    # 1. Architect lập kế hoạch
    context = architect.plan_architecture(context, "backend/models/database.py")
    
    # 2. Coder tổng hợp patch
    context = coder.synthesize_patch(context, "[PATCH] Increase connection pool size to 20")
    
    # 3. Reviewer rà soát phản biện
    context = reviewer.audit_patch(context)
    assert context.review_status == "approved"

    # 4. Harness thực thi Sandbox
    context = harness.execute_in_sandbox(context, simulated_success=True)
    
    # Tất cả các tác viên phải để lại vết sự kiện trong Event Sourcing Timeline
    agents_recorded = [e.agent for e in context.events]
    assert "Architect" in agents_recorded
    assert "Coder" in agents_recorded
    assert "Reviewer" in agents_recorded
    assert "Harness" in agents_recorded
