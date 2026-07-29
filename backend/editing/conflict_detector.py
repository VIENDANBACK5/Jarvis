import hashlib
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class ConflictDetector:
    def __init__(self):
        # Lưu mã hash SHA256 gốc của các file khi đọc: {filepath: sha256_hash}
        self._read_registry: Dict[str, str] = {}

    def _calculate_hash(self, content: str) -> str:
        """Tính toán SHA256 hash cho nội dung chuỗi."""
        return hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()

    def register_file(self, filepath: str, content: str):
        """Ghi nhận mã hash gốc của file khi Agent đọc file."""
        file_hash = self._calculate_hash(content)
        self._read_registry[filepath] = file_hash
        logger.debug(f"ConflictDetector: Registered {filepath} with hash {file_hash[:8]}...")

    def detect_conflict(self, filepath: str, current_content: str) -> Tuple[bool, Optional[str]]:
        """Kiểm tra xem nội dung file hiện tại trên đĩa có bị sửa đổi so với khi đọc không.
        
        Trả về: (has_conflict, error_message)
        """
        if filepath not in self._read_registry:
            # File chưa từng được đọc (ví dụ: tạo mới hoàn toàn) -> không có xung đột
            return False, None

        expected_hash = self._read_registry[filepath]
        current_hash = self._calculate_hash(current_content)

        if expected_hash != current_hash:
            logger.warning(
                f"Conflict detected on {filepath}! "
                f"Expected hash: {expected_hash[:8]} | Actual hash: {current_hash[:8]}"
            )
            return True, (
                f"Xung đột nội dung (Context Conflict) trên file '{filepath}': "
                f"File đã bị thay đổi bên ngoài kể từ lần cuối Agent đọc file."
            )

        return False, None

    def clear(self):
        self._read_registry.clear()
