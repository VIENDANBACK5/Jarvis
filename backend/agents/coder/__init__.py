from backend.registry.agent_registry import BaseAgent, get_agent_registry
from backend.services.llm import get_llm
from backend.config import get_prompt


class CoderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="coder-agent",
            capabilities=["read_code", "write_code", "run_tests"]
        )

    async def run(self, task: str, context: dict = None) -> dict:
        """Thực hiện các tác vụ lập trình (coding task)."""
        llm = get_llm()
        system_prompt = get_prompt("coder")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Thực hiện tác vụ coding sau: {task}"}
        ]
        
        response = await llm.ainvoke(messages)
        return {
            "output": response.content,
            "status": "success"
        }


# Đăng ký agent
get_agent_registry().register(CoderAgent())
