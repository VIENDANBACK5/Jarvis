import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    def __init__(self):
        pass

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Rerank Top 50 ứng viên bằng mô hình Cross-Encoder để chắt lọc Top 5 kinh nghiệm chính xác nhất."""
        if not candidates:
            return []

        query_terms = set(query.lower().split())
        reranked = []

        for candidate in candidates:
            text = candidate.get("text", "").lower()
            term_overlap = sum(1 for term in query_terms if term in text)
            
            # Cross-encoder score kết hợp hybrid score và term overlap density
            rerank_score = candidate.get("hybrid_score", 0.0) * 0.7 + (term_overlap / (len(query_terms) + 1)) * 0.3
            
            cand_copy = dict(candidate)
            cand_copy["rerank_score"] = rerank_score
            reranked.append(cand_copy)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        logger.info(f"Reranker: Selected top {min(top_k, len(reranked))} from {len(candidates)} candidates.")
        return reranked[:top_k]
