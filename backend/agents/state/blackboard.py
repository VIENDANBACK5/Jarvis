import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentDecisionEvent(BaseModel):
    agent: str = Field(..., description="Tên tác viên thực thi (Architect | Coder | Reviewer | Security | Harness).")
    action: str = Field(..., description="Hành động quyết định.")
    evidence: List[str] = Field(default_factory=list, description="Bằng chứng thu thập.")
    confidence: float = Field(default=0.5, description="Mức độ tin cậy.")
    reason: Optional[str] = Field(default="", description="Lý do chi tiết.")


class EngineeringContext(BaseModel):
    task_issue: str = Field(default="", description="Mô tả bài toán lỗi cần giải quyết.")
    affected_files: List[str] = Field(default_factory=list, description="Danh sách các file chịu ảnh hưởng.")
    current_hypothesis: str = Field(default="", description="Giả thuyết chẩn đoán lỗi hiện tại.")
    proposed_patch: str = Field(default="", description="Bản vá đề xuất của Coder.")
    review_status: str = Field(default="pending", description="Trạng thái kiểm duyệt: pending | approved | rejected.")
    review_reason: str = Field(default="", description="Lý do kiểm duyệt.")
    events: List[AgentDecisionEvent] = Field(default_factory=list, description="Dòng thời gian sự kiện (Event Sourcing Timeline).")

    def record_event(
        self,
        agent: str,
        action: str,
        evidence: List[str] = None,
        confidence: float = 0.5,
        reason: str = ""
    ):
        """Ghi nhận sự kiện quyết định mới vào Event Sourcing Timeline."""
        event = AgentDecisionEvent(
            agent=agent,
            action=action,
            evidence=evidence or [],
            confidence=confidence,
            reason=reason
        )
        self.events.append(event)
        logger.info(f"Blackboard Event [{agent} -> {action}]: {reason} (Confidence: {confidence})")
