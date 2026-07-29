import logging
from typing import List, Optional
from unidiff import PatchSet, PatchedFile

logger = logging.getLogger(__name__)


class DiffParser:
    @staticmethod
    def parse_patch(diff_str: str, default_filename: str = "file.py") -> Optional[PatchedFile]:
        """Phân tích chuỗi Unified Diff thô thành đối tượng PatchedFile có cấu trúc của unidiff.
        
        Tự động bổ sung header giả lập nếu LLM quên sinh dòng --- và +++.
        """
        lines = diff_str.splitlines()
        
        # Kiểm tra xem có dòng header file nào không
        has_header = False
        for line in lines[:5]:
            if line.startswith("---") or line.startswith("+++") or line.startswith("Index:"):
                has_header = True
                break

        # Nếu không có header, chèn header giả lập để unidiff có thể parse thành công
        if not has_header:
            logger.debug(f"DiffParser: Không tìm thấy header. Đang bổ sung header giả lập cho {default_filename}")
            header = [
                f"--- a/{default_filename}",
                f"+++ b/{default_filename}",
            ]
            # Đảm bảo chèn ngay trước các hunk @@
            hunk_index = 0
            for idx, line in enumerate(lines):
                if line.startswith("@@"):
                    hunk_index = idx
                    break
            
            lines = lines[:hunk_index] + header + lines[hunk_index:]

        normalized_diff = "\n".join(lines) + "\n"

        try:
            patch_set = PatchSet(normalized_diff)
            if len(patch_set) > 0:
                return patch_set[0]
        except Exception as e:
            logger.error(f"DiffParser: Lỗi phân tích cú pháp diff: {str(e)}")
            
        return None
