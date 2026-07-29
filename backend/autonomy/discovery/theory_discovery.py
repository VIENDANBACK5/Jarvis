import os
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EngineeringPrinciple(BaseModel):
    id: str = Field(..., description="Mã định danh nguyên lý kỹ thuật.")
    symptom_pattern: str = Field(..., description="Triệu chứng lỗi lặp lại.")
    context: Dict[str, Any] = Field(..., description="Ngữ cảnh phát hiện lỗi.")
    derived_rule: str = Field(..., description="Quy tắc cứng rút ra để bảo vệ hệ thống.")
    confidence: float = Field(default=0.5, description="Độ tin cậy của quy tắc.")
    status: str = Field(default="candidate", description="Trạng thái: candidate | validating | validated | rejected")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Kết quả chi tiết thẩm định thực nghiệm.")


class TheoryDiscoveryEngine:
    def __init__(self):
        pass

    def discover_principles(self, failed_hyps_path: str) -> List[EngineeringPrinciple]:
        """Phân tích các mẫu lỗi lặp lại trong lịch sử thất bại và tự đúc kết ra nguyên lý kỹ thuật mới."""
        logger.info("TheoryDiscoveryEngine: Đang phân tích dữ liệu thất bại để khám phá quy luật...")
        
        principles = []
        if not os.path.exists(failed_hyps_path):
            return principles

        try:
            with open(failed_hyps_path, "r", encoding="utf-8") as f:
                failed_hyps = json.load(f)

            # Phân tích tương quan lỗi (Failure Correlation Analysis)
            # Thống kê số lượng lỗi liên quan tới 'migration' hoặc 'planner'
            migration_errors = 0
            planner_errors = 0
            total_failures = len(failed_hyps)

            for item in failed_hyps:
                hypothesis = item.get("hypothesis", "").lower()
                target = item.get("target", "").lower()
                
                if "migration" in hypothesis or "database" in hypothesis:
                    migration_errors += 1
                if "planner" in target or "tool" in hypothesis:
                    planner_errors += 1

            # Quy luật 1: Phát hiện nhiều lỗi liên quan tới database migration
            if total_failures > 0 and (migration_errors / total_failures) >= 0.5:
                principles.append(EngineeringPrinciple(
                    id="RULE-DB-001",
                    symptom_pattern="database migration error",
                    context={"database": "PostgreSQL", "framework": "Django/FastAPI"},
                    derived_rule="ALWAYS check current migration history and schema delta before running sql patches.",
                    confidence=0.85
                ))
                logger.info("TheoryDiscoveryEngine: Rút ra nguyên lý RULE-DB-001 thành công.")

            # Quy luật 2: Phát hiện nhiều lỗi liên quan tới planner tool calling
            if total_failures > 0 and (planner_errors / total_failures) >= 0.5:
                principles.append(EngineeringPrinciple(
                    id="RULE-PLANNER-001",
                    symptom_pattern="planner tool selection failure",
                    context={"framework": "LangGraph", "agent": "PlannerAgent"},
                    derived_rule="ALWAYS run impact analysis via World Model before patching core modules.",
                    confidence=0.90
                ))
                logger.info("TheoryDiscoveryEngine: Rút ra nguyên lý RULE-PLANNER-001 thành công.")

        except Exception as e:
            logger.error(f"TheoryDiscoveryEngine: Lỗi khi khám phá quy luật: {str(e)}")

        return principles
