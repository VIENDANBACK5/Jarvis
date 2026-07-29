import pytest
from backend.autonomy.discovery.theory_discovery import EngineeringPrinciple
from backend.autonomy.discovery.principle_store import PrincipleStore
from backend.autonomy.discovery.rule_adapter import RuleAdapter
from backend.autonomy.discovery.principle_validator import PrincipleValidator


def test_positive_validation():
    validator = PrincipleValidator()
    p = EngineeringPrinciple(
        id="RULE-DB-001",
        symptom_pattern="database migration error",
        context={"database": "PostgreSQL"},
        derived_rule="ALWAYS check current migration history before running sql patches.",
        confidence=0.85,
        status="candidate"
    )

    res = validator.validate_candidate(p, [0.60], [0.72], p_value_override=0.01)
    
    assert res.status == "validated"
    assert res.validation["delta"] == 0.12
    assert res.validation["p_value"] == 0.01


def test_low_delta_reject():
    validator = PrincipleValidator()
    p = EngineeringPrinciple(
        id="RULE-DB-001",
        symptom_pattern="database migration error",
        context={"database": "PostgreSQL"},
        derived_rule="ALWAYS check current migration history before running sql patches.",
        confidence=0.85,
        status="candidate"
    )

    res = validator.validate_candidate(p, [0.70], [0.72], p_value_override=0.01)
    
    assert res.status == "rejected"
    assert res.validation["delta"] == 0.02
    assert "insufficient improvement" in res.validation["reason"]


def test_high_variance_reject():
    validator = PrincipleValidator()
    p = EngineeringPrinciple(
        id="RULE-DB-001",
        symptom_pattern="database migration error",
        context={"database": "PostgreSQL"},
        derived_rule="ALWAYS check current migration history before running sql patches.",
        confidence=0.85,
        status="candidate"
    )

    res = validator.validate_candidate(p, [0.60], [0.72], p_value_override=0.25)
    
    assert res.status == "rejected"
    assert res.validation["p_value"] == 0.25


def test_rule_adapter_filtering(tmp_path):
    store = PrincipleStore(str(tmp_path / "storage"))
    
    p_candidate = EngineeringPrinciple(
        id="RULE-A",
        symptom_pattern="planner tool selection failure",
        context={"framework": "LangGraph"},
        derived_rule="ALWAYS run impact analysis.",
        confidence=0.90,
        status="candidate"
    )
    
    p_validated = EngineeringPrinciple(
        id="RULE-B",
        symptom_pattern="database error",
        context={"database": "Postgres"},
        derived_rule="ALWAYS check migration history.",
        confidence=0.85,
        status="validated"
    )

    store.save_principles([p_candidate, p_validated])

    adapter = RuleAdapter(store)
    prompt_str = adapter.format_rules_for_prompt()
    
    # Chỉ chèn RULE-B (validated), không chèn RULE-A (candidate)
    assert "RULE-B" in prompt_str
    assert "RULE-A" not in prompt_str
