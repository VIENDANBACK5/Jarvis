import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class PatchApplier:
    @staticmethod
    def apply_patch(original_code: str, patch_str: str) -> Tuple[bool, str, Optional[str]]:
        """Áp dụng bản vá Unified Diff lên đoạn mã nguồn gốc.
        
        Trả về: (success, result_code, error_message)
        """
        lines = original_code.splitlines(keepends=True)
        patch_lines = patch_str.splitlines()

        hunks = []
        current_hunk = None

        # 1. Phân tích cú pháp các dòng Unified Diff thành hunks
        hunk_header_re = re.compile(r"^@@\s+-(\d+),?(\d+)?\s+\+(\d+),?(\d+)?\s+@@")

        for line in patch_lines:
            # Bỏ qua các dòng header file
            if line.startswith("---") or line.startswith("+++") or line.startswith("Index:") or line.startswith("diff --git"):
                continue

            match = hunk_header_re.match(line)
            if match:
                if current_hunk:
                    hunks.append(current_hunk)
                # Lấy dòng bắt đầu (1-indexed, đổi về 0-indexed)
                orig_start = int(match.group(1)) - 1
                orig_len = int(match.group(2)) if match.group(2) else 1
                current_hunk = {
                    "start": orig_start,
                    "len": orig_len,
                    "lines": []
                }
            elif current_hunk is not None:
                current_hunk["lines"].append(line)

        if current_hunk:
            hunks.append(current_hunk)

        if not hunks:
            return False, original_code, "Không tìm thấy hunk hợp lệ nào trong bản vá."

        # 2. Áp dụng từng hunk từ dưới lên trên (để giữ nguyên chỉ mục dòng ở phía trước)
        hunks.sort(key=lambda h: h["start"], reverse=True)

        for hunk in hunks:
            start = hunk["start"]
            hunk_lines = hunk["lines"]
            
            # Tách biệt các dòng cần khớp và các dòng thay thế
            expected_context = []
            replacement = []
            
            for hl in hunk_lines:
                if hl.startswith(" ") or hl.startswith("-"):
                    expected_context.append(hl[1:])
                if hl.startswith(" ") or hl.startswith("+"):
                    replacement.append(hl[1:])

            # Xác định đoạn lines cần kiểm tra khớp nội dung
            actual_len = len(expected_context)
            # Thử khớp tại vị trí khai báo 'start'
            match_index = -1
            
            # Để tăng tính mềm dẻo (fuzzy matching), ta thử tìm khớp chính xác trong phạm vi lân cận
            search_range = 10  # cho phép lệch tối đa 10 dòng
            for offset in range(0, search_range + 1):
                for direction in [1, -1] if offset > 0 else [1]:
                    test_pos = start + (offset * direction)
                    if 0 <= test_pos <= len(lines) - actual_len:
                        test_lines = [lines[test_pos + i].rstrip("\r\n") for i in range(actual_len)]
                        if test_lines == [el.rstrip("\r\n") for el in expected_context]:
                            match_index = test_pos
                            break
                if match_index != -1:
                    break

            if match_index == -1:
                # Trả về thông báo lỗi xung đột chi tiết
                expected_str = "\n".join(expected_context[:3])
                return False, original_code, f"Không khớp ngữ cảnh tại dòng {start + 1}. Mong đợi:\n{expected_str}"

            # Thực hiện thay thế lines
            # Bảo tồn định dạng xuống dòng của file gốc cho các dòng mới
            newline = "\n"
            if lines:
                # Lấy định dạng xuống dòng của dòng đầu tiên
                newline = "\r\n" if lines[0].endswith("\r\n") else "\n"
                
            replaced_lines = [r + newline for r in replacement]
            lines[match_index:match_index + actual_len] = replaced_lines

        return True, "".join(lines), None
