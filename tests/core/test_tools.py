from pathlib import Path
import pytest
from backend.core.tools.read import ReadTool
from backend.core.tools.write import WriteTool
from backend.core.tools.edit import EditTool
from backend.core.tools.bash import BashTool
from backend.core.tools.glob import GlobTool
from backend.core.tools.grep import GrepTool
from backend.core.tools.todo import TodoTool
from backend.core.tools.base import ToolContext


@pytest.mark.asyncio
async def test_real_tools_execution(tmp_path):
    ws = Path(tmp_path)
    ctx = ToolContext(workspace=ws, cwd=ws)

    # 1. Write Tool
    write_tool = WriteTool()
    res_w = await write_tool.run({"path": "test.txt", "content": "hello world"}, ctx)
    assert res_w.is_error is False

    # 2. Read Tool
    read_tool = ReadTool()
    res_r = await read_tool.run({"path": "test.txt"}, ctx)
    assert "hello world" in res_r.content

    # 3. Edit Tool
    edit_tool = EditTool()
    res_e = await edit_tool.run({"path": "test.txt", "old_string": "world", "new_string": "jarvis"}, ctx)
    assert res_e.is_error is False

    # Verify Edit
    res_r2 = await read_tool.run({"path": "test.txt"}, ctx)
    assert "hello jarvis" in res_r2.content

    # 4. Glob Tool
    glob_tool = GlobTool()
    res_g = await glob_tool.run({"pattern": "*.txt"}, ctx)
    assert "test.txt" in res_g.content

    # 5. Grep Tool
    grep_tool = GrepTool()
    res_gr = await grep_tool.run({"pattern": "jarvis"}, ctx)
    assert "test.txt" in res_gr.content

    # 6. Bash Tool
    bash_tool = BashTool()
    res_b = await bash_tool.run({"command": "echo 'running bash'"}, ctx)
    assert "running bash" in res_b.content

    # 7. Todo Tool
    todo_tool = TodoTool()
    res_t = await todo_tool.run({"todos": [{"content": "Build AI agent", "status": "pending"}]}, ctx)
    assert "Build AI agent" in res_t.content
