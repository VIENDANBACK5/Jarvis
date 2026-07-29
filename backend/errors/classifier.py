import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ErrorClassifier:
    @staticmethod
    def classify_error(stderr: str, stdout: str) -> Dict[str, Any]:
        """Phân loại lỗi dựa trên stdout/stderr và đề xuất chiến lược sửa lỗi (Repair Strategy)."""
        combined_output = f"{stderr}\n{stdout}"
        
        # 1. Kiểm tra lỗi thiếu thư viện / Dependency
        if "ModuleNotFoundError" in combined_output or "ImportError" in combined_output or "No module named" in combined_output:
            # Trích xuất tên module bị thiếu bằng regex
            match = re.search(r"(?:No module named|ModuleNotFoundError: No module named)\s+['\"]?([\w\.\-]+)['\"]?", combined_output)
            missing_module = match.group(1) if match else "unknown"
            
            return {
                "category": "DEPENDENCY_ERROR",
                "root_cause": f"Thiếu thư viện dependency: {missing_module}",
                "repair_strategy": "INSTALL_PACKAGE",
                "target_package": missing_module
            }

        # 2. Kiểm tra lỗi cú pháp (Syntax Error)
        if "SyntaxError" in combined_output or "IndentationError" in combined_output or "TabError" in combined_output:
            # Trích xuất dòng và nguyên nhân lỗi cú pháp
            match = re.search(r"File\s+['\"].*?['\"]\s*,\s*line\s+(\d+)", combined_output)
            line = match.group(1) if match else "unknown"
            
            return {
                "category": "SYNTAX_ERROR",
                "root_cause": f"Lỗi cú pháp tại dòng: {line}",
                "repair_strategy": "FIX_SYNTAX",
                "error_line": line
            }

        # 3. Kiểm tra lỗi logic kiểm thử (Assertion / Test Failure)
        if "AssertionError" in combined_output or "FAILED tests/" in combined_output or "FAIL:" in combined_output:
            return {
                "category": "LOGIC_ERROR",
                "root_cause": "Kiểm thử (Assertion) thất bại do sai logic nghiệp vụ hoặc sai kỳ vọng kiểm thử.",
                "repair_strategy": "MODIFY_LOGIC"
            }

        # 4. Kiểm tra lỗi Timeout
        if "timeout" in combined_output.lower() or "quá giới hạn thời gian" in combined_output.lower():
            return {
                "category": "TIMEOUT_ERROR",
                "root_cause": "Thực thi câu lệnh bị treo hoặc vượt quá thời gian tối đa cho phép.",
                "repair_strategy": "OPTIMIZE_PERFORMANCE_OR_INCREASE_TIMEOUT"
            }

        # 5. Các trường hợp lỗi runtime khác
        return {
            "category": "RUNTIME_ERROR",
            "root_cause": "Lỗi Runtime không xác định cụ thể trong test suite.",
            "repair_strategy": "REFACTOR_CODE"
        }
