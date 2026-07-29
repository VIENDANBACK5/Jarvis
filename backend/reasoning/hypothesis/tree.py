import uuid
from typing import List, Dict, Any


class HypothesisNode:
    def __init__(self, name: str, probability: float = 0.33):
        self.id = f"hyp-{uuid.uuid4().hex[:8]}"
        self.name = name
        self.probability = probability
        self.evidence_matched: List[str] = []


class HypothesisTree:
    def __init__(self):
        self.hypotheses: List[HypothesisNode] = []

    def add_hypothesis(self, name: str, probability: float = 0.33):
        """Thêm một giả thuyết chẩn đoán lỗi vào cây chẩn đoán."""
        node = HypothesisNode(name, probability)
        self.hypotheses.append(node)

    def rank_hypotheses(self) -> List[HypothesisNode]:
        """Sắp xếp các giả thuyết chẩn đoán theo xác suất từ cao xuống thấp."""
        self.hypotheses.sort(key=lambda x: x.probability, reverse=True)
        return self.hypotheses
