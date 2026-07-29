import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.graph.state import AgentState
from backend.graph.coordinator import (
    route_after_execution,
    route_after_decision,
    critic_node,
    decision_node,
    planner_node
)
from backend.learning.retriever import ExperienceRetriever
from backend.learning.strategy_memory import StrategyMemory
from backend.learning.experience import Experience, ExperienceStore


def test_experience_retriever(tmp_path):
    retriever = ExperienceRetriever(str(tmp_path))
    
    # Tạo các kinh nghiệm mẫu quá khứ
    exp1 = Experience(
        task_id="task-1",
        goal="Fix memory leak in flask app cache connection",
        reward=0.8
    )
    exp2 = Experience(
        task_id="task-2",
        goal="Sửa lỗi giao diện CSS căn lề navbar",
        reward=0.9
    )
    
    retriever.store.save_experience(exp1)
    retriever.store.save_experience(exp2)

    # Lọc tìm kiếm theo từ khóa
    matches = retriever.retrieve_similar_experiences("flask cache memory leak")
    assert len(matches) == 1
    assert matches[0].task_id == "task-1"


def test_strategy_memory(tmp_path):
    db_file = tmp_path / "strategy_weights.json"
    strategy_mem = StrategyMemory(str(db_file))

    # Lấy chiến lược tốt nhất mặc định
    best = strategy_mem.get_best_strategy()
    assert best == "modify_logic"

    # Giảm trọng số của modify_logic
    strategy_mem.update_weights("modify_logic", reward=-0.5)
    
    # Nạp lại bộ nhớ
    new_mem = StrategyMemory(str(db_file))
    assert new_mem.weights["modify_logic"] < 0.6


@pytest.mark.asyncio
async def test_critic_and_decision_nodes(tmp_path):
    state: AgentState = {
        "error": "AssertionError: expected 10 got 12",
        "retry_count": 2,
        "diagnosis": {"category": "logic_error"}
    }

    # 1. Chạy thử critic_node
    res_critic = await critic_node(state)
    assert "diagnosis" in res_critic

    # 2. Chạy thử decision_node với Mock StrategyMemory
    mock_strategy_mem = MagicMock()
    mock_strategy_mem.get_best_strategy.return_value = "modify_logic"

    with patch("backend.learning.strategy_memory.StrategyMemory", return_value=mock_strategy_mem):
        res_decision = await decision_node(state)
        
        assert res_decision["decision_action"] == "change_strategy"
        assert res_decision["retry_count"] == 3
        mock_strategy_mem.update_weights.assert_called_once_with("modify_logic", reward=-0.2)


def test_graph_routing_flow():
    # 1. Chạy thành công -> Đi tiếp đến reflect
    state_ok: AgentState = {
        "error": None,
        "tasks": [{"id": 1, "capability": "write_code"}],
        "current_task_index": 1
    }
    assert route_after_execution(state_ok) == "reflect"

    # 2. Chạy lỗi -> Định tuyến sang critic
    state_err: AgentState = {
        "error": "AssertionError",
        "tasks": [{"id": 1, "capability": "write_code"}],
        "current_task_index": 0
    }
    assert route_after_execution(state_err) == "critic"

    # 3. Decision chọn retry -> Quay lại execute
    state_retry: AgentState = {
        "decision_action": "retry"
    }
    assert route_after_decision(state_retry) == "execute"

    # 4. Decision chọn abort -> Dừng chuyển giao respond
    state_abort: AgentState = {
        "decision_action": "abort"
    }
    assert route_after_decision(state_abort) == "respond"


@pytest.mark.asyncio
async def test_planner_node_with_retrieval(tmp_path):
    state: AgentState = {
        "messages": [{"role": "user", "content": "Fix flask memory leak"}]
    }

    mock_planner = MagicMock()
    mock_planner.run = AsyncMock(return_value={"plan": "Mocked Plan"})
    
    # Tạo kinh nghiệm flask tương tự
    exp = Experience(
        task_id="task-flask-old",
        goal="Fix memory leak in flask app cache connection",
        final_solution={"patch": "diff patch logic"},
        reward=0.9
    )
    
    mock_retriever = MagicMock()
    mock_retriever.retrieve_similar_experiences.return_value = [exp]
    
    with patch("backend.learning.retriever.ExperienceRetriever", return_value=mock_retriever), \
         patch("backend.graph.coordinator.get_agent_registry") as mock_registry:
             
        mock_registry.return_value.get.return_value = mock_planner

        res = await planner_node(state)
        assert res["plan"] == "Mocked Plan"
        
        # Xác minh Planner nhận được thông tin kinh nghiệm quá khứ từ Retriever
        called_args = mock_planner.run.call_args[0][0]
        assert "Kinh nghiệm giải quyết các nhiệm vụ tương tự" in called_args
        assert "Fix memory leak in flask app cache connection" in called_args
