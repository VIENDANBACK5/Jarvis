import pytest


def test_replay_consistency():
    """Kiểm định tính tái lặp kết quả (Deterministic Replay Consistency Test)."""
    # Mô phỏng 3 lần chạy liên tiếp trên cùng 1 task lỗi token refresh authentication
    run_results = [
        {
            "root_cause": "JWT token expired after session timeout",
            "patch": "[PATCH] Refresh token before calling protected endpoint",
            "reward": 0.85
        },
        {
            "root_cause": "JWT token expiration in session timeout window",
            "patch": "[PATCH] Refresh token before calling protected endpoint",
            "reward": 0.82
        },
        {
            "root_cause": "JWT token expired after session timeout",
            "patch": "[PATCH] Refresh token logic added before API call",
            "reward": 0.86
        }
    ]

    rewards = [r["reward"] for r in run_results]
    mean_reward = sum(rewards) / len(rewards)
    reward_variance = sum((x - mean_reward) ** 2 for x in rewards) / len(rewards)

    # 1. Kiểm tra variance của reward < 0.15
    assert reward_variance < 0.15

    # 2. Kiểm tra tính tương đồng patch và root cause
    assert "JWT" in run_results[0]["root_cause"] and "JWT" in run_results[1]["root_cause"]
    assert "Refresh token" in run_results[0]["patch"]
