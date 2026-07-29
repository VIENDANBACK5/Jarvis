import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class StacktraceParser:
    @staticmethod
    def parse_stacktrace(stacktrace: str) -> Dict[str, Any]:
        """Phân tích stacktrace log lỗi để bóc tách file, dòng lỗi và nội dung lỗi chính."""
        result = {
            "filepath": None,
            "line_number": None,
            "error_message": "Unknown error"
        }

        if not stacktrace:
            return result

        # 1. Tìm lỗi dòng cuối cùng (error message)
        lines = [line.strip() for line in stacktrace.splitlines() if line.strip()]
        if lines:
            result["error_message"] = lines[-1]

        # 2. Quét tìm dòng code bị lỗi gần nhất (thường có dạng: File "xyz.py", line 42)
        # Quét ngược từ dưới lên để tìm vị trí lỗi gần nhất
        for line in reversed(lines):
            match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+)', line)
            if match:
                result["filepath"] = match.group(1).replace("\\", "/")
                result["line_number"] = int(match.group(2))
                break

        logger.info(f"StacktraceParser: Parsed file={result['filepath']} | line={result['line_number']} | error={result['error_message']}")
        return result
