import uuid
import logging
from typing import Dict, List, Set, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CausalNode(BaseModel):
    id: str = Field(default_factory=lambda: f"node-{uuid.uuid4().hex[:8]}")
    node_type: str = Field(..., description="symptom | cause | evidence | action")
    name: str = Field(..., description="Tên nhận diện của node nhân quả.")
    confidence: float = Field(default=1.0, description="Độ tin cậy của node.")
    source: str = Field(..., description="rule | experience | llm | world_model")
    evidence_list: List[str] = Field(default_factory=list, description="Danh sách bằng chứng đi kèm.")


class CausalGraph:
    def __init__(self):
        self.nodes: Dict[str, CausalNode] = {}
        # adj_list: {from_node_id: {to_node_id}}
        self.adj_list: Dict[str, Set[str]] = {}

    def add_node(self, node: CausalNode):
        """Thêm một CausalNode vào đồ thị nhân quả."""
        self.nodes[node.id] = node
        if node.id not in self.adj_list:
            self.adj_list[node.id] = set()

    def add_edge(self, from_id: str, to_id: str):
        """Thêm mối liên kết nhân quả từ node này sang node kia."""
        if from_id in self.nodes and to_id in self.nodes:
            self.adj_list[from_id].add(to_id)

    def get_possible_causes(self, symptom_name: str) -> List[CausalNode]:
        """Tìm các nguyên nhân khả dĩ liên kết trực tiếp với triệu chứng lỗi chỉ định."""
        symptom_node = None
        for node in self.nodes.values():
            if node.node_type == "symptom" and node.name.lower() == symptom_name.lower():
                symptom_node = node
                break

        if not symptom_node:
            return []

        causes = []
        # Quét các node kề được liên kết từ symptom node
        for child_id in self.adj_list.get(symptom_node.id, []):
            child_node = self.nodes.get(child_id)
            if child_node and child_node.node_type == "cause":
                causes.append(child_node)
        return causes
