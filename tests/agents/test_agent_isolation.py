import pytest
from backend.agents.state.blackboard import EngineeringContext
from backend.agents.topology.architect_agent import ArchitectAgent
from backend.agents.topology.coder_agent import CoderAgent


def test_agent_role_isolation():
    context = EngineeringContext(task_issue="Fix payment timeout")
    architect = ArchitectAgent()
    coder = CoderAgent()

    # Architect lập kế hoạch
    context = architect.plan_architecture(context, "backend/api/payment.py")
    assert "backend/api/payment.py" in context.affected_files

    # Coder tổng hợp patch
    context = coder.synthesize_patch(context, "[PATCH] Add timeout parameter")
    assert context.proposed_patch == "[PATCH] Add timeout parameter"

    # Ghi vết hành động phân biệt rõ rệt vai trò tác viên
    assert context.events[0].agent == "Architect"
    assert context.events[1].agent == "Coder"
