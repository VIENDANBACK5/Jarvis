import os
import logging
from typing import Dict, List, Set, Tuple

from backend.world_model.parser.ast_parser import ASTParser

logger = logging.getLogger(__name__)


class DependencyGraph:
    def __init__(self):
        # Lưu các cạnh quan hệ: {source_file: [(target_file, rel_type)]}
        self.adj_list: Dict[str, Set[Tuple[str, str]]] = {}
        # Đồ thị đảo phục vụ tra ngược: {target_file: [(source_file, rel_type)]}
        self.rev_adj_list: Dict[str, Set[Tuple[str, str]]] = {}

    def add_dependency(self, source: str, target: str, rel_type: str = "IMPORT"):
        """Thêm một cạnh quan hệ phụ thuộc vào đồ thị."""
        # Chuẩn hóa đường dẫn
        src = source.replace("\\", "/")
        tgt = target.replace("\\", "/")
        
        if src not in self.adj_list:
            self.adj_list[src] = set()
        self.adj_list[src].add((tgt, rel_type))
        
        if tgt not in self.rev_adj_list:
            self.rev_adj_list[tgt] = set()
        self.rev_adj_list[tgt].add((src, rel_type))

    def build_graph(self, workspace_dir: str):
        """Duyệt workspace để phân tích AST và tự động dựng dependency graph."""
        ws_dir = os.path.abspath(workspace_dir)
        
        # Quét toàn bộ file Python
        python_files = []
        for root, _, files in os.walk(ws_dir):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        for filepath in python_files:
            rel_src = os.path.relpath(filepath, ws_dir).replace("\\", "/")
            structure = ASTParser.parse_file(filepath)
            
            for imp in structure["imports"]:
                # Tìm xem có file nào trong workspace tương ứng với module import không
                imp_parts = imp.split(".")
                potential_path = os.path.join(ws_dir, *imp_parts) + ".py"
                potential_init = os.path.join(ws_dir, *imp_parts, "__init__.py")
                
                if os.path.exists(potential_path):
                    rel_tgt = os.path.relpath(potential_path, ws_dir).replace("\\", "/")
                    self.add_dependency(rel_src, rel_tgt, "IMPORT")
                elif os.path.exists(potential_init):
                    rel_tgt = os.path.relpath(potential_init, ws_dir).replace("\\", "/")
                    self.add_dependency(rel_src, rel_tgt, "IMPORT")

    def get_dependent_files(self, filepath: str) -> List[str]:
        """Trả về danh sách các tệp tin import/phụ thuộc vào tệp tin chỉ định (tra cứu ngược)."""
        rel_path = filepath.replace("\\", "/")
        dependents = []
        if rel_path in self.rev_adj_list:
            for src, rel_type in self.rev_adj_list[rel_path]:
                dependents.append(src)
        return list(set(dependents))
