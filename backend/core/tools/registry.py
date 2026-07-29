"""Tool registry: schema export for the model, dispatch for the loop."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.core.tools.base import Tool, ToolContext, ToolError, ToolResult
from backend.core.tools.bash import BashTool
from backend.core.tools.edit import EditTool
from backend.core.tools.glob import GlobTool
from backend.core.tools.grep import GrepTool
from backend.core.tools.read import ReadTool
from backend.core.tools.todo import TodoTool
from backend.core.tools.write import WriteTool

logger = logging.getLogger(__name__)


class ToolBox:
    """The set of tools available to one session."""

    def __init__(self, tools: Optional[List[Tool]] = None) -> None:
        self._tools: Dict[str, Tool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError(f"{type(tool).__name__} has no name.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return list(self._tools)

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def schemas(self) -> List[Dict[str, Any]]:
        """Tool definitions in Anthropic's format.

        The OpenAI-compatible backend reshapes these itself, so this stays the
        single source of truth for names, descriptions and argument schemas.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    async def execute(
        self, name: str, args: Dict[str, Any], ctx: ToolContext
    ) -> ToolResult:
        """Run a tool, converting failures into results the model can read.

        A tool that raises must not kill the turn -- the model's next step is
        usually to read the error and try something else.
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                content=(
                    f"No tool named '{name}'. Available tools: "
                    f"{', '.join(sorted(self._tools))}."
                ),
                is_error=True,
            )

        if not isinstance(args, dict):
            return ToolResult(
                content=f"Arguments for '{name}' must be a JSON object.",
                is_error=True,
            )

        try:
            return await tool.run(args, ctx)
        except ToolError as exc:
            # Expected, actionable failure.
            return ToolResult(content=str(exc), is_error=True)
        except Exception as exc:  # noqa: BLE001 - surface anything to the model
            logger.exception("Tool %s crashed", name)
            return ToolResult(
                content=f"{name} failed unexpectedly: {type(exc).__name__}: {exc}",
                is_error=True,
            )


def default_toolbox(bash_timeout: int = 120) -> ToolBox:
    """The standard Jarvis tool set."""
    return ToolBox([
        ReadTool(),
        WriteTool(),
        EditTool(),
        BashTool(default_timeout=bash_timeout),
        GlobTool(),
        GrepTool(),
        TodoTool(),
    ])
