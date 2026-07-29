import pytest
from backend.memory.vector_store import VectorMemoryStore
from backend.memory.hybrid_retriever import HybridRetriever


def test_hybrid_retrieval(tmp_path):
    store = VectorMemoryStore(str(tmp_path / "vector"))
    store.add_item("EXP-1", "Fix bug in calculate_payment_v2 function", {"task": "payment"})
    store.add_item("EXP-2", "General database transaction error", {"task": "db"})

    retriever = HybridRetriever(store)
    results = retriever.retrieve("calculate_payment_v2", top_k=2)

    assert len(results) > 0
    # Exact symbol calculate_payment_v2 phải có điểm BM25 cao và được xếp top 1
    assert results[0]["id"] == "EXP-1"
    assert results[0]["bm25_score"] > 0.0
