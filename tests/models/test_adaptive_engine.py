import pytest
from backend.models.adaptive_engine import AdaptiveThinkingEngine


def test_adaptive_thinking_engine_eval():
    engine = AdaptiveThinkingEngine()

    # Simple task
    model, budget, temp = engine.select_model_and_budget("Format code print output")
    assert model == "gpt-4o-mini"
    assert budget == 3

    # Complex task with deadlocks
    model_c, budget_c, temp_c = engine.select_model_and_budget("Fix database deadlock race condition and authentication")
    assert model_c == "claude-3-5-sonnet"
    assert budget_c == 10
