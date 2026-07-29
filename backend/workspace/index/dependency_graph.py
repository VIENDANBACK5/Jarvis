import os
import logging
from typing import Dict, List, Set, Optional

from backend.workspace.scanner import WorkspaceScanner
from backend.workspace.parser.python import PythonSymbolParser
from backend.workspace.parser.javascript import JavaScriptSymbolParser

logger = logging.getLogger(__name__)


class DependencyGraph:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        # file_path (relative) -> Set of file_paths it imports/depends on
        self._dependencies: Dict[str, Set[str]] = {}
        # file_path (relative) -> Set of file_paths that import it (reverse dependencies)
        self._dependents: Dict[str, Set[str]] = {}

        self.py_parser = PythonSymbolParser()
        self.js_parser = JavaScriptSymbolParser()

    def build_graph(self):
        """Quét workspace và xây dựng Đồ thị Phụ thuộc giữa các file."""
        self._dependencies.clear()
        self._dependents.clear()

        scanner = WorkspaceScanner(self.base_dir)
        files = scanner.scan()
        file_paths = {f["path"] for f in files}

        for f in files:
            rel_path = f["path"]
            ext = f["extension"]
            
            if ext not in [".py", ".js", ".jsx", ".ts", ".tsx"]:
                continue
                
            full_path = os.path.join(self.base_dir, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                    code = file.read()
                
                # Trích xuất các chuỗi import thô
                raw_imports = []
                if ext == ".py":
                    raw_imports = self.py_parser.parse_imports(code)
                elif ext in [".js", ".jsx", ".ts", ".tsx"]:
                    raw_imports = self.js_parser.parse_imports(code)

                # Giải quyết các import thô thành đường dẫn file thực tế trong dự án
                resolved_deps = set()
                for imp in raw_imports:
                    resolved_path = self._resolve_import_to_path(rel_path, imp, file_paths)
                    if resolved_path:
                        resolved_deps.add(resolved_path)

                self._dependencies[rel_path] = resolved_deps

                # Cập nhật ngược đồ thị dependents
                for dep in resolved_deps:
                    if dep not in self._dependents:
                        self._dependents[dep] = set()
                    self._dependents[dep].add(rel_path)

            except Exception as e:
                logger.error(f"Lỗi khi xây dựng dependency graph cho {rel_path}: {str(e)}")

    def _resolve_import_to_path(self, current_file: str, import_str: str, file_paths: Set[str]) -> Optional[str]:
        """Giải quyết chuỗi import thô thành đường dẫn file tương đối trong dự án."""
        # 1. Trường hợp import tương đối (đặc trưng của JS/TS)
        if import_str.startswith("."):
            current_dir = os.path.dirname(current_file)
            # Chuẩn hóa đường dẫn tương đối
            target_path = os.path.normpath(os.path.join(current_dir, import_str)).replace("\\", "/")
            
            # Thử các extension khác nhau
            for ext in [".js", ".ts", ".jsx", ".tsx", ".py"]:
                test_path = target_path + ext
                if test_path in file_paths:
                    return test_path
            # Thử thư mục index file
            for ext in [".js", ".ts"]:
                test_path = f"{target_path}/index{ext}"
                if test_path in file_paths:
                    return test_path
            return None

        # 2. Trường hợp import tuyệt đối liên quan đến tên package nội bộ (ví dụ: backend.api.routes hoặc backend/main)
        # Thay thế dấu chấm bằng dấu xuyệt để chuyển đổi python import format
        normalized_imp = import_str.replace(".", "/")
        
        # Thử tìm file tương ứng trong dự án bắt đầu bằng đường dẫn import đó
        for path in file_paths:
            # Ví dụ: backend/api/routes.py bắt đầu bằng backend/api/routes
            if path.startswith(normalized_imp):
                return path

        return None

    def get_dependencies(self, file_path: str) -> Set[str]:
        """Lấy danh sách các file mà file_path phụ thuộc vào."""
        return self._dependencies.get(file_path, set())

    def get_dependents(self, file_path: str) -> Set[str]:
        """Lấy danh sách các file phụ thuộc ngược lại vào file_path."""
        return self._dependents.get(file_path, set())

    def get_all_dependencies(self) -> Dict[str, Set[str]]:
        return self._dependencies
