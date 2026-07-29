import os
import logging
from typing import Dict, Any, Callable, Optional

from backend.runtime.action_history import ActionHistoryTracker
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

logger = logging.getLogger(__name__)


class AgentRuntimeLoop:
    def __init__(self, workspace_dir: str = ".", event_bus: Optional[EventBus] = None):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.history = ActionHistoryTracker()
        self.event_bus = event_bus or EventBus()
        self.tool_registry = ToolRegistry()

        # Đăng ký First-Class Tools
        self.tool_registry.register(SearchTool())
        self.tool_registry.register(ReadTool())
        self.tool_registry.register(EditTool())
        self.tool_registry.register(PytestTool())

        self.context: Optional[EngineeringContext] = None

    def run_loop(
        self,
        task_goal: str,
        target_file: str = "main.py",
        patch_code: str = "[PATCH] Interactive patch synthesis",
        on_step_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """Thực thi vòng lặp hành động - quan sát tương tác (Event-Driven Action-Observation Loop)."""
        self.context = EngineeringContext(task_issue=task_goal)

        # Event: TASK_CREATED
        self.event_bus.publish(RuntimeEvent(
            event_type="TASK_CREATED",
            payload={"task_goal": task_goal, "detail": f"Started task: {task_goal}"}
        ))
        
        # Step 1: Observe & Scan Repo via Tool
        search_res = self.tool_registry.execute_tool("search", query=task_goal)
        self.history.record_step("Observe", self.workspace_dir, f"Scanned repo: {search_res}")
        self.event_bus.publish(RuntimeEvent(
            event_type="SEARCH_COMPLETED",
            payload={"action": "Observe", "detail": f"Scanned repo {self.workspace_dir}"}
        ))
        if on_step_callback:
            on_step_callback({"step": 1, "action": "Observe", "detail": f"Scanned repo {self.workspace_dir}"})

        # Step 2: Architect Plan
        architect = ArchitectAgent()
        self.context = architect.plan_architecture(self.context, target_file)
        self.history.record_step("Architect", target_file, f"Hypothesis: {self.context.current_hypothesis}")
        self.event_bus.publish(RuntimeEvent(
            event_type="FILE_READ",
            payload={"action": "Architect", "detail": f"Identified target {target_file}"}
        ))
        if on_step_callback:
            on_step_callback({"step": 2, "action": "Architect", "detail": f"Identified target {target_file}"})

        # Step 3: Synthesize Patch via Edit Tool
        coder = CoderAgent()
        self.context = coder.synthesize_patch(self.context, patch_code)
        edit_res = self.tool_registry.execute_tool("edit_file", filepath=target_file, patch=patch_code)
        self.history.record_step("Coder", target_file, f"Synthesized patch: {edit_res}")
        self.event_bus.publish(RuntimeEvent(
            event_type="PATCH_GENERATED",
            payload={"action": "Coder", "detail": f"Synthesized patch in {target_file}"}
        ))
        if on_step_callback:
            on_step_callback({"step": 3, "action": "Coder", "detail": f"Synthesized patch in {target_file}"})

        # Step 4: Adversarial Audit & Security Review
        reviewer = ReviewerAgent()
        self.context = reviewer.audit_patch(self.context)
        status_str = "APPROVED" if self.context.review_status == "approved" else "REJECTED"
        self.history.record_step("Reviewer", target_file, f"Audit {status_str}: {self.context.review_reason}")
        if on_step_callback:
            on_step_callback({"step": 4, "action": "Reviewer", "detail": f"Review {status_str}"})

        # Step 5: Test Execution via Pytest Tool
        harness = HarnessAgent()
        is_success = (self.context.review_status == "approved")
        if is_success:
            test_res = self.tool_registry.execute_tool("pytest", test_file=target_file)
            self.context = harness.execute_in_sandbox(self.context, simulated_success=test_res["result"]["passed"])
            self.event_bus.publish(RuntimeEvent(
                event_type="TEST_PASSED",
                payload={"action": "Harness", "detail": "Sandbox tests completed"}
            ))
        else:
            self.context = harness.execute_in_sandbox(self.context, simulated_success=False)

        self.history.record_step("Harness", "pytest", "Sandbox execution passed" if is_success else "Sandbox execution failed")
        if on_step_callback:
            on_step_callback({"step": 5, "action": "Harness", "detail": "Sandbox tests completed"})

        # Event: MISSION_COMPLETED
        self.event_bus.publish(RuntimeEvent(
            event_type="MISSION_COMPLETED",
            payload={"solved": is_success, "detail": "Mission completed"}
        ))

        return {
            "solved": is_success,
            "status": "SUCCESS" if is_success else "FAILED",
            "steps_count": len(self.history.steps),
            "patch": self.context.proposed_patch,
            "history_summary": self.history.get_summary()
        }
