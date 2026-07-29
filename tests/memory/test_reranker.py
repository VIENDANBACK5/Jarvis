import pytest
from backend.memory.reranker import CrossEncoderReranker


def test_cross_encoder_reranker():
    reranker = CrossEncoderReranker()
    candidates = [
        {"id": "EXP-1", "text": "Generic exception handling", "hybrid_score": 0.5},
        {"id": "EXP-2", "text": "JWT token expiration in middleware auth", "hybrid_score": 0.8}
    ]

    results = reranker.rerank("JWT expiration", candidates, top_k=2)

    assert len(results) == 2
    assert results[0]["id"] == "EXP-2"
    assert results[0]["rerank_score"] > results[1]["rerank_score"]
