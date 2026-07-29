import uuid
from typing import Dict, Any
from pydantic import BaseModel, Field


class SelfModificationProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"prop-{uuid.uuid4().hex[:8]}")
    target_file: str = Field(..., description="Đường dẫn tương đối đến tệp tin cần sửa đổi.")
    proposed_change: str = Field(..., description="Nội dung mã nguồn hoặc prompts đề xuất thay đổi.")
    confidence: float = Field(default=0.85, description="Độ tự tin của Agent vào đề xuất này.")
    rationale: str = Field(..., description="Lý do khoa học và bằng chứng tối ưu hóa của đề xuất.")
