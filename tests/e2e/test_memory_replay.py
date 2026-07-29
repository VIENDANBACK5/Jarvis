import pytest
from backend.memory.vector_store import VectorMemoryStore
from backend.memory.hybrid_retriever import HybridRetriever
from backend.memory.memory_ranker import MemoryRanker


def test_memory_replay_integration(tmp_path):
    store = VectorMemoryStore(str(tmp_path / "vector"))
    store.add_item("EXP-1", "Fixed auth timeout by refreshing JWT tokens in middleware", {"task": "auth"})
    store.add_item("EXP-2", "Fixed postgres migration schema error by updating models", {"task": "db"})

    retriever = HybridRetriever(store)
    ranker = MemoryRanker(retriever)

    memories = ranker.get_top_experiences("User session token expired authentication failure", final_k=1)

    assert len(memories) == 1
    assert memories[0]["id"] == "EXP-1"
