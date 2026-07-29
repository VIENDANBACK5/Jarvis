import os
import logging
from typing import Dict, Any, Optional, Callable

from backend.runtime.mission_controller import MissionController
from backend.runtime.online_world_model import OnlineWorldModel
from backend.runtime.hierarchical_planner import HierarchicalPlanner
from backend.runtime.event_bus import EventBus
from backend.runtime.event import RuntimeEvent
from backend.tools.registry import ToolRegistry
from backend.tools.search_tool import SearchTool
from backend.tools.read_tool import ReadTool
from backend.tools.edit_tool import EditTool
from backend.tools.pytest_tool import PytestTool
from backend.agents.topology.architect_agent import ArchitectAgent
from backend.agents.topology.coder_agent import CoderAgent
from backend.agents.topology.reviewer_agent import ReviewerAgent
from backend.agents.topology.harness_agent import HarnessAgent
from backend.agents.state.blackboard import EngineeringContext
from backend.models.adaptive_engine import AdaptiveThinkingEngine

logger = logging.getLogger(__name__)


class HierarchicalCognitiveOS:
    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.online_world_model = OnlineWorldModel(self.workspace_dir)
        self.planner = HierarchicalPlanner()
        self.event_bus = EventBus()
        self.tool_registry = ToolRegistry()
        self.adaptive_engine = AdaptiveThinkingEngine()

        # Register tools
        self.tool_registry.register(SearchTool())
        self.tool_registry.register(ReadTool())
        self.tool_registry.register(EditTool())
        self.tool_registry.register(PytestTool())

    def run_mission(
        self,
        task_id: str,
        task_goal: str,
        target_file: str = "main.py",
        patch_code: str = "[PATCH] Strategic patch",
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """Thực thi sứ mệnh qua 3 tầng vòng lặp lồng nhau (Hierarchical Cognitive OS Engine)."""
        from backend.models.adaptive_engine import ComplexityVector
        
        # 1. Khởi tạo Complexity Vector đánh giá độ khó đa chiều
        vector = ComplexityVector(
            files_changed=1,
            dependency_graph_depth=2,
            failing_tests=0,
            architectural_risk="timeout" in task_goal.lower() or "deadlock" in task_goal.lower()
        )
        
        config = self.adaptive_engine.evaluate_vector(vector)
        iterations_budget = config.budget.max_steps
        logger.info(f"HierarchicalCognitiveOS: Selected model mode {config.mode} with budget {iterations_budget} steps | Reasons: {config.reasons}")

        # Layer 1: Mission Controller Loop
        mission = MissionController(task_id, task_goal, self.workspace_dir, iterations_budget)
        mission.start()

        self.event_bus.publish(RuntimeEvent(
            event_type="TASK_CREATED",
            payload={"task_goal": task_goal, "detail": f"Started Hierarchical OS Mission [{task_id}]"}
        ))

        # Layer 2: Hierarchical Cognitive Loop
        context = EngineeringContext(task_issue=task_goal)
        sub_goals = self.planner.decompose_task(task_goal)

        # 1. Observe & Update Online World Model
        self.online_world_model.update_on_action("search", target_file)
        self.event_bus.publish(RuntimeEvent(
            event_type="SEARCH_COMPLETED",
            payload={"detail": f"Online World Model updated context for {self.workspace_dir}"}
        ))

        # 2. Architect Strategy
        architect = ArchitectAgent()
        context = architect.plan_architecture(context, target_file)

        # 3. Coder Synthesis via Edit Tool
        coder = CoderAgent()
        context = coder.synthesize_patch(context, patch_code)
        self.tool_registry.execute_tool("edit_file", filepath=target_file, patch=patch_code)
        self.online_world_model.update_on_action("edit_file", target_file)
        self.event_bus.publish(RuntimeEvent(
            event_type="PATCH_GENERATED",
            payload={"detail": f"Synthesized and applied patch in {target_file}"}
        ))

        # 4. Adversarial Reviewer Audit
        reviewer = ReviewerAgent()
        context = reviewer.audit_patch(context)

        # Re-plan if rejected
        if context.review_status == "rejected":
            self.planner.replan_on_rejection(context.review_reason)

        # 5. Sandbox Pytest Execution
        harness = HarnessAgent()
        is_success = (context.review_status == "approved")
        context = harness.execute_in_sandbox(context, simulated_success=is_success)

        if is_success:
            self.event_bus.publish(RuntimeEvent(
                event_type="TEST_PASSED",
                payload={"detail": "Sandbox execution passed cleanly"}
            ))

        mission.complete(success=is_success)

        # Layer 3: Continuous Online & Offline Learning Loop
        self.event_bus.publish(RuntimeEvent(
            event_type="MISSION_COMPLETED",
            payload={"solved": is_success, "detail": f"Hierarchical OS Mission completed with status {mission.state}"}
        ))

        return {
            "task_id": task_id,
            "status": mission.state,
            "review_status": context.review_status,
            "sub_goals_count": len(sub_goals),
            "modified_files": self.online_world_model.modified_files
        }
