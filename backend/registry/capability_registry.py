from typing import List, Set
from backend.registry.agent_registry import get_agent_registry, BaseAgent


class CapabilityRegistry:
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Tìm tất cả các Agent có năng lực phù hợp."""
        registry = get_agent_registry()
        matching_agents = []
        for agent in registry.get_all():
            if capability in agent.capabilities:
                matching_agents.append(agent)
        return matching_agents

    def get_all_capabilities(self) -> Set[str]:
        """Lấy danh sách tất cả các năng lực hiện có trong hệ thống."""
        registry = get_agent_registry()
        capabilities = set()
        for agent in registry.get_all():
            capabilities.update(agent.capabilities)
        return capabilities

    def route_task(self, capability: str) -> BaseAgent:
        """Tìm Agent phù hợp nhất hỗ trợ năng lực được yêu cầu."""
        agents = self.get_agents_by_capability(capability)
        if not agents:
            raise ValueError(f"Không tìm thấy Agent nào hỗ trợ năng lực: '{capability}'")
        # Định tuyến đơn giản (chọn Agent đăng ký trước)
        return agents[0]


# Singleton instance
_capability_registry = CapabilityRegistry()


def get_capability_registry() -> CapabilityRegistry:
    return _capability_registry
