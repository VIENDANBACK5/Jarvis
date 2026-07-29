import shutil
import pytest
import asyncio

from backend.sandbox.docker_runtime import DockerSandbox


def is_docker_available() -> bool:
    """Kiểm tra xem Docker CLI có khả dụng trên hệ thống không."""
    return shutil.which("docker") is not None


@pytest.mark.asyncio
async def test_sandbox_execution():
    """Kiểm thử khởi chạy Docker Sandbox và thực thi câu lệnh cô lập."""
    if not is_docker_available():
        pytest.skip("Bỏ qua test vì Docker CLI không được cài đặt hoặc không khả dụng.")

    # Đặt tên sandbox tạm thời cho test
    sandbox = DockerSandbox(
        container_name="jarvis-sandbox-test-temp",
        image="python:3.11-slim"
    )

    # Khởi chạy container
    started = await sandbox.start()
    if not started:
        pytest.skip("Bỏ qua test vì Docker daemon không hoạt động hoặc lỗi khởi tạo.")

    try:
        # 1. Kiểm tra thực thi lệnh thành công
        res = await sandbox.execute("echo 'Hello Jarvis Sandbox'")
        assert res["exit_code"] == 0
        assert "Hello Jarvis Sandbox" in res["stdout"].strip()

        # 2. Kiểm tra thực thi python script
        res_py = await sandbox.execute("python -c \"print(2 + 3)\"")
        assert res_py["exit_code"] == 0
        assert res_py["stdout"].strip() == "5"

        # 3. Kiểm tra kiểm soát giới hạn thời gian (Timeout)
        res_timeout = await sandbox.execute("sleep 2", timeout=1)
        assert res_timeout["timeout"] is True
        assert "vượt quá giới hạn thời gian" in res_timeout["stderr"]
    finally:
        # Dọn dẹp container sau khi test xong
        await sandbox.stop()
