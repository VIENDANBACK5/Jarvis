from abc import ABC, abstractmethod
from typing import Dict, List


class BaseAgent(ABC):
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities

    @abstractmethod
    async def run(self, task: str, context: dict = None) -> dict:
        """Thực thi nhiệm vụ được giao."""
        pass


class AgentRegistry:
    def __init__(self):
        self._registry: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """Đăng ký Agent vào hệ thống."""
        if agent.name in self._registry:
            raise ValueError(f"Agent '{agent.name}' đã tồn tại trong Registry.")
        self._registry[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        """Lấy Agent theo tên."""
        if name not in self._registry:
            raise KeyError(f"Agent '{name}' không tồn tại trong Registry.")
        return self._registry[name]

    def list(self) -> List[str]:
        """Liệt kê danh sách tên các Agent đã đăng ký."""
        return list(self._registry.keys())

    def get_all(self) -> List[BaseAgent]:
        """Lấy tất cả các Agent đã đăng ký."""
        return list(self._registry.values())


# Singleton registry instance
_agent_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    return _agent_registry
