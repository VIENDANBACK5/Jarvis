import pytest
from backend.models.adaptive_engine import AdaptiveThinkingEngine, ComplexityVector


def test_reasoning_budget_allocation():
    engine = AdaptiveThinkingEngine()

    # Budget for simple tasks
    v_simple = ComplexityVector(files_changed=1, failing_tests=0)
    config_s = engine.evaluate_vector(v_simple)
    assert config_s.budget.tokens == 4000
    assert config_s.budget.max_steps == 3
    assert "search" in config_s.budget.allowed_tools

    # Budget for complex tasks (deep thinking)
    v_complex = ComplexityVector(files_changed=12, architectural_risk=True)
    config_c = engine.evaluate_vector(v_complex)
    assert config_c.budget.tokens == 32000
    assert config_c.budget.max_steps == 10
    assert "git_diff" in config_c.budget.allowed_tools
