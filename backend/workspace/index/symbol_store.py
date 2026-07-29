import os
import logging
from typing import Dict, List, Any, Optional

from backend.workspace.scanner import WorkspaceScanner
from backend.workspace.parser.python import PythonSymbolParser
from backend.workspace.parser.javascript import JavaScriptSymbolParser

logger = logging.getLogger(__name__)


class SymbolStore:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        # Lưu trữ symbols dạng: {rel_path: [symbols_list]}
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self.py_parser = PythonSymbolParser()
        self.js_parser = JavaScriptSymbolParser()

    def index_workspace(self):
        """Quét và lập chỉ mục toàn bộ các file trong workspace."""
        logger.info(f"Đang tiến hành chỉ mục hóa codebase tại: {self.base_dir}")
        scanner = WorkspaceScanner(self.base_dir)
        files = scanner.scan()

        for f in files:
            rel_path = f["path"]
            ext = f["extension"]
            
            if ext not in [".py", ".js", ".jsx", ".ts", ".tsx"]:
                continue
                
            full_path = os.path.join(self.base_dir, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                    code = file.read()
                self._index_file_content(rel_path, ext, code)
            except Exception as e:
                logger.error(f"Lỗi khi chỉ mục file {rel_path}: {str(e)}")

        logger.info(f"Lập chỉ mục hoàn tất. Đã lập chỉ mục {len(self._store)} files.")

    def _index_file_content(self, rel_path: str, extension: str, code: str):
        if extension == ".py":
            symbols = self.py_parser.parse_code(code, filepath=rel_path)
        elif extension in [".js", ".jsx", ".ts", ".tsx"]:
            symbols = self.js_parser.parse_code(code)
        else:
            symbols = []

        # Lưu thêm thông tin về filepath vào từng symbol để dễ định tuyến
        for s in symbols:
            s["filepath"] = rel_path

        self._store[rel_path] = symbols

    def update_file(self, rel_path: str, code: str):
        """Cập nhật lại chỉ mục cho một file cụ thể khi file đó thay đổi."""
        ext = os.path.splitext(rel_path)[1].lower()
        if ext in [".py", ".js", ".jsx", ".ts", ".tsx"]:
            self._index_file_content(rel_path, ext, code)
            logger.info(f"Đã cập nhật chỉ mục cho file: {rel_path}")

    def query_symbol(self, name: str) -> List[Dict[str, Any]]:
        """Tìm kiếm các định nghĩa symbol trên toàn dự án."""
        matches = []
        name_lower = name.lower()
        
        for filepath, symbols in self._store.items():
            for s in symbols:
                if s["name"].lower() == name_lower:
                    matches.append(s)
                    
        return matches

    def list_all_symbols(self) -> Dict[str, List[Dict[str, Any]]]:
        return self._store
