import os
import pytest
import shutil
import asyncio
from backend.tools.git.checkpoint import GitCheckpointManager


def is_git_installed() -> bool:
    return shutil.which("git") is not None


@pytest.mark.asyncio
async def test_git_checkpoint_and_rollback(tmp_path):
    if not is_git_installed():
        pytest.skip("Bỏ qua test vì Git không được cài đặt trên hệ thống.")

    repo_dir = str(tmp_path)
    
    # 1. Khởi tạo repo git tạm thời
    proc = await asyncio.create_subprocess_exec("git", "init", cwd=repo_dir)
    await proc.wait()
    await asyncio.sleep(0.5)
    
    # Cấu hình user dummy cho commit trong test
    proc_email = await asyncio.create_subprocess_exec("git", "config", "user.email", "test@test.com", cwd=repo_dir)
    await proc_email.wait()
    proc_name = await asyncio.create_subprocess_exec("git", "config", "user.name", "Test User", cwd=repo_dir)
    await proc_name.wait()

    manager = GitCheckpointManager(repo_dir)
    assert await manager.is_git_repo() is True

    # 2. Tạo file ban đầu và checkpoint
    file_path = tmp_path / "hello.txt"
    file_path.write_text("Trạng thái ban đầu\n", encoding="utf-8")
    
    checkpoint_hash = await manager.create_checkpoint("First commit")
    assert len(checkpoint_hash) > 0

    # 3. Sửa file và tạo file mới (rác)
    file_path.write_text("Đã bị thay đổi\n", encoding="utf-8")
    new_file = tmp_path / "extra.txt"
    new_file.write_text("File rác mới\n", encoding="utf-8")

    # Kiểm tra xem diff có thấy sự thay đổi không
    diff = await manager.get_diff(checkpoint_hash)
    assert "Trạng thái ban đầu" in diff
    assert "Đã bị thay đổi" in diff

    # 4. Thực hiện rollback phục hồi trạng thái cũ
    success = await manager.rollback(checkpoint_hash)
    assert success is True

    # Xác thực file đã quay về nội dung ban đầu
    assert file_path.read_text(encoding="utf-8") == "Trạng thái ban đầu\n"
    # Xác thực file rác đã bị xóa sạch
    assert not new_file.exists()
