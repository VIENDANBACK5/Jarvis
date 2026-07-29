import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TelemetryTracker:
    def __init__(self):
        # Lưu trữ lịch sử hoạt động dạng: {task_id: [events]}
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def start_action(self) -> float:
        """Ghi nhận thời điểm bắt đầu hành động."""
        return time.time()

    def log_action(
        self,
        task_id: str,
        agent_id: str,
        tool_name: str,
        start_time: float,
        success: bool,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost_usd: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ghi nhận thông số chi tiết của hành động vào telemetry."""
        latency = time.time() - start_time
        
        event = {
            "agent_id": agent_id,
            "tool_name": tool_name,
            "latency_seconds": latency,
            "success": success,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }

        if task_id not in self._sessions:
            self._sessions[task_id] = []
        self._sessions[task_id].append(event)

        logger.info(
            f"Telemetry: Task {task_id} | Agent {agent_id} | Tool {tool_name} | "
            f"Success: {success} | Latency: {latency:.3f}s | Cost: ${cost_usd:.6f}"
        )
        return event

    def get_session_events(self, task_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(task_id, [])

    def get_summary(self, task_id: str) -> Dict[str, Any]:
        """Tóm tắt tổng quan mức tiêu hao của task_id."""
        events = self.get_session_events(task_id)
        if not events:
            return {"total_actions": 0, "total_latency": 0.0, "total_tokens": 0, "total_cost_usd": 0.0}

        return {
            "total_actions": len(events),
            "total_latency": sum(e["latency_seconds"] for e in events),
            "total_tokens": sum(e["tokens_in"] + e["tokens_out"] for e in events),
            "total_cost_usd": sum(e["cost_usd"] for e in events),
            "success_rate": sum(1 for e in events if e["success"]) / len(events)
        }


# Singleton instance
_telemetry_tracker = TelemetryTracker()


def get_telemetry_tracker() -> TelemetryTracker:
    return _telemetry_tracker
