import logging

logger = logging.getLogger(__name__)


def calculate_reward(
    test_success: float,       # Tỷ lệ test case pass (0.0 đến 1.0)
    code_quality: float,       # Điểm chất lượng code tĩnh/AST (0.0 đến 1.0)
    token_cost_usd: float,     # Chi phí token sử dụng thực tế (USD)
    execution_time_sec: float  # Thời gian thực thi (giây)
) -> float:
    """Tính toán phần thưởng định lượng (reward) của hành động cải tiến.
    
    Công thức:
    reward = (0.5 * test_success) + (0.2 * code_quality) - (0.1 * token_cost_usd * 100) - (0.2 * execution_time_sec / 60)
    """
    # Chuẩn hóa chi phí token (giả định 1$ là rất lớn, ta nhân 100 để có penalty đáng kể)
    token_penalty = 0.1 * (token_cost_usd * 100)
    
    # Chuẩn hóa thời gian thực thi (chia cho 60 giây để quy về phút, penalty trên thang phút)
    time_penalty = 0.2 * (execution_time_sec / 60.0)
    
    base_reward = (0.5 * test_success) + (0.2 * code_quality)
    final_reward = base_reward - token_penalty - time_penalty

    # Giới hạn reward tối thiểu là -1.0 và tối đa là 1.0
    final_reward = max(-1.0, min(1.0, final_reward))

    logger.debug(
        f"Reward calculation: test_success={test_success} | code_quality={code_quality} | "
        f"token_cost_usd={token_cost_usd} | execution_time_sec={execution_time_sec} | "
        f"calculated_reward={final_reward:.4f}"
    )
    return final_reward
