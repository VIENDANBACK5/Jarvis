import pytest
from backend.cli.rich_tui import RichTerminalUI
from backend.runtime.event import RuntimeEvent


def test_rich_terminal_ui(capsys):
    ui = RichTerminalUI()
    ui.render_banner("Fix payment authorization bug")
    ui.handle_event(RuntimeEvent(event_type="TASK_CREATED", payload={"detail": "Started task"}))
    ui.handle_event(RuntimeEvent(event_type="SEARCH_COMPLETED", payload={"detail": "Found payment.py"}))
    ui.render_checklist()

    captured = capsys.readouterr()
    assert "JARVIS ENGINEERING AGENT" in captured.out
    assert "Fix payment authorization bug" in captured.out
    assert "Found payment.py" in captured.out
    assert "1. [✓] Scan repository AST" in captured.out
