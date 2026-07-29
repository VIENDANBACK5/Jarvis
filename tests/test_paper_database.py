import pytest
from backend.autonomy.research.research_agent import ResearchAgent


def test_paper_database_retrieval(tmp_path):
    db_file = tmp_path / "papers.json"
    agent = ResearchAgent(str(db_file))

    # 1. Kiểm thử trùng mẫu lỗi wrong_tool_selection -> ReAct paper
    proposal1 = agent.conduct_research(
        failure_pattern="wrong_tool_selection",
        failure_count=5,
        target_filepath="backend/graph/planner.py"
    )
    assert "react_2022" in proposal1.related_research or "ReAct" in proposal1.related_research
    assert proposal1.confidence_calibration == 0.86

    # 2. Kiểm thử trùng mẫu lỗi code_patch_fail -> Self-Refine paper
    proposal2 = agent.conduct_research(
        failure_pattern="code_patch_fail",
        failure_count=3,
        target_filepath="backend/graph/planner.py"
    )
    assert "self_refine_2023" in proposal2.related_research or "Self-Refine" in proposal2.related_research
    assert proposal2.confidence_calibration == 0.90
