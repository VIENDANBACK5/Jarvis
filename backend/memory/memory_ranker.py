import logging
from typing import List, Dict, Any

from backend.memory.hybrid_retriever import HybridRetriever
from backend.memory.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


class MemoryRanker:
    def __init__(self, hybrid_retriever: HybridRetriever, reranker: CrossEncoderReranker = None):
        self.retriever = hybrid_retriever
        self.reranker = reranker or CrossEncoderReranker()

    def get_top_experiences(self, query: str, final_k: int = 5) -> List[Dict[str, Any]]:
        """Lấy danh sách kinh nghiệm tối ưu nhất thông qua truy vấn lai và Cross-Encoder Reranking."""
        candidates = self.retriever.retrieve(query, top_k=50)
        final_memory = self.reranker.rerank(query, candidates, top_k=final_k)
        return final_memory
