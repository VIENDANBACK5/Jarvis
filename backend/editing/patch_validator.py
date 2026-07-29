import ast
import logging
from typing import Tuple, Optional

from backend.editing.patch_applier import PatchApplier

logger = logging.getLogger(__name__)


class PatchValidator:
    @staticmethod
    def validate_patch(
        original_code: str,
        patch_str: str,
        filename: str = "<string>"
    ) -> Tuple[bool, Optional[str]]:
        """Kiểm chứng độ an toàn của bản vá (Dry-run và cú pháp).
        
        Trả về: (is_valid, error_message)
        """
        # 1. Thử nghiệm áp dụng patch (Dry run)
        success, patched_code, err = PatchApplier.apply_patch(original_code, patch_str)
        if not success:
            return False, f"Lỗi xung đột bản vá: {err}"

        # 2. Kiểm tra cú pháp đối với file Python
        if filename.endswith(".py"):
            try:
                ast.parse(patched_code, filename=filename)
            except SyntaxError as se:
                return False, f"Bản vá gây lỗi cú pháp Python tại dòng {se.lineno}: {se.msg}"
            except Exception as e:
                return False, f"Lỗi không xác định khi parse AST: {str(e)}"

        # 3. Kiểm tra cú pháp thô đối với JavaScript/TypeScript
        elif filename.endswith((".js", ".jsx", ".ts", ".tsx")):
            # Kiểm tra xem có đóng/mở ngoặc cân bằng cơ bản không để tránh hư hỏng nặng
            open_braces = patched_code.count("{")
            close_braces = patched_code.count("}")
            if open_braces != close_braces:
                return False, f"Bản vá gây mất cân bằng ngoặc nhọn (Mở: {open_braces}, Đóng: {close_braces})"

        return True, None
