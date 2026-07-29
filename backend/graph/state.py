from typing import List, Dict, Any, TypedDict


class AgentState(TypedDict, total=False):
    """Trạng thái toàn cục (Global State Schema) cho LangGraph Coordinator."""

    # Lịch sử hội thoại
    messages: List[Dict[str, Any]]
    query: str
    response: str
    
    # Kế hoạch phân rã và danh sách các subtask cần thực hiện
    plan: str
    tasks: List[Dict[str, Any]]
    current_task_index: int

    # Kết quả đầu ra của từng Agent đã chạy
    agent_outputs: Dict[str, Any]

    # Kết quả kiểm chuẩn/đánh giá (Reflection)
    reflection_results: Dict[str, Any]

    # Các thông tin metadata bổ sung khác
    metadata: Dict[str, Any]
    error: str
