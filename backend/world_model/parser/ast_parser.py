import ast
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ASTParser:
    @staticmethod
    def parse_file(filepath: str) -> Dict[str, Any]:
        """Phân tích cú pháp AST của tệp tin Python để trích xuất cấu trúc classes, methods, imports và calls."""
        structure = {
            "filepath": filepath,
            "imports": [],
            "classes": [],
            "calls": []
        }

        if not os.path.exists(filepath):
            return structure

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                node = ast.parse(f.read(), filename=filepath)

            class_context = None

            for child in ast.walk(node):
                # 1. Trích xuất imports
                if isinstance(child, ast.Import):
                    for alias in child.names:
                        structure["imports"].append(alias.name)
                elif isinstance(child, ast.ImportFrom):
                    if child.module:
                        structure["imports"].append(child.module)

                # 2. Trích xuất classes & methods
                elif isinstance(child, ast.ClassDef):
                    class_context = child.name
                    methods = []
                    for item in child.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)
                    structure["classes"].append({
                        "name": child.name,
                        "methods": methods
                    })

                # 3. Trích xuất calls (lời gọi hàm)
                elif isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        # Lời gọi dạng: obj.func_name()
                        structure["calls"].append({
                            "func_name": child.func.attr,
                            "caller_class": class_context
                        })
                    elif isinstance(child.func, ast.Name):
                        # Lời gọi dạng: func_name()
                        structure["calls"].append({
                            "func_name": child.func.id,
                            "caller_class": class_context
                        })

        except Exception as e:
            logger.error(f"ASTParser: Lỗi khi parse file {filepath}: {str(e)}")

        return structure
