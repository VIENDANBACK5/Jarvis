from typing import Any, Dict
from langgraph.graph import END, StateGraph

from backend.context import ContextBuilder
from backend.graph.state import AgentState
from backend.registry import get_agent_registry, get_capability_registry


async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    """Phân tích ý định của người dùng để quyết định luồng đi (Conversational vs Planning)."""
    messages = state.get("messages") or []
    query = state.get("query")

    if not messages and query:
        messages = [{"role": "user", "content": query}]

    if not messages:
        return {"error": "Không tìm thấy nội dung hội thoại."}

    last_msg = messages[-1]["content"]
    # Kiểm tra xem có yêu cầu lập kế hoạch không
    # Nếu câu hỏi quá ngắn (ví dụ: chào hỏi), ta đi thẳng tới respond.
    if len(last_msg.split()) < 5:
        return {"messages": messages, "metadata": {"need_planning": False}}
    return {"messages": messages, "metadata": {"need_planning": True}}


def route_after_intent(state: AgentState) -> str:
    metadata = state.get("metadata", {})
    if metadata.get("need_planning"):
        return "plan"
    return "respond"


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner Agent phân tích yêu cầu lớn và sinh kế hoạch tổng quan."""
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"]

    # 1. Tích hợp Experience Retrieval từ các task quá khứ
    from backend.learning.retriever import ExperienceRetriever
    retriever = ExperienceRetriever("trajectory/")
    similar_exps = retriever.retrieve_similar_experiences(last_msg, limit=2)
    
    context_str = ""
    if similar_exps:
        context_str += "\n\nKinh nghiệm giải quyết các nhiệm vụ tương tự trong quá khứ:\n"
        for exp in similar_exps:
            context_str += f"- Nhiệm vụ: {exp.goal}\n  Giải pháp thành công: {exp.final_solution.get('patch') if exp.final_solution else 'N/A'}\n"

    registry = get_agent_registry()
    planner = registry.get("planner-agent")

    task_with_exp = last_msg + context_str
    result = await planner.run(task_with_exp)
    return {"plan": result.get("plan")}


async def task_decomposer_node(state: AgentState) -> Dict[str, Any]:
    """Phân rã kế hoạch thành danh sách các subtask cụ thể và gán capability."""
    plan = state.get("plan", "")
    
    # Ở phase cơ bản, ta chia kế hoạch thành 2 subtask mẫu đại diện cho nghiên cứu và lập trình
    subtasks = [
        {"id": 1, "task": f"Tìm kiếm tài liệu học thuật liên quan tới: {plan[:50]}...", "capability": "search_paper"},
        {"id": 2, "task": f"Viết mã nguồn hoặc cấu trúc cho: {plan[:50]}...", "capability": "write_code"}
    ]
    return {"tasks": subtasks, "current_task_index": 0}


async def executor_node(state: AgentState) -> Dict[str, Any]:
    """Thực thi tuần tự từng subtask bằng cách định tuyến động qua Capability Registry."""
    tasks = state.get("tasks", [])
    current_index = state.get("current_task_index", 0)
    agent_outputs = state.get("agent_outputs") or {}

    if current_index >= len(tasks):
        return {}

    subtask = tasks[current_index]
    capability = subtask["capability"]
    task_desc = subtask["task"]

    cap_registry = get_capability_registry()
    try:
        # 1. Định tuyến động lấy Agent dựa trên capability
        agent = cap_registry.route_task(capability)

        # 2. Xây dựng Context sử dụng Context Engine
        builder = ContextBuilder()
        system_context = builder.build_context(state)

        # 3. Gọi Agent thực thi subtask
        output = await agent.run(task_desc, context={"system_context": system_context})
        agent_outputs[agent.name] = output.get("output") or output.get("plan")

        return {
            "agent_outputs": agent_outputs,
            "current_task_index": current_index + 1
        }
    except Exception as e:
        return {"error": f"Lỗi thực thi subtask '{task_desc}': {str(e)}"}


def route_after_execution(state: AgentState) -> str:
    if state.get("error"):
        return "critic"

    tasks = state.get("tasks", [])
    current_index = state.get("current_task_index", 0)

    if current_index < len(tasks):
        return "execute"
    return "reflect"


async def critic_node(state: AgentState) -> Dict[str, Any]:
    """Critic Node bóc tách log lỗi và RCA."""
    from backend.agents.reflection.critic import CriticAgent
    critic = CriticAgent()
    error_msg = state.get("error", "Lỗi thực thi không xác định.")
    diagnosis = await critic.analyze_failure(error_msg)
    return {"diagnosis": diagnosis}


async def decision_node(state: AgentState) -> Dict[str, Any]:
    """Decision Node đưa ra quyết định hành động tiếp theo."""
    from backend.agents.reflection.decision import DecisionAgent
    from backend.learning.strategy_memory import StrategyMemory
    
    current_retry = state.get("retry_count", 0)
    diagnosis = state.get("diagnosis") or {}
    category = diagnosis.get("category", "unknown")
    
    decision_agent = DecisionAgent(max_retries=3)
    action, msg = decision_agent.decide(current_retry, category)
    
    # Điều chỉnh giảm nhẹ trọng số nếu chiến lược đó gây thất bại liên tục
    strategy_mem = StrategyMemory("trajectory/strategy_weights.json")
    if action == "change_strategy":
        current_strategy = strategy_mem.get_best_strategy()
        strategy_mem.update_weights(current_strategy, reward=-0.2)
        
    return {
        "decision_action": action,
        "retry_count": current_retry + 1,
        # Nếu tiếp tục thử lại thì tạm thời xóa flag error để tiếp tục loop
        "error": None if action in ["retry", "change_strategy"] else state.get("error")
    }


def route_after_decision(state: AgentState) -> str:
    action = state.get("decision_action")
    if action in ["retry", "change_strategy"]:
        return "execute"
    return "respond"


async def reflection_node(state: AgentState) -> Dict[str, Any]:
    """Đánh giá, phản hồi kết quả thực thi (Reflection)."""
    # Trả về kết quả đánh giá thành công
    return {"reflection_results": {"status": "passed", "score": 1.0}}


async def memory_update_node(state: AgentState) -> Dict[str, Any]:
    """Cập nhật bộ nhớ trải nghiệm hội thoại (Episodic/Semantic)."""
    # Mô phỏng cập nhật bộ nhớ
    return {}


async def respond_node(state: AgentState) -> Dict[str, Any]:
    """Tổng hợp kết quả cuối cùng từ các Agent và phản hồi tới User."""
    error = state.get("error")
    if error:
        return {"response": f"Lỗi thực thi: {error}", "error": error}

    messages = state.get("messages", [])
    if not messages:
        return {"response": "Lỗi: Không tìm thấy tin nhắn hợp lệ.", "error": "Empty messages"}

    last_msg = messages[-1]["content"]
    agent_outputs = state.get("agent_outputs") or {}
    plan = state.get("plan", "")

    if not plan:
        # Nếu hội thoại ngắn không cần plan, gọi LLM trả lời trực tiếp
        from backend.services.llm import get_llm
        llm = get_llm()
        response = await llm.ainvoke([("user", last_msg)])
        return {"response": response.content}

    # Tổng hợp các output từ Planner & Executor
    summary = []
    summary.append("### Kết quả điều hành hệ thống Jarvis:\n")
    summary.append(f"📋 **Kế hoạch lập ra:** {plan}\n")
    summary.append("⚙️ **Các bước đã thực hiện:**")
    for agent_name, output in agent_outputs.items():
        summary.append(f"\n- **{agent_name}**:\n{output}\n")

    return {"response": "\n".join(summary)}


def build_coordinator_graph(version: str = "v1") -> StateGraph:
    """Xây dựng và biên dịch Đồ thị Điều phối LangGraph."""
    workflow = StateGraph(AgentState)

    # 1. Đăng ký các Node
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("plan", planner_node)
    workflow.add_node("decompose", task_decomposer_node)
    workflow.add_node("execute", executor_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("reflect", reflection_node)
    workflow.add_node("update_memory", memory_update_node)
    workflow.add_node("respond", respond_node)

    # 2. Xây dựng các Edge điều hướng
    workflow.set_entry_point("intent_router")
    
    workflow.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {"plan": "plan", "respond": "respond"}
    )

    workflow.add_edge("plan", "decompose")
    workflow.add_edge("decompose", "execute")

    workflow.add_conditional_edges(
        "execute",
        route_after_execution,
        {
            "execute": "execute",
            "critic": "critic",
            "reflect": "reflect",
            END: END
        }
    )

    workflow.add_edge("critic", "decision")

    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "execute": "execute",
            "respond": "respond"
        }
    )

    workflow.add_edge("reflect", "update_memory")
    workflow.add_edge("update_memory", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()
