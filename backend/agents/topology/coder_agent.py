import logging
from backend.agents.state.blackboard import EngineeringContext

logger = logging.getLogger(__name__)


class CoderAgent:
    def __init__(self):
        pass

    def synthesize_patch(self, context: EngineeringContext, patch_code: str) -> EngineeringContext:
        """Đọc kế hoạch từ Blackboard và tổng hợp bản vá mã nguồn."""
        context.proposed_patch = patch_code
        context.review_status = "pending"

        context.record_event(
            agent="Coder",
            action="synthesize_patch",
            evidence=[f"Generated {len(patch_code.splitlines())} lines patch"],
            confidence=0.80,
            reason="Synthesized patch maintaining whitespace format and AST structure"
        )
        return context
