import os
import logging
from typing import Tuple, Optional

from backend.editing.patch_validator import PatchValidator

logger = logging.getLogger(__name__)


class PatchSession:
    def __init__(
        self,
        filepath: str,
        original_content: str,
        modified_content: str,
        diff_str: str
    ):
        self.filepath = os.path.abspath(filepath)
        self.original_content = original_content
        self.modified_content = modified_content
        self.diff_str = diff_str
        self._applied = False

    def validate(self) -> Tuple[bool, Optional[str]]:
        """Kiểm chứng độ an toàn (cú pháp, AST) của bản vá."""
        return PatchValidator.validate_patch(
            self.original_content,
            self.diff_str,
            filename=os.path.basename(self.filepath)
        )

    def apply(self) -> bool:
        """Ghi đè nội dung đã vá xuống file trên đĩa."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.modified_content)
            self._applied = True
            logger.info(f"PatchSession: Đã ghi đè thành công {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"PatchSession: Lỗi khi ghi đè file {self.filepath}: {str(e)}")
            return False

    def revert(self) -> bool:
        """Phục hồi nội dung file gốc ban đầu trên đĩa."""
        if not self._applied:
            logger.info(f"PatchSession: Phiên chưa ghi đè đĩa, không cần revert cho {self.filepath}")
            return True
            
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.original_content)
            self._applied = False
            logger.info(f"PatchSession: Đã khôi phục hoàn nguyên file gốc: {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"PatchSession: Lỗi khi khôi phục hoàn nguyên file {self.filepath}: {str(e)}")
            return False

    @property
    def is_applied(self) -> bool:
        return self._applied
