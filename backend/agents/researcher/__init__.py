from backend.registry.agent_registry import BaseAgent, get_agent_registry
from backend.services.llm import get_llm
from backend.config import get_prompt


class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="researcher-agent",
            capabilities=["search_paper", "summarize_paper", "gap_analysis"]
        )

    async def run(self, task: str, context: dict = None) -> dict:
        """Thực hiện các nghiên cứu học thuật."""
        llm = get_llm()
        system_prompt = get_prompt("researcher")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Thực hiện nghiên cứu sau: {task}"}
        ]
        
        response = await llm.ainvoke(messages)
        return {
            "output": response.content,
            "status": "success"
        }


# Đăng ký agent
get_agent_registry().register(ResearcherAgent())
