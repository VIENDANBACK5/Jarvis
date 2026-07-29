import os
import pytest
from backend.editing.diff_parser import DiffParser
from backend.editing.conflict_detector import ConflictDetector
from backend.editing.patch_session import PatchSession
from backend.telemetry.tracker import TelemetryTracker


def test_telemetry_tracker():
    tracker = TelemetryTracker()
    start = tracker.start_action()
    
    # Ghi nhận hành động mock
    tracker.log_action(
        task_id="task-123",
        agent_id="test-agent",
        tool_name="open_file",
        start_time=start,
        success=True,
        tokens_in=100,
        tokens_out=50,
        cost_usd=0.0003
    )

    summary = tracker.get_summary("task-123")
    assert summary["total_actions"] == 1
    assert summary["total_tokens"] == 150
    assert summary["total_cost_usd"] == 0.0003
    assert summary["success_rate"] == 1.0


def test_conflict_detector():
    detector = ConflictDetector()
    filepath = "src/main.py"
    
    # 1. Đăng ký ban đầu
    original = "x = 1\ny = 2\n"
    detector.register_file(filepath, original)

    # 2. Kiểm tra không có xung đột khi nội dung vẫn giữ nguyên
    has_conflict, _ = detector.detect_conflict(filepath, original)
    assert has_conflict is False

    # 3. Kiểm tra có xung đột khi nội dung bị sửa đổi từ bên ngoài
    modified = "x = 1\ny = 3\n"
    has_conflict_mod, err = detector.detect_conflict(filepath, modified)
    assert has_conflict_mod is True
    assert "Xung đột nội dung" in err


def test_diff_parser_with_missing_header():
    diff_no_header = (
        "@@ -1,2 +1,2 @@\n"
        " def run():\n"
        "-    print(1)\n"
        "+    print(2)\n"
    )

    # Thử parse, kiểm tra tự động chèn header giả lập thành công
    patched_file = DiffParser.parse_patch(diff_no_header, "utils.py")
    assert patched_file is not None
    assert patched_file.path == "utils.py"
    # PatchedFile là một list-like chứa các hunks
    assert len(patched_file) == 1


def test_patch_session_lifecycle(tmp_path):
    file_path = tmp_path / "app.py"
    original = "def run():\n    pass\n"
    file_path.write_text(original, encoding="utf-8")

    modified = "def run():\n    print('Hello')\n"
    diff = (
        "@@ -1,2 +1,2 @@\n"
        " def run():\n"
        "-    pass\n"
        "+    print('Hello')\n"
    )

    session = PatchSession(str(file_path), original, modified, diff)

    # 1. Chạy validate
    is_valid, _ = session.validate()
    assert is_valid is True

    # 2. Áp dụng sửa đổi ghi xuống đĩa
    assert session.apply() is True
    assert file_path.read_text(encoding="utf-8") == modified

    # 3. Phục hồi hoàn nguyên lại file gốc
    assert session.revert() is True
    assert file_path.read_text(encoding="utf-8") == original
