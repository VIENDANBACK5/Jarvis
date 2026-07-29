from typing import Any, Dict, List


class ContextSelector:
    """Lọc thông tin có liên quan cao nhất tới tác vụ hiện tại."""

    def select_relevant_facts(self, query: str, facts: List[str]) -> List[str]:
        # Ở phase này, lọc đơn giản dựa trên từ khóa chung. 
        # Sau này sẽ tích hợp với Semantic Similarity qua Embedding Service.
        query_words = set(query.lower().split())
        relevant = []
        for fact in facts:
            fact_words = set(fact.lower().split())
            if query_words.intersection(fact_words):
                relevant.append(fact)
        # Nếu không khớp từ khóa nào, trả về tất cả
        return relevant if relevant else facts
