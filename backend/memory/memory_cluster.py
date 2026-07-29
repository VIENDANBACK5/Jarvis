import logging
from typing import List, Dict, Any

from backend.memory.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class MemoryClusterEngine:
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.engine = EmbeddingEngine()

    def cluster_and_merge(self, experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cụm nhóm các trajectory tương đồng thành Canonical Skill, loại bỏ trùng lặp tri thức rác."""
        if not experiences:
            return []

        clusters: List[List[Dict[str, Any]]] = []

        for exp in experiences:
            text = exp.get("text", "")
            vec = self.engine.embed_text(text)
            
            merged = False
            for cluster in clusters:
                rep_vec = self.engine.embed_text(cluster[0].get("text", ""))
                sim = EmbeddingEngine.cosine_similarity(vec, rep_vec)
                if sim >= self.threshold:
                    cluster.append(exp)
                    merged = True
                    break

            if not merged:
                clusters.append([exp])

        canonical_skills = []
        for cluster in clusters:
            rep = cluster[0]
            canonical_skills.append({
                "canonical_id": f"CANONICAL-{rep.get('id', 'SKILL')}",
                "text": rep.get("text", ""),
                "cluster_count": len(cluster),
                "metadata": rep.get("metadata", {})
            })

        logger.info(f"MemoryClusterEngine: Clustered {len(experiences)} experiences into {len(canonical_skills)} canonical skills.")
        return canonical_skills
