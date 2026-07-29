import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MissionController:
    def __init__(
        self,
        task_id: str,
        goal: str,
        repo_path: str,
        max_iterations: int = 5,
        token_budget: int = 50000,
        timeout_seconds: int = 300
    ):
        self.task_id = task_id
        self.goal = goal
        self.repo_path = repo_path
        self.max_iterations = max_iterations
        self.token_budget = token_budget
        self.timeout_seconds = timeout_seconds

        self.current_iteration = 0
        self.tokens_used = 0
        self.start_time = time.time()
        self.state = "INITIALIZED"

    def start(self):
        self.state = "RUNNING"
        self.start_time = time.time()
        logger.info(f"MissionController: Started mission [{self.task_id}] -> Goal: {self.goal}")

    def increment_step(self, tokens_in_step: int = 1000) -> bool:
        """Tăng số bước thực thi và kiểm tra ngân sách."""
        self.current_iteration += 1
        self.tokens_used += tokens_in_step

        if self.current_iteration > self.max_iterations:
            self.state = "MAX_ITERATIONS_EXCEEDED"
            logger.warning(f"MissionController: Stopped - Exceeded max iterations ({self.max_iterations})")
            return False

        if self.tokens_used > self.token_budget:
            self.state = "TOKEN_BUDGET_EXCEEDED"
            logger.warning(f"MissionController: Stopped - Exceeded token budget ({self.token_budget})")
            return False

        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            self.state = "TIMEOUT_EXCEEDED"
            logger.warning(f"MissionController: Stopped - Exceeded timeout ({self.timeout_seconds}s)")
            return False

        return True

    def complete(self, success: bool = True):
        self.state = "SUCCESS" if success else "FAILED"
        logger.info(f"MissionController: Completed mission [{self.task_id}] with status {self.state}")

    def is_active(self) -> bool:
        return self.state == "RUNNING"
