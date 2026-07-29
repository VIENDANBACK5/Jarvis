import pytest
from backend.memory.vector_store import VectorMemoryStore


def test_vector_retrieval_semantic_matching(tmp_path):
    store = VectorMemoryStore(str(tmp_path / "vector"))

    # Thêm 2 kinh nghiệm mẫu
    store.add_item("EXP-1", "JWT token expired during session authentication window", {"task": "auth"})
    store.add_item("EXP-2", "PostgreSQL database connection pool exhausted", {"task": "db"})

    # Query đồng nghĩa không dùng trùng từ khóa nguyên bản
    results = store.search_similar("User session credential timeout", top_k=2)

    assert len(results) > 0
    assert results[0]["id"] == "EXP-1"
    assert results[0]["similarity"] > 0.0
