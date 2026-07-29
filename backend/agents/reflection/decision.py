import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class DecisionAgent:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def decide(self, current_retry: int, error_category: str) -> Tuple[str, str]:
        """Đưa ra quyết định tiếp theo: 'retry', 'change_strategy', hoặc 'abort'."""
        if current_retry >= self.max_retries:
            return "abort", f"Vượt quá số lần thử tối đa ({self.max_retries}). Dừng tác vụ để bảo vệ tài nguyên."

        if error_category in ["dependency_error", "syntax_error"]:
            # Lỗi biên dịch hoặc thiếu thư viện -> Sửa trực diện tại chỗ
            return "retry", f"Lỗi cú pháp/môi trường ({error_category}). Tiến hành vá lỗi và chạy lại."

        if current_retry >= 2:
            # Đã thử 2 lần chiến lược cũ nhưng lỗi logic vẫn tiếp diễn -> Khuyên đổi chiến lược
            return "change_strategy", "Chiến lược hiện tại không hiệu quả. Đang chuyển giao chiến lược mới."

        return "retry", "Tiếp tục sửa đổi mã nguồn và chạy lại."
