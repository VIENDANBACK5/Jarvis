from pathlib import Path
import pytest
from backend.core.permissions import PermissionBroker, Decision
from backend.core.tools.read import ReadTool
from backend.core.tools.write import WriteTool
from backend.core.tools.bash import BashTool


def test_permission_broker(tmp_path):
    ws = Path(tmp_path)
    broker = PermissionBroker(workspace=ws)

    read_tool = ReadTool()
    write_tool = WriteTool()
    bash_tool = BashTool()

    # Read tools are allowed by default
    assert broker.needs_approval(read_tool, {"path": "main.py"}) is False

    # Mutating tools require confirmation when no rule exists
    assert broker.needs_approval(write_tool, {"path": "main.py"}) is True

    # Add rule to allow bash pytest
    broker.add_rule(bash_tool, {"command": "pytest"})
    assert broker.needs_approval(bash_tool, {"command": "pytest"}) is False
