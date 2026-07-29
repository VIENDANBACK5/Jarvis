import logging
from backend.agents.state.blackboard import EngineeringContext

logger = logging.getLogger(__name__)


class SecurityAgent:
    def __init__(self):
        pass

    def scan_security(self, context: EngineeringContext) -> bool:
        """Quét static analysis rà soát các lỗ hổng an ninh nguy hiểm."""
        patch = context.proposed_patch.lower()
        dangerous_patterns = ["eval(", "exec(", "os.system(", "subprocess.call("]

        for pattern in dangerous_patterns:
            if pattern in patch:
                context.review_status = "rejected"
                context.review_reason = f"Security Violation: Dangerous function call '{pattern}' detected"
                context.record_event(
                    agent="Security",
                    action="scan_security_reject",
                    evidence=[f"Pattern match: {pattern}"],
                    confidence=0.99,
                    reason=context.review_reason
                )
                return False

        context.record_event(
            agent="Security",
            action="scan_security_pass",
            evidence=["No dangerous execution patterns found"],
            confidence=0.95,
            reason="Static security analysis clean"
        )
        return True
