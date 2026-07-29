import logging
from typing import List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DiagnosticExperiment(BaseModel):
    hypothesis: str = Field(..., description="Tên giả thuyết cần kiểm chứng.")
    evidence_needed: List[str] = Field(..., description="Bằng chứng cần thu hoạch.")
    experiment_actions: List[str] = Field(..., description="Hành động thực nghiệm chẩn đoán nhanh.")
    success_condition: str = Field(..., description="Điều kiện chứng minh giả thuyết đúng.")


class DiagnosticExperimentGenerator:
    def __init__(self):
        pass

    def generate_experiment(self, hypothesis_name: str) -> DiagnosticExperiment:
        """Thiết kế phép thử chẩn đoán định lượng dựa trên giả thuyết chẩn đoán."""
        hyp_lower = hypothesis_name.lower()
        
        if "database" in hyp_lower or "migration" in hyp_lower:
            return DiagnosticExperiment(
                hypothesis=hypothesis_name,
                evidence_needed=["migration version", "schema diff"],
                experiment_actions=["scan migrations", "compare database schema"],
                success_condition="difference detected"
            )
        elif "syntax" in hyp_lower or "code" in hyp_lower:
            return DiagnosticExperiment(
                hypothesis=hypothesis_name,
                evidence_needed=["compilation status", "syntax warning"],
                experiment_actions=["run syntax check", "check type lint"],
                success_condition="syntax warning found"
            )
        else:
            return DiagnosticExperiment(
                hypothesis=hypothesis_name,
                evidence_needed=["dependency status", "pip list"],
                experiment_actions=["pip check", "verify package import"],
                success_condition="missing module found"
            )
