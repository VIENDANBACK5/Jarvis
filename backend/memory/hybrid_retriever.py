import logging
from typing import List, Dict, Any

from backend.memory.vector_store import VectorMemoryStore

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(self, vector_store: VectorMemoryStore):
        self.vector_store = vector_store

    def _bm25_score(self, query: str, text: str) -> float:
        """Tính điểm từ khóa BM25 cho exact symbol/identifier matching."""
        query_clean = query.lower().replace("_", " ").replace("-", " ")
        text_clean = text.lower().replace("_", " ").replace("-", " ")
        
        query_words = set(query_clean.split())
        text_words = set(text_clean.split())
        if not query_words or not text_words:
            return 0.0

        matches = sum(1 for word in query_words if word in text_words)
        return matches / len(query_words)

    def retrieve(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Truy xuất lai (Hybrid Search) kết hợp exact keyword match BM25 và Dense Vector search."""
        vector_results = self.vector_store.search_similar(query, top_k=top_k)
        
        candidates = []
        for item in vector_results:
            bm25 = self._bm25_score(query, item["text"])
            vector_sim = item["similarity"]
            # Trọng số kết hợp: 0.4 BM25 + 0.6 Dense Vector
            hybrid_score = 0.4 * bm25 + 0.6 * vector_sim

            candidates.append({
                "id": item["id"],
                "text": item["text"],
                "bm25_score": bm25,
                "vector_score": vector_sim,
                "hybrid_score": hybrid_score,
                "metadata": item["metadata"]
            })

        candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return candidates[:top_k]
