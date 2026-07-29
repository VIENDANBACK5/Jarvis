from backend.registry.agent_registry import BaseAgent, get_agent_registry
from backend.services.llm import get_llm
from backend.config import get_prompt


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="planner-agent",
            capabilities=["plan_tasks", "decompose_tasks"]
        )

    async def run(self, task: str, context: dict = None) -> dict:
        """Lập kế hoạch phân rã công việc sử dụng LLM."""
        llm = get_llm()
        system_prompt = get_prompt("planner")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Hãy lập kế hoạch phân rã tác vụ sau: {task}"}
        ]
        
        response = await llm.ainvoke(messages)
        plan_content = response.content
        
        # Một parser kế hoạch đơn giản (ví dụ)
        return {
            "plan": plan_content,
            "status": "success"
        }


# Tự động đăng ký agent khi module được import
get_agent_registry().register(PlannerAgent())
