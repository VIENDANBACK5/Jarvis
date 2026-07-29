import pytest
import shutil
import asyncio
from unittest.mock import patch, MagicMock

from backend.execution.engine import ExecutionEngine


def is_docker_available() -> bool:
    return shutil.which("docker") is not None and shutil.which("git") is not None


@pytest.mark.asyncio
async def test_execution_engine_success(tmp_path):
    """Test luồng thực thi thành công ngay từ lần đầu tiên."""
    if not is_docker_available():
        pytest.skip("Bỏ qua test vì Docker hoặc Git không khả dụng trên hệ thống.")

    repo_dir = str(tmp_path)
    
    # Khởi tạo Git repo
    proc = await asyncio.create_subprocess_exec("git", "init", cwd=repo_dir)
    await proc.wait()
    await asyncio.create_subprocess_exec("git", "config", "user.email", "test@test.com", cwd=repo_dir)
    await asyncio.create_subprocess_exec("git", "config", "user.name", "Test User", cwd=repo_dir)

    # Viết một file mẫu
    (tmp_path / "main.py").write_text("print('Start')\n", encoding="utf-8")

    engine = ExecutionEngine(repo_dir, max_retries=2)
    
    # Lệnh test thành công (chạy python xuất ra chữ Healed)
    res = await engine.run_and_heal_code_task(
        task_desc="Print Healed",
        test_command="python -c \"print('Healed')\""
    )

    assert res["status"] == "success"
    assert res["retries"] == 0
    assert res["error"] is None


@pytest.mark.asyncio
async def test_execution_engine_failure_and_rollback(tmp_path):
    """Test luồng thực thi thất bại liên tục và kích hoạt Git Rollback."""
    if not is_docker_available():
        pytest.skip("Bỏ qua test vì Docker hoặc Git không khả dụng trên hệ thống.")

    repo_dir = str(tmp_path)
    
    # Khởi tạo Git repo
    proc = await asyncio.create_subprocess_exec("git", "init", cwd=repo_dir)
    await proc.wait()
    await asyncio.create_subprocess_exec("git", "config", "user.email", "test@test.com", cwd=repo_dir)
    await asyncio.create_subprocess_exec("git", "config", "user.name", "Test User", cwd=repo_dir)

    # Viết file ban đầu
    file_path = tmp_path / "hello.txt"
    file_path.write_text("Original State\n", encoding="utf-8")

    # Khởi tạo Engine với số lượt retry = 2
    engine = ExecutionEngine(repo_dir, max_retries=2)
    
    # Thử chạy lệnh cố tình lỗi
    res = await engine.run_and_heal_code_task(
        task_desc="Run failing command",
        test_command="python -c \"import sys; sys.exit(1)\""
    )

    assert res["status"] == "failed"
    assert res["retries"] == 2
    assert "Exit Code: 1" in res["error"]

    # Đảm bảo file được phục hồi nguyên vẹn
    assert file_path.read_text(encoding="utf-8") == "Original State\n"
