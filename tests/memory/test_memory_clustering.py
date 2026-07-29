import pytest
from backend.memory.memory_cluster import MemoryClusterEngine


def test_memory_clustering():
    cluster_engine = MemoryClusterEngine(similarity_threshold=0.85)

    experiences = [
        {"id": "EXP-1", "text": "Fix database migration schema error", "metadata": {}},
        {"id": "EXP-2", "text": "Fix database migration schema error", "metadata": {}},
        {"id": "EXP-3", "text": "JWT token authentication issue", "metadata": {}}
    ]

    canonical_skills = cluster_engine.cluster_and_merge(experiences)

    # 2 bài test migration trùng lặp được gom thành 1 skill đại diện canonical
    assert len(canonical_skills) == 2
    assert any(c["cluster_count"] == 2 for c in canonical_skills)
