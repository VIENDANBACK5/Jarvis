import pytest
from backend.sandbox.docker_manager import DockerSandboxManager
from backend.sandbox.container_executor import ContainerExecutor
from backend.sandbox.resource_monitor import ResourceMonitor


def test_docker_sandbox_lifecycle(tmp_path):
    mgr = DockerSandboxManager(str(tmp_path))
    container_id = mgr.create_sandbox(str(tmp_path))

    assert container_id.startswith("jarvis-sandbox-")
    assert mgr.active_container_id == container_id

    executor = ContainerExecutor(container_id)
    res = executor.execute_command("echo 'Hello Sandbox'")
    assert res["passed"] is True
    assert "Hello Sandbox" in res["stdout"]

    monitor = ResourceMonitor(memory_limit_mb=512)
    limits = monitor.check_resource_limits(memory_used_mb=128.0, cpu_used_pct=15.0)
    assert limits["is_safe"] is True

    destroyed = mgr.destroy_sandbox()
    assert destroyed is True
    assert mgr.active_container_id is None
