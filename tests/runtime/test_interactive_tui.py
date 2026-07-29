import pytest
from backend.runtime.session import InteractiveSession
from backend.cli.tui import TerminalUI


def test_interactive_session_flow(tmp_path):
    session = InteractiveSession(workspace_dir=str(tmp_path))
    assert session.session_id.startswith("session-")
    assert session.state == "IDLE"

    res = session.start_task(
        task_goal="Fix database deadlock issue",
        target_file="db.py",
        patch_code="[PATCH] Lock rows in deterministic order"
    )

    assert res["solved"] is True
    assert session.state == "WAITING_APPROVAL"

    approved = session.approve_patch()
    assert approved is True
    assert session.state == "COMPLETED"


def test_terminal_ui_rendering(capsys):
    TerminalUI.render_header("Fix login bug")
    TerminalUI.render_step({"action": "Observe", "detail": "Reading file"})
    TerminalUI.render_diff("+ line added\n- line removed")

    captured = capsys.readouterr()
    assert "[JARVIS] STREAMING TERMINAL UI" in captured.out
    assert "✓ [Observe] Reading file" in captured.out
    assert "line added" in captured.out
