import math
import logging
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    def __init__(self, dim: int = 64):
        self.dim = dim

    def _hash_text_to_vector(self, text: str) -> List[float]:
        """Tạo vector mật độ cao deterministic hỗ trợ cụm ngữ nghĩa semantic clusters."""
        vec = [0.0] * self.dim
        words = text.lower().replace("_", " ").replace("-", " ").split()
        if not words:
            return vec

        # Nhóm ngữ nghĩa đặc trưng (Semantic clusters)
        semantic_map = {
            "auth": 0, "jwt": 0, "session": 0, "token": 0, "credential": 0, "timeout": 0, "expired": 0, "login": 0,
            "db": 1, "database": 1, "postgres": 1, "postgresql": 1, "sql": 1, "connection": 1, "pool": 1, "migration": 1,
            "payment": 2, "stripe": 2, "billing": 2, "charge": 2, "card": 2, "calculate": 2
        }

        for idx, word in enumerate(words):
            # 1. Semantic Cluster Projection
            if word in semantic_map:
                group = semantic_map[word]
                start_idx = group * 10
                for i in range(10):
                    vec[(start_idx + i) % self.dim] += 2.0

            # 2. Trigram hashing
            for i in range(len(word) - 2):
                tri = word[i:i+3]
                val = sum(ord(c) for c in tri)
                pos = val % self.dim
                vec[pos] += 1.0

        # Chuẩn hóa vector L2
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        return vec

    def embed_text(self, text: str) -> List[float]:
        """Chuyển đổi văn bản thành Vector Embedding mật độ cao."""
        return self._hash_text_to_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Chuyển đổi danh sách văn bản thành danh sách Vector Embeddings."""
        return [self.embed_text(t) for t in texts]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Tính toán Cosine Similarity giữa 2 vectors."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a < 1e-9 or norm_b < 1e-9:
            return 0.0
        return dot / (norm_a * norm_b)
