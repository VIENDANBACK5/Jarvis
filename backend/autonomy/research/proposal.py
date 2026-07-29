import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ArchitectureProposal(BaseModel):
    experiment_id: str = Field(..., description="Mã định danh đề xuất thực nghiệm.")
    target_filepath: str = Field(..., description="File mã nguồn hoặc prompt cần sửa đổi.")
    baseline_version: str = Field(..., description="Phiên bản đối chứng cơ sở.")
    problem_pattern: str = Field(..., description="Mẫu lỗi lặp lại cần giải quyết.")
    evidence: Dict[str, Any] = Field(..., description="Bằng chứng thu thập định lượng.")
    hypothesis: str = Field(..., description="Giả thuyết nghiên cứu khoa học.")
    null_hypothesis: str = Field(..., description="Giả thuyết không (đối chứng).")
    experiment_plan: Dict[str, Any] = Field(..., description="Kế hoạch chạy thực nghiệm.")
    success_criteria: Dict[str, Any] = Field(..., description="Tiêu chí đánh giá thành công.")
    confidence_calibration: float = Field(default=0.5, description="Độ tin cậy của bằng chứng.")
    related_research: str = Field(..., description="Tài liệu nghiên cứu khoa học đối chiếu.")
    proposed_patch: str = Field(..., description="Bản vá đề xuất.")
    expected_gain: float = Field(..., description="Mức tăng điểm reward dự kiến.")
    risk_level: str = Field(..., description="Mức độ rủi ro: LOW | MEDIUM | HIGH.")
    reversible: bool = Field(default=True, description="Có khả năng rollback không.")
    rollback_cost: str = Field(default="LOW", description="Chi phí rollback.")
