import pytest
from backend.tools.registry import ToolRegistry
from backend.tools.search_tool import SearchTool
from backend.tools.read_tool import ReadTool
from backend.tools.edit_tool import EditTool
from backend.tools.pytest_tool import PytestTool


def test_tool_registry():
    registry = ToolRegistry()
    registry.register(SearchTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(PytestTool())

    tools = registry.list_tools()
    assert len(tools) == 4

    res = registry.execute_tool("search", query="authentication")
    assert res["status"] == "SUCCESS"
    assert res["result"]["query"] == "authentication"

    edit_res = registry.execute_tool("edit_file", filepath="auth.py", patch="[PATCH] Fix")
    assert edit_res["status"] == "SUCCESS"
    assert edit_res["result"]["applied"] is True
