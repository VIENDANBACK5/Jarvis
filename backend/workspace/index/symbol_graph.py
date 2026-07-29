import os
import re
import logging
from typing import Dict, List, Any, Optional

from backend.workspace.scanner import WorkspaceScanner
from backend.workspace.parser.python import PythonSymbolParser
from backend.workspace.parser.javascript import JavaScriptSymbolParser

logger = logging.getLogger(__name__)


class SymbolGraph:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        # file_path -> list of symbols defined in it
        self._symbols_by_file: Dict[str, List[Dict[str, Any]]] = {}
        self.py_parser = PythonSymbolParser()
        self.js_parser = JavaScriptSymbolParser()

    def build_graph(self):
        """Lập chỉ mục các symbol định nghĩa trên toàn bộ workspace."""
        self._symbols_by_file.clear()
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

                symbols = []
                if ext == ".py":
                    symbols = self.py_parser.parse_code(code, filepath=rel_path)
                elif ext in [".js", ".jsx", ".ts", ".tsx"]:
                    symbols = self.js_parser.parse_code(code)

                # Bổ sung filepath tương đối vào từng symbol
                for s in symbols:
                    s["filepath"] = rel_path

                self._symbols_by_file[rel_path] = symbols
            except Exception as e:
                logger.error(f"Lỗi khi phân tích symbols cho file {rel_path}: {str(e)}")

        logger.info(f"Đã lập chỉ mục Symbol Graph cho {len(self._symbols_by_file)} files.")

    def find_definition(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Tìm định nghĩa của một symbol (Class, Function, Method) trong toàn dự án."""
        matches = []
        symbol_name_lower = symbol_name.lower()

        for filepath, symbols in self._symbols_by_file.items():
            for s in symbols:
                if s["name"].lower() == symbol_name_lower:
                    matches.append(s)

        return matches

    def find_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Tìm kiếm tất cả các vị trí tham chiếu (gọi) symbol trong toàn bộ codebase."""
        references = []
        
        # Regex tìm từ nguyên vẹn để tránh so khớp nhầm (ví dụ: 'User' khớp 'UserService')
        pattern = re.compile(rf"\b{re.escape(symbol_name)}\b")
        
        # Lấy thông tin định nghĩa để loại trừ dòng khai báo
        definitions = self.find_definition(symbol_name)
        def_locations = {(d["filepath"], d["start_line"]) for d in definitions}

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
                    lines = file.readlines()

                for idx, line in enumerate(lines, 1):
                    # Bỏ qua dòng comment thô sơ để giảm thiểu nhiễu
                    trimmed = line.strip()
                    if trimmed.startswith("#") or trimmed.startswith("//") or trimmed.startswith("*"):
                        continue

                    if pattern.search(line):
                        # Loại trừ nếu dòng này chính là dòng định nghĩa symbol
                        if (rel_path, idx) in def_locations:
                            continue

                        references.append({
                            "filepath": rel_path,
                            "line_number": idx,
                            "line_content": trimmed
                        })
            except Exception as e:
                logger.error(f"Lỗi khi tìm tham chiếu trong file {rel_path}: {str(e)}")

        return references
