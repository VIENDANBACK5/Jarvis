import difflib
from typing import List


class DiffAnalyzer:
    @staticmethod
    def get_unified_diff(original_code: str, modified_code: str, filename: str = "file") -> str:
        """Sinh ra chuỗi Unified Diff trực quan so sánh mã nguồn cũ và mới."""
        orig_lines = original_code.splitlines(keepends=True)
        mod_lines = modified_code.splitlines(keepends=True)

        diff = difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        )
        return "".join(diff)
