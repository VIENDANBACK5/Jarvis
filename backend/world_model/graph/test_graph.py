import os
import logging
from typing import Dict, List, Set

from backend.world_model.parser.ast_parser import ASTParser

logger = logging.getLogger(__name__)


class CoverageGraph:
    def __init__(self):
        # Source file -> Test files
        self.source_to_tests: Dict[str, Set[str]] = {}

    def add_test_dependency(self, source_file: str, test_file: str):
        """Khai báo test_file kiểm định cho source_file."""
        src = source_file.replace("\\", "/")
        tst = test_file.replace("\\", "/")
        
        if src not in self.source_to_tests:
            self.source_to_tests[src] = set()
        self.source_to_tests[src].add(tst)

    def build_test_graph(self, workspace_dir: str):
        """Tự động xây dựng đồ thị liên kết source file với test suite tương ứng."""
        ws_dir = os.path.abspath(workspace_dir)
        
        test_files = []
        for root, _, files in os.walk(ws_dir):
            # Chỉ tìm trong thư mục tests/ hoặc file có chứa prefix/suffix test
            if "tests" in root.replace("\\", "/").split("/"):
                for file in files:
                    if file.endswith(".py"):
                        test_files.append(os.path.join(root, file))
            else:
                for file in files:
                    if (file.startswith("test_") or file.endswith("_test.py")) and file.endswith(".py"):
                        test_files.append(os.path.join(root, file))

        for test_path in test_files:
            rel_test = os.path.relpath(test_path, ws_dir).replace("\\", "/")
            structure = ASTParser.parse_file(test_path)
            
            for imp in structure["imports"]:
                imp_parts = imp.split(".")
                potential_path = os.path.join(ws_dir, *imp_parts) + ".py"
                
                if os.path.exists(potential_path):
                    rel_src = os.path.relpath(potential_path, ws_dir).replace("\\", "/")
                    self.add_test_dependency(rel_src, rel_test)

    def get_associated_tests(self, source_file: str) -> List[str]:
        """Trả về danh sách các tệp test bao phủ tệp mã nguồn chỉ định."""
        rel_path = source_file.replace("\\", "/")
        return list(self.source_to_tests.get(rel_path, []))
