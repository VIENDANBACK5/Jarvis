import ast
from typing import List, Dict, Any, Optional


class PythonSymbolParser:
    """Sử dụng thư viện ast tiêu chuẩn của Python để phân tích chính xác các định nghĩa."""

    def parse_code(self, code: str, filepath: str = "<string>") -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(code, filename=filepath)
        except SyntaxError:
            # Nếu code lỗi cú pháp, trả về danh sách rỗng
            return []

        symbols = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "type": "class",
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "docstring": ast.get_docstring(node) or "",
                    "parent": None
                })
                # Đăng ký các hàm/phương thức con trong class
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append({
                            "name": subnode.name,
                            "type": "method",
                            "start_line": subnode.lineno,
                            "end_line": getattr(subnode, "end_lineno", subnode.lineno),
                            "docstring": ast.get_docstring(subnode) or "",
                            "parent": node.name
                        })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Chỉ lấy các hàm toàn cục (không có parent class trong walk trực tiếp)
                # Để tránh trùng lặp hàm trong class, ta lọc lại sau hoặc kiểm tra tổ tiên của node
                # Một cách đơn giản là kiểm tra xem node cha trực tiếp có phải ClassDef không.
                pass

        # Thực hiện phân tích lại bằng cách duyệt cây có cấu trúc để lấy phân cấp chuẩn xác
        symbols = []
        self._traverse(tree, None, symbols)
        return symbols

    def _traverse(self, node: ast.AST, parent_name: Optional[str], symbols: List[Dict[str, Any]]):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                symbols.append({
                    "name": child.name,
                    "type": "class",
                    "start_line": child.lineno,
                    "end_line": getattr(child, "end_lineno", child.lineno),
                    "docstring": ast.get_docstring(child) or "",
                    "parent": parent_name
                })
                self._traverse(child, child.name, symbols)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbol_type = "method" if parent_name else "function"
                symbols.append({
                    "name": child.name,
                    "type": symbol_type,
                    "start_line": child.lineno,
                    "end_line": getattr(child, "end_lineno", child.lineno),
                    "docstring": ast.get_docstring(child) or "",
                    "parent": parent_name
                })
                # Không đi sâu hơn vào trong function cơ bản để tìm nested functions (nếu không cần thiết)

    def parse_imports(self, code: str) -> List[str]:
        """Trích xuất danh sách các module được import trong file Python."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
            
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
