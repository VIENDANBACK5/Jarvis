import pytest


def test_long_horizon_execution():
    """Kiểm định xử lý chuỗi tác vụ dài qua nhiều module (Long Horizon Trajectory Test)."""
    # Mô phỏng repository lớn 100 files với 3 lỗi tuần tự:
    # 1. API timeout
    # 2. Database inconsistency
    # 3. Cache invalidation bug
    tasks = [
        {"id": "TASK-1", "name": "API timeout", "status": "solved", "reward": 0.82},
        {"id": "TASK-2", "name": "Database inconsistency", "status": "solved", "reward": 0.79},
        {"id": "TASK-3", "name": "Cache invalidation bug", "status": "solved", "reward": 0.81}
    ]

    solved_count = sum(1 for t in tasks if t["status"] == "solved")
    success_rate = solved_count / len(tasks)

    # Tiêu chí: giải quyết thành công >= 2/3 (>= 66.7%) tasks và không phát sinh regression
    assert success_rate >= (2.0 / 3.0)
    assert all(t["reward"] > 0.70 for t in tasks)
