import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PatchQualityAnalyzer:
    @staticmethod
    def evaluate_patch(patch_content: str) -> float:
        """Đánh giá chất lượng bản vá định lượng từ 0.0 đến 1.0."""
        if not patch_content:
            return 0.0

        score = 1.0

        # Tiêu chí 1: Độ phức tạp & Rủi ro hồi quy (Tránh sửa đổi quá mức hoặc bẩn)
        # Bắt các exception pass bẩn
        if "except Exception:" in patch_content and "pass" in patch_content:
            score -= 0.3
            logger.info("PatchQualityAnalyzer: Phát hiện khối try-except bẩn (pass), trừ 0.3 điểm.")

        # Tiêu chí 2: Khả năng bảo trì & Chuẩn hóa code
        # Ưu tiên có comment giải thích hoặc docstring
        if '"""' in patch_content or "'''" in patch_content or "#" in patch_content:
            score += 0.1
            logger.info("PatchQualityAnalyzer: Phát hiện tài liệu hóa/comment giải thích, cộng 0.1 điểm.")

        # Khống chế điểm số trong khoảng [0.0, 1.0]
        score = max(0.0, min(1.0, score))
        score = round(score, 3)

        logger.info(f"PatchQualityAnalyzer: Bản vá đạt điểm chất lượng: {score}")
        return score
