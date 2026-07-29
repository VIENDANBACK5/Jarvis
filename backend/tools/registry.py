import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BaseTool:
    name: str = "base_tool"
    description: str = "Base tool interface"

    def execute(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Tool must implement execute method.")


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Đăng ký một công cụ chuẩn hóa vào Tool Registry."""
        self._tools[tool.name] = tool
        logger.info(f"ToolRegistry: Registered tool [{tool.name}]")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Thực thi công cụ bằng tên với các tham số truyền vào."""
        tool = self.get_tool(name)
        if not tool:
            return {"status": "ERROR", "message": f"Tool '{name}' not found in registry."}
        try:
            res = tool.execute(**kwargs)
            return {"status": "SUCCESS", "result": res}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def list_tools(self) -> List[Dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]
