import os
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.autonomy.observer.failure_miner import FailureMiner
from backend.autonomy.hypothesis.generator import HypothesisGenerator
from backend.autonomy.experiment.branch_manager import BranchManager
from backend.autonomy.evaluation.benchmark import BenchmarkRunner
from backend.autonomy.optimizer.decision import AutonomyOptimizer


def test_failure_miner(tmp_path):
    # 1. Tạo mock trajectory files
    task1 = [
        {"event_type": "action", "action_name": "open_file"},
        {"event_type": "observation", "outputs": {"error": "syntax error", "category": "syntax_error"}}
    ]
    task2 = [
        {"event_type": "action", "action_name": "run_test"},
        {"event_type": "observation", "outputs": {"error": "ModuleNotFoundError", "category": "dependency_error"}}
    ]
    task3 = [
        {"event_type": "action", "action_name": "run_test"},
        {"event_type": "observation", "outputs": {"error": "ModuleNotFoundError", "category": "dependency_error"}}
    ]

    with open(tmp_path / "task_1.json", "w") as f:
        json.dump(task1, f)
    with open(tmp_path / "task_2.json", "w") as f:
        json.dump(task2, f)
    with open(tmp_path / "task_3.json", "w") as f:
        json.dump(task3, f)

    miner = FailureMiner(str(tmp_path))
    stats = miner.mine_failures()

    assert stats["total_tasks_scanned"] == 3
    assert stats["total_failures"] == 3
    assert stats["categories"]["dependency_error"] == 2
    assert stats["categories"]["syntax_error"] == 1
    assert stats["most_common_failure"] == "dependency_error"


@pytest.mark.asyncio
async def test_hypothesis_generator():
    generator = HypothesisGenerator()
    stats = {
        "total_tasks_scanned": 10,
        "total_failures": 5,
        "categories": {"dependency_error": 4, "syntax_error": 1},
        "most_common_failure": "dependency_error"
    }

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content=(
        "{\n"
        "  \"hypothesis_id\": \"hyp-123\",\n"
        "  \"description\": \"Thêm hướng dẫn cài đặt dependency.\",\n"
        "  \"target_file\": \"backend/config/prompts/coder.txt\",\n"
        "  \"proposed_change\": \"Hãy tự động cài đặt dependency nếu test báo thiếu module.\",\n"
        "  \"confidence\": 0.90\n"
        "}"
    )))

    with patch("backend.autonomy.hypothesis.generator.get_llm", return_value=mock_llm):
        proposal = await generator.generate_hypothesis(stats)
        
        assert proposal["hypothesis_id"] == "hyp-123"
        assert proposal["target_file"] == "backend/config/prompts/coder.txt"
        assert proposal["confidence"] == 0.90


@pytest.mark.asyncio
async def test_branch_manager_git_calls(tmp_path):
    manager = BranchManager(str(tmp_path))

    # Mock git subprocess execution để tránh thay đổi nhánh git thực tế của workspace
    mock_run = AsyncMock(return_value=(0, "Success", ""))
    manager._run_git = mock_run

    # 1. Test tạo nhánh
    ok = await manager.create_experiment_branch("experiment/prompt-v2")
    assert ok is True
    # Verify checkout -b was run
    mock_run.assert_any_call("checkout", "-b", "experiment/prompt-v2")

    # 2. Test apply change
    file_path = "backend/config/prompts/coder.txt"
    ok_apply = await manager.apply_proposal_change(file_path, "New prompt instruction")
    assert ok_apply is True
    # Kiểm tra nội dung file được ghi đúng
    assert (tmp_path / file_path).read_text(encoding="utf-8") == "New prompt instruction"

    # 3. Test checkout main and merge
    ok_merge = await manager.checkout_main_and_merge("experiment/prompt-v2")
    assert ok_merge is True
    mock_run.assert_any_call("merge", "experiment/prompt-v2", "--no-edit")


@pytest.mark.asyncio
async def test_benchmark_runner(tmp_path):
    runner = BenchmarkRunner(os.getcwd())
    
    # Chỉ chạy thử trên 1 file test siêu nhỏ để lấy điểm số thật
    reward = await runner.run_quick_evaluation("tests/test_openai_api.py")
    assert reward >= -1.0
    assert reward <= 1.0


def test_autonomy_optimizer():
    optimizer = AutonomyOptimizer(threshold=0.05)

    # 1. Cải tiến tốt vượt ngưỡng -> Accept
    accept, msg = optimizer.decide_on_proposal(old_reward=0.20, new_reward=0.28)
    assert accept is True
    assert "Accept" in msg

    # 2. Cải tiến kém hoặc thụt lùi -> Reject
    reject, msg_r = optimizer.decide_on_proposal(old_reward=0.20, new_reward=0.22)
    assert reject is False
    assert "Reject" in msg_r
