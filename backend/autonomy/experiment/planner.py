import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ExperimentPlanner:
    def __init__(self):
        pass

    def plan_experiment(self, hypothesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Lập kế hoạch chi tiết các bước thực thi thử nghiệm từ giả thuyết được chọn."""
        hyp_id = hypothesis.get("hypothesis_id", "hyp-unknown")
        target_file = hypothesis.get("target_file", "unknown_file")
        change_content = hypothesis.get("proposed_change", "")

        logger.info(f"ExperimentPlanner: Lập kế hoạch thử nghiệm cho {hyp_id} trên file {target_file}")

        steps = [
            {
                "step_index": 1,
                "action": "create_branch",
                "branch_name": f"experiment/{hyp_id}"
            },
            {
                "step_index": 2,
                "action": "backup_state",
                "target_file": target_file
            },
            {
                "step_index": 3,
                "action": "apply_modification",
                "target_file": target_file,
                "change": change_content
            },
            {
                "step_index": 4,
                "action": "run_benchmark"
            },
            {
                "step_index": 5,
                "action": "statistical_validate"
            }
        ]
        return steps
