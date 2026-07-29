import os
import logging
from typing import Dict, List, Set, Any

from backend.workspace.index.dependency_graph import DependencyGraph
from backend.workspace.index.symbol_graph import SymbolGraph

logger = logging.getLogger(__name__)


class ImpactAnalyzer:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self.dep_graph = DependencyGraph(self.base_dir)
        self.symbol_graph = SymbolGraph(self.base_dir)

    def initialize(self):
        """Khởi tạo và xây dựng các đồ thị phụ thuộc và symbol."""
        self.dep_graph.build_graph()
        self.symbol_graph.build_graph()

    def analyze_impact(self, file_path: str) -> Dict[str, Any]:
        """Phân tích mức độ ảnh hưởng (Impact Analysis) khi sửa đổi một file.
        
        Trả về các file bị ảnh hưởng trực tiếp, gián tiếp, các symbol và các bài test liên quan.
        """
        # Chuẩn hóa đường dẫn tương đối
        rel_path = os.path.relpath(os.path.join(self.base_dir, file_path), self.base_dir).replace("\\", "/")

        # 1. Các file bị ảnh hưởng trực tiếp (dependents trực tiếp)
        direct_dependents = self.dep_graph.get_dependents(rel_path)

        # 2. Các file bị ảnh hưởng gián tiếp (quét đệ quy tìm kiếm transitive dependents)
        all_dependents = set()
        queue = list(direct_dependents)
        while queue:
            current = queue.pop(0)
            if current not in all_dependents:
                all_dependents.add(current)
                # Lấy các file depend vào current
                for dep in self.dep_graph.get_dependents(current):
                    if dep != rel_path:
                        queue.append(dep)

        indirect_dependents = all_dependents - direct_dependents

        # 3. Phân tách các file test bị ảnh hưởng
        affected_tests = set()
        normal_files = set()
        
        for dep in all_dependents:
            if "test_" in os.path.basename(dep) or dep.startswith("tests/"):
                affected_tests.add(dep)
            else:
                normal_files.append(dep) if isinstance(normal_files, list) else normal_files.add(dep)

        # 4. Trích xuất danh sách các symbol bị ảnh hưởng trong các file thường
        affected_symbols = []
        for file in (direct_dependents | indirect_dependents):
            symbols = self.symbol_graph._symbols_by_file.get(file, [])
            for s in symbols:
                affected_symbols.append({
                    "name": s["name"],
                    "type": s["type"],
                    "filepath": file
                })

        return {
            "target_file": rel_path,
            "direct_dependents": list(direct_dependents),
            "indirect_dependents": list(indirect_dependents),
            "affected_symbols": affected_symbols,
            "affected_tests": list(affected_tests)
        }
