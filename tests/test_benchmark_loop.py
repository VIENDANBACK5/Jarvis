import os
import json
import pytest
from unittest.mock import patch, MagicMock

from backend.learning.memory_replay import EngineeringMemoryReplay
from backend.evaluation.patch_quality import PatchQualityAnalyzer
from backend.evaluation.evaluator import MultiObjectiveEvaluator
from backend.evaluation.repo_manager import RepoManager
from backend.evaluation.swe_runner import SWERunner


def test_engineering_memory_replay():
    replay = EngineeringMemoryReplay("/tmp/mock_exp")
    
    # 1. Khớp issue async -> Trả về trajectory tương ứng
    res_async = replay.retrieve_journey("async iterator timeout error in loop")
    assert res_async["matched_topic"] == "async iterator handling timeout"
    assert "LOCATE: backend/async_helpers.py" in res_async["trajectory"]
    assert res_async["confidence"] > 0.5

    # 2. Khớp issue database -> Trả về trajectory tương ứng
    res_db = replay.retrieve_journey("database migration mismatched version")
    assert res_db["matched_topic"] == "database migration conflict"
    assert "LOCATE: migrations/" in res_db["trajectory"]

    # 3. Không khớp -> Trả về hành trình chung mặc định
    res_unknown = replay.retrieve_journey("unknown token problem")
    assert res_unknown["matched_topic"] == "generic task"
    assert res_unknown["confidence"] == 0.1


def test_patch_quality_analyzer():
    good_patch = (
        "def charge(self):\n"
        "    # Thực hiện thanh toán qua stripe\n"
        "    return stripe.charge()\n"
    )
    bad_patch = (
        "def charge(self):\n"
        "    try:\n"
        "        stripe.charge()\n"
        "    except Exception:\n"
        "        pass # Tránh crash\n"
    )

    score_good = PatchQualityAnalyzer.evaluate_patch(good_patch)
    score_bad = PatchQualityAnalyzer.evaluate_patch(bad_patch)

    assert score_good > score_bad
    assert score_bad <= 0.80  # Phải bị trừ điểm vì pass bẩn


def test_multi_objective_evaluator():
    evaluator = MultiObjectiveEvaluator()
    
    # 1. Chạy hoàn hảo, ít token, chạy nhanh
    reward_best = evaluator.calculate_reward(
        success_rate=1.0,
        patch_content="def solve(): # resolve issue\n    pass",
        token_count=1000,
        duration_sec=10.0
    )
    assert reward_best >= 0.75

    # 2. Test pass kém, patch bẩn, tốn token, chạy lâu -> Reward thấp
    reward_bad = evaluator.calculate_reward(
        success_rate=0.4,
        patch_content="try:\n    pass\nexcept Exception:\n    pass",
        token_count=60000,
        duration_sec=700.0
    )
    assert reward_bad < 0.50


@patch("subprocess.run")
def test_repo_manager(mock_run):
    # Cấu hình mock
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
    
    manager = RepoManager("/tmp/mock_repo")
    
    assert manager.backup_checkpoint() is True
    assert manager.restore_checkpoint() is True


@patch("subprocess.run")
def test_swe_runner_integration(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
    
    ws_dir = tmp_path / "ws"
    exp_dir = tmp_path / "exp"
    graph_file = tmp_path / "causal_graph.json"
    os.makedirs(ws_dir)
    os.makedirs(exp_dir)

    runner = SWERunner(str(ws_dir), str(exp_dir), str(graph_file))

    # 1. Chạy thành công -> success = True, reward cao
    res_success = runner.run_task(
        issue_text="async iterator timeout error",
        patch_content="def run_async(): # docstring\n    pass",
        token_count=1000,
        duration_sec=10.0,
        success_rate=1.0
    )

    assert res_success["success"] is True
    assert res_success["reward"] >= 0.70
    assert "LOCATE: backend/async_helpers.py" in res_success["journey_guide"]

    # Đảm bảo đồ thị tiến hóa ghi nhận thành công
    with open(graph_file, "r") as f:
        data = json.load(f)
    assert data["links"][0]["confidence"] > 0.50

    # 2. Chạy thất bại -> success = False
    res_fail = runner.run_task(
        issue_text="database migration mismatched",
        patch_content="try:\n    pass\nexcept:\n    pass",
        token_count=60000,
        duration_sec=800.0,
        success_rate=0.2
    )
    assert res_fail["success"] is False
