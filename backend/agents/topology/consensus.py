import logging
from typing import List, Dict, Any

from backend.agents.state.blackboard import AgentDecisionEvent

logger = logging.getLogger(__name__)


class ConsensusEngine:
    def __init__(self):
        pass

    def calculate_decision_score(self, event: AgentDecisionEvent, historical_accuracy: float = 0.90) -> float:
        """Tính toán điểm số đồng thuận có trọng số bằng chứng (Evidence-Weighted Consensus)."""
        evidence_quality = min(len(event.evidence) / 5.0, 1.0)
        score = event.confidence * evidence_quality * historical_accuracy
        return round(score, 3)

    def resolve_consensus(self, events: List[AgentDecisionEvent]) -> AgentDecisionEvent:
        """Phân xử bất đồng ý kiến giữa các tác viên dựa trên bằng chứng thu thập thực tế."""
        if not events:
            return None

        best_event = None
        best_score = -1.0

        for event in events:
            score = self.calculate_decision_score(event)
            if score > best_score:
                best_score = score
                best_event = event

        logger.info(f"ConsensusEngine: Resolved decision in favor of [{best_event.agent}] with score {best_score}")
        return best_event
