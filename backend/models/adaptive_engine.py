import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ComplexityVector(BaseModel):
    files_changed: int = 0
    dependency_graph_depth: int = 0
    failing_tests: int = 0
    uncertainty: float = 0.0
    architectural_risk: bool = False


class ThinkingBudget(BaseModel):
    tokens: int = 4000
    max_steps: int = 3
    reflection_rounds: int = 1
    allowed_tools: List[str] = Field(default_factory=lambda: ["search", "read_file", "edit_file"])


class AdaptiveThinkingConfig(BaseModel):
    mode: str = "fast"
    roles: Dict[str, str] = Field(default_factory=dict)
    budget: ThinkingBudget = Field(default_factory=ThinkingBudget)
    reasons: List[str] = Field(default_factory=list)


class AdaptiveThinkingEngine:
    """Động cơ Phân tích Độ phức tạp Đa chiều (Complexity Vector) và Phân bổ Ngân sách (Dynamic Thinking Budget)."""

    def __init__(self, mode: str = "adaptive"):
        self.mode = mode

    def evaluate_vector(self, vector: ComplexityVector) -> AdaptiveThinkingConfig:
        """Đánh giá ComplexityVector và đưa ra cấu hình phân vai LLM & Thinking Budget thích ứng."""
        reasons = []
        
        # 1. Tính toán độ phức tạp dựa trên Complexity Vector
        score = 2.0
        
        if vector.files_changed > 5:
            score += 3.5
            reasons.append("high file change scope")
            
        if vector.dependency_graph_depth > 3:
            score += 2.0
            reasons.append("cross-module dependency depth")
            
        if vector.failing_tests > 2:
            score += 3.0
            reasons.append("multiple test failures")
            
        if vector.architectural_risk:
            score += 4.0
            reasons.append("architectural modifications required")
            
        logger.info(f"AdaptiveThinkingEngine: Complexity vector score: {score:.2f} | Reasons: {reasons}")

        # 2. Quyết định phân vai LLM theo chiến lược Cloud Brain của người dùng
        config = AdaptiveThinkingConfig()
        config.reasons = reasons

        if score < 4.0:
            config.mode = "fast"
            config.roles = {
                "requirement_analyzer": "gpt-4o-mini",
                "planner": "gpt-4o-mini",  # Task nhỏ -> GPT mini
                "coder": "gpt-4o-mini",
                "critic": "gpt-4o-mini",
                "long_doc_reader": "gemini-1.5-pro"
            }
            config.budget = ThinkingBudget(
                tokens=4000,
                max_steps=3,
                reflection_rounds=1,
                allowed_tools=["search", "read_file", "edit_file"]
            )
        elif score < 7.5:
            config.mode = "advanced"
            config.roles = {
                "requirement_analyzer": "gpt-4o",  # Hiểu yêu cầu -> GPT
                "planner": "claude-3-5-sonnet",     # Thiết kế kiến trúc -> Claude
                "coder": "gpt-4o",                 # Code gen -> GPT/Claude
                "critic": "claude-3-5-sonnet",      # Review -> Claude
                "long_doc_reader": "gemini-1.5-pro" # Tài liệu dài -> Gemini
            }
            config.budget = ThinkingBudget(
                tokens=16000,
                max_steps=6,
                reflection_rounds=2,
                allowed_tools=["search", "read_file", "edit_file", "pytest"]
            )
        else:
            config.mode = "deep"
            config.roles = {
                "requirement_analyzer": "gpt-4o",
                "planner": "claude-3-5-sonnet",
                "coder": "claude-3-5-sonnet",
                "critic": "claude-3-5-sonnet",
                "long_doc_reader": "gemini-1.5-pro"
            }
            config.budget = ThinkingBudget(
                tokens=32000,
                max_steps=10,
                reflection_rounds=3,
                allowed_tools=["search", "read_file", "edit_file", "pytest", "git_diff"]
            )

        return config

    def select_model_and_budget(self, task_goal: str, test_failure_count: int = 0):
        """Wrapper tương thích ngược để chọn mô hình và budget từ chuỗi mục tiêu task."""
        vector = ComplexityVector(
            files_changed=1,
            dependency_graph_depth=4 if "deadlock" in task_goal.lower() else 1,
            failing_tests=test_failure_count,
            architectural_risk="deadlock" in task_goal.lower() or "timeout" in task_goal.lower()
        )
        config = self.evaluate_vector(vector)
        return config.roles.get("planner", "qwen2.5-coder:7b"), config.budget.max_steps, 0.2
