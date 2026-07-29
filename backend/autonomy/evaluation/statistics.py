import math
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class StatisticalValidator:
    @staticmethod
    def validate_improvement(
        old_rewards: List[float],
        new_rewards: List[float],
        alpha: float = 0.05
    ) -> Tuple[bool, str]:
        """Kiểm định thống kê xem sự cải tiến giữa 2 nhóm kết quả có ý nghĩa thực sự hay không."""
        n_old = len(old_rewards)
        n_new = len(new_rewards)

        if n_old == 0 or n_new == 0:
            return False, "Không có đủ mẫu kết quả để kiểm định thống kê."

        mean_old = sum(old_rewards) / n_old
        mean_new = sum(new_rewards) / n_new
        delta = mean_new - mean_old

        if n_old < 2 or n_new < 2:
            # Không đủ mẫu để tính phương sai -> Dựa trên so khớp ngưỡng delta thô tối thiểu
            is_significant = delta > 0.02
            msg = (
                f"Kiểm định thô (Cỡ mẫu quá nhỏ): Mean Old: {mean_old:.4f} | "
                f"Mean New: {mean_new:.4f} | Delta: {delta:.4f} | Ý nghĩa: {is_significant}"
            )
            return is_significant, msg

        # Tính phương sai mẫu (sample variance)
        var_old = sum((x - mean_old) ** 2 for x in old_rewards) / (n_old - 1)
        var_new = sum((x - mean_new) ** 2 for x in new_rewards) / (n_new - 1)

        # Tính sai số tiêu chuẩn (Standard Error) của sự khác biệt trung bình
        standard_error = math.sqrt((var_old / n_old) + (var_new / n_new))
        
        if standard_error == 0:
            is_significant = delta > 0.0
            return is_significant, f"Sai số tiêu chuẩn bằng 0. Delta: {delta:.4f} | Ý nghĩa: {is_significant}"

        # Tính trị số t-statistic
        t_stat = delta / standard_error
        
        # Ngưỡng t-critical đơn giản cho độ tin cậy 95% (2-tailed, t xấp xỉ 1.96 - 2.0 tùy bậc tự do)
        t_critical = 1.96
        is_significant = t_stat >= t_critical

        msg = (
            f"Kiểm định T-Test: Mean Old: {mean_old:.4f} | Mean New: {mean_new:.4f} | "
            f"Delta: {delta:.4f} | Standard Error: {standard_error:.4f} | "
            f"T-Stat: {t_stat:.2f} (Critical: {t_critical}) | Ý nghĩa thống kê: {is_significant}"
        )
        logger.info(msg)
        return is_significant, msg
