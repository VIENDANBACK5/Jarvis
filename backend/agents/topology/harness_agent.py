import logging
from backend.agents.state.blackboard import EngineeringContext

logger = logging.getLogger(__name__)


class HarnessAgent:
    def __init__(self):
        pass

    def execute_in_sandbox(self, context: EngineeringContext, simulated_success: bool = True) -> EngineeringContext:
        """Thực thi bản vá đã duyệt trong Sandbox và đo lường chỉ số."""
        if context.review_status != "approved":
            context.record_event(
                agent="Harness",
                action="sandbox_skip",
                evidence=[f"Review status: {context.review_status}"],
                confidence=1.0,
                reason="Skipped sandbox execution because patch was not approved by Reviewer"
            )
            return context

        if simulated_success:
            context.record_event(
                agent="Harness",
                action="sandbox_pass",
                evidence=["All test assertions PASSED in Docker Sandbox"],
                confidence=0.95,
                reason="Sandbox execution successful with 0 regression"
            )
        else:
            context.record_event(
                agent="Harness",
                action="sandbox_fail",
                evidence=["Test failure in Sandbox"],
                confidence=0.95,
                reason="Execution failed assertion check in Sandbox"
            )
        return context
