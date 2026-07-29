import pytest
from backend.memory.memory_consolidator import MemoryConsolidator


def test_memory_recency_decay():
    consolidator = MemoryConsolidator(decay_rate=0.05)

    experiences = [
        {"id": "EXP-NEW", "reward": 0.9, "success_rate": 1.0, "age_days": 1.0},
        {"id": "EXP-OLD", "reward": 0.9, "success_rate": 1.0, "age_days": 100.0}
    ]

    consolidated = consolidator.consolidate(experiences, score_threshold=0.30)

    # Tri thức mới được giữ lại, tri thức quá cũ (100 ngày) bị đào thải do score < 0.30
    assert len(consolidated) == 1
    assert consolidated[0]["id"] == "EXP-NEW"
