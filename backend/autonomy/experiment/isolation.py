import os
import shutil
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class IsolationManager:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        # Lưu trữ nội dung tệp tin đã sao lưu trong bộ nhớ: {relative_path: original_content}
        self._backup_registry: Dict[str, str] = {}

    def backup_file(self, target_file: str) -> bool:
        """Sao lưu trạng thái nội dung file trước khi thử nghiệm sửa đổi."""
        full_path = os.path.abspath(os.path.join(self.workspace_dir, target_file))
        if not os.path.exists(full_path):
            logger.warning(f"IsolationManager: File sao lưu không tồn tại: {full_path}")
            return False

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self._backup_registry[target_file] = content
            logger.info(f"IsolationManager: Đã sao lưu thành công {target_file} vào registry")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi sao lưu file {target_file}: {str(e)}")
            return False

    def restore_file(self, target_file: str) -> bool:
        """Phục hồi hoàn nguyên tệp tin về trạng thái sao lưu ban đầu."""
        if target_file not in self._backup_registry:
            logger.warning(f"IsolationManager: Không tìm thấy registry sao lưu cho: {target_file}")
            return False

        full_path = os.path.abspath(os.path.join(self.workspace_dir, target_file))
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(self._backup_registry[target_file])
            logger.info(f"IsolationManager: Đã khôi phục hoàn nguyên thành công {target_file}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi khôi phục hoàn nguyên file {target_file}: {str(e)}")
            return False

    def clear(self):
        self._backup_registry.clear()
