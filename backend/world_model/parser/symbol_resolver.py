import ast
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SymbolResolver:
    def __init__(self):
        self.symbol_table: Dict[str, str] = {}

    def build_symbol_table(self, code: str):
        """Duyệt mã nguồn để phân tích và gán kiểu (types/classes) cho các biến."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Tìm gán dạng: var = ClassName()
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                        class_name = node.value.func.id
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                self.symbol_table[target.id] = class_name
        except Exception as e:
            logger.error(f"SymbolResolver: Lỗi khi dựng symbol table: {str(e)}")

    def resolve_type(self, var_name: str) -> Optional[str]:
        """Trả về kiểu/Class của biến nếu tìm thấy trong symbol table."""
        return self.symbol_table.get(var_name)

    def resolve_call(self, var_name: str, method_name: str) -> str:
        """Phân giải lời gọi hàm động thành class method định danh đầy đủ."""
        resolved_type = self.resolve_type(var_name)
        if resolved_type:
            return f"{resolved_type}.{method_name}"
        return f"Unknown.{method_name}"
