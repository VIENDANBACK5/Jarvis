import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ExecutionTraceMemory:
    def __init__(self, storage_dir: str):
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.trace_file = os.path.join(self.storage_dir, "trajectories.json")

    def record_trajectory(
        self,
        task_id: str,
        problem: str,
        actions: List[Dict[str, Any]],
        reward: float,
        success: bool
    ):
        """Ghi nhận toàn bộ vết hành động - quan sát (Execution Trace Trajectory)."""
        trajectories = []
        if os.path.exists(self.trace_file):
            try:
                with open(self.trace_file, "r", encoding="utf-8") as f:
                    trajectories = json.load(f)
            except:
                pass

        trajectories.append({
            "task_id": task_id,
            "problem": problem,
            "actions": actions,
            "reward": reward,
            "success": success
        })

        with open(self.trace_file, "w", encoding="utf-8") as f:
            json.dump(trajectories, f, indent=2)

        logger.info(f"ExecutionTraceMemory: Recorded trajectory for task {task_id} (Reward: {reward})")
