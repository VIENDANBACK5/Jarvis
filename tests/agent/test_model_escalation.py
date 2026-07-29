import pytest
from backend.models.adaptive_engine import AdaptiveThinkingEngine, ComplexityVector


def test_model_escalation_scenarios():
    engine = AdaptiveThinkingEngine()

    # Case 1: Small bug fix -> fast mode
    v1 = ComplexityVector(files_changed=1, failing_tests=0)
    config1 = engine.evaluate_vector(v1)
    assert config1.mode == "fast"
    assert config1.roles["planner"] == "gpt-4o-mini"

    # Case 2: High tests failing -> advanced or deep mode escalation
    v2 = ComplexityVector(files_changed=2, failing_tests=3)
    config2 = engine.evaluate_vector(v2)
    assert config2.mode in ["advanced", "deep"]

    # Case 3: High files changed + architectural risk -> deep thinking mode escalation
    v3 = ComplexityVector(files_changed=10, architectural_risk=True)
    config3 = engine.evaluate_vector(v3)
    assert config3.mode == "deep"
    assert config3.roles["planner"] == "claude-3-5-sonnet"
