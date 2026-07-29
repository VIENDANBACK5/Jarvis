import os
import json
import pytest

from backend.autonomy.discovery.theory_discovery import TheoryDiscoveryEngine, EngineeringPrinciple
from backend.autonomy.discovery.principle_store import PrincipleStore
from backend.autonomy.discovery.rule_adapter import RuleAdapter


def test_theory_discovery_engine(tmp_path):
    failed_hyp_file = tmp_path / "failed_hypothesis.json"
    
    # Giả lập lịch sử 3 lần lỗi, trong đó 2 lần (>= 50%) liên quan tới database migration
    failed_data = [
        {
            "hypothesis": "Database schema mismatch during upgrade",
            "delta": -0.05,
            "target": "backend/models/user.py"
        },
        {
            "hypothesis": "Database migration mismatched version issue",
            "delta": -0.02,
            "target": "backend/models/payment.py"
        },
        {
            "hypothesis": "Wrong api signature calling",
            "delta": 0.01,
            "target": "backend/api/auth.py"
        }
    ]
    with open(failed_hyp_file, "w", encoding="utf-8") as f:
        json.dump(failed_data, f)

    engine = TheoryDiscoveryEngine()
    principles = engine.discover_principles(str(failed_hyp_file))
    
    # Phải rút ra quy luật lỗi migration database
    assert len(principles) == 1
    assert principles[0].id == "RULE-DB-001"
    assert "ALWAYS check current migration history" in principles[0].derived_rule


def test_principle_store_and_adapter(tmp_path):
    store = PrincipleStore(str(tmp_path / "storage"))
    
    p = EngineeringPrinciple(
        id="RULE-PLANNER-001",
        symptom_pattern="planner tool selection failure",
        context={"framework": "LangGraph"},
        derived_rule="ALWAYS run impact analysis via World Model before patching core modules.",
        confidence=0.90,
        status="validated"
    )
    
    # 1. Lưu nguyên lý
    store.save_principles([p])
    
    # 2. Nạp nguyên lý
    loaded = store.load_principles()
    assert len(loaded) == 1
    assert loaded[0].id == "RULE-PLANNER-001"
    assert loaded[0].confidence == 0.90

    # 3. Tích hợp RuleAdapter chèn prompt
    adapter = RuleAdapter(store)
    prompt_str = adapter.format_rules_for_prompt()
    
    assert "RULE-PLANNER-001" in prompt_str
    assert "ALWAYS run impact analysis via World Model" in prompt_str
    assert "90.0%" in prompt_str
