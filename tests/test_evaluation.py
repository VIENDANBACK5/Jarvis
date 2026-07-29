import os
import pytest
import shutil
import asyncio
from unittest.mock import patch, MagicMock

from backend.evaluation.runner import SWEBenchEvaluator


def is_git_installed() -> bool:
    return shutil.which("git") is not None and shutil.which("docker") is not None


@pytest.mark.asyncio
async def test_swe_bench_evaluator(tmp_path):
    if not is_git_installed():
        pytest.skip("Bỏ qua test vì Git hoặc Docker không khả dụng.")

    repo_dir = str(tmp_path)
    
    # 1. Khởi tạo Repo Git giả lập
    proc = await asyncio.create_subprocess_exec("git", "init", cwd=repo_dir)
    await proc.wait()
    proc_email = await asyncio.create_subprocess_exec("git", "config", "user.email", "test@test.com", cwd=repo_dir)
    await proc_email.wait()
    proc_name = await asyncio.create_subprocess_exec("git", "config", "user.name", "Test User", cwd=repo_dir)
    await proc_name.wait()

    # 2. Commit 1: Trạng thái gốc
    file_path = tmp_path / "app.py"
    file_path.write_text("APP_NAME = 'Original'\n", encoding="utf-8")
    
    proc_add = await asyncio.create_subprocess_exec("git", "add", ".", cwd=repo_dir)
    await proc_add.wait()
    proc_commit = await asyncio.create_subprocess_exec("git", "commit", "-m", "Initial commit", cwd=repo_dir)
    await proc_commit.wait()
    
    # Lấy commit hash 1
    proc_hash = await asyncio.create_subprocess_exec(
        "git", "rev-parse", "HEAD",
        cwd=repo_dir,
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc_hash.communicate()
    base_commit_hash = stdout.decode().strip()

    # 3. Tạo nhánh 'main' làm mốc khôi phục của Git
    proc_branch = await asyncio.create_subprocess_exec("git", "branch", "-M", "main", cwd=repo_dir)
    await proc_branch.wait()

    # 4. Mock cuộc gọi sửa đổi của Agent để giả lập sửa file thành công
    async def mock_run_and_heal(*args, **kwargs):
        # Giả lập sửa đổi file trong sandbox/workspace
        file_path.write_text("APP_NAME = 'Healed'\n", encoding="utf-8")
        return {
            "status": "success",
            "retries": 1,
            "error": None
        }

    evaluator = SWEBenchEvaluator(repo_dir)
    
    instance = {
        "instance_id": "issue-42",
        "repo": "jarvis-eval-repo",
        "base_commit": base_commit_hash,
        "problem_statement": "Change APP_NAME to Healed",
        "test_patch": ""
    }

    # Chạy đánh giá
    with patch("backend.execution.engine.ExecutionEngine.run_and_heal_code_task", side_effect=mock_run_and_heal):
        res = await evaluator.evaluate_instance(instance)

    # 5. Xác thực kết quả đầu ra
    assert res["instance_id"] == "issue-42"
    assert res["status"] == "completed"
    assert res["agent_success"] is True
    assert res["retries"] == 1
    assert "APP_NAME = 'Healed'" in res["patch_diff"]
    assert "-APP_NAME = 'Original'" in res["patch_diff"]
