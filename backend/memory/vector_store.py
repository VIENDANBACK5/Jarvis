import os
import json
import logging
from typing import List, Dict, Any

from backend.memory.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class VectorMemoryStore:
    def __init__(self, storage_dir: str = "."):
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.store_file = os.path.join(self.storage_dir, "vector_memory.json")
        self.embedding_engine = EmbeddingEngine()
        self.items: List[Dict[str, Any]] = self._load_store()

    def _load_store(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.store_file):
            return []
        try:
            with open(self.store_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"VectorMemoryStore: Lỗi đọc chỉ mục vector: {str(e)}")
            return []

    def save(self):
        """Lưu đĩa cứng chỉ mục vector."""
        try:
            with open(self.store_file, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2)
        except Exception as e:
            logger.error(f"VectorMemoryStore: Lỗi ghi chỉ mục vector: {str(e)}")

    def add_item(self, item_id: str, text: str, metadata: Dict[str, Any] = None):
        """Thêm một kinh nghiệm/kỹ năng vào Vector Store."""
        vec = self.embedding_engine.embed_text(text)
        item = {
            "id": item_id,
            "text": text,
            "vector": vec,
            "metadata": metadata or {}
        }
        self.items.append(item)
        self.save()

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Truy vấn Top-K phần tử tương đồng nhất theo Vector Cosine Similarity."""
        query_vec = self.embedding_engine.embed_text(query)
        scored_items = []
        
        for item in self.items:
            sim = EmbeddingEngine.cosine_similarity(query_vec, item["vector"])
            scored_items.append({
                "id": item["id"],
                "text": item["text"],
                "similarity": sim,
                "metadata": item["metadata"]
            })

        scored_items.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_items[:top_k]
