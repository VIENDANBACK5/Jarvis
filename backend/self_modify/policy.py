import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Các thư mục hoặc tệp được phép tự sửa đổi (chỉnh sửa prompts, config)
ALLOWED_PREFIXES = [
    "backend/config/prompts/",
    "backend/config/prompts.py",
    "backend/services/llm/router.py",
    "backend/graph/state.py",
]

# Các thư mục hoặc tệp cấm ngặt nghèo (bảo mật sandbox, chính sách bảo vệ lõi)
BLOCKED_PREFIXES = [
    "backend/sandbox/",
    "backend/self_modify/",
    "backend/evaluation/reward.py",
    "backend/registry/",
]


class SelfModificationPolicy:
    @staticmethod
    def is_modification_allowed(filepath: str, base_dir: str = ".") -> Tuple[bool, Optional[str]]:
        """Kiểm tra xem file chỉ định có được phép sửa đổi tự động bởi Agent hay không.
        
        Trả về: (allowed, error_reason)
        """
        # Chuẩn hóa đường dẫn tương đối để dễ so khớp
        norm_path = os.path.relpath(os.path.abspath(filepath), os.path.abspath(base_dir)).replace("\\", "/")

        # 1. Kiểm tra danh sách cấm trước (Blocked list)
        for blocked in BLOCKED_PREFIXES:
            if norm_path.startswith(blocked):
                return False, f"Chính sách bảo mật: Cấm tự động sửa đổi lõi hệ thống tại '{blocked}'"

        # 2. Kiểm tra danh sách cho phép (Allowed list)
        for allowed in ALLOWED_PREFIXES:
            if norm_path.startswith(allowed):
                return True, None

        # 3. Theo mặc định, nếu không khớp danh sách được phép cụ thể -> Cấm để bảo đảm an toàn hệ thống
        return False, f"Chính sách bảo mật: File '{norm_path}' không nằm trong danh sách cho phép tự sửa đổi."
