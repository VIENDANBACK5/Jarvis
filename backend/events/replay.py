import logging
from typing import List, Dict, Any

from backend.events.stream import EventStream

logger = logging.getLogger(__name__)


class ActionReplay:
    @staticmethod
    def print_timeline(stream: EventStream) -> str:
        """Sinh ra chuỗi timeline trực quan mô tả chuỗi hành động và phản hồi đã thực thi."""
        timeline = []
        events = stream.get_events()
        
        timeline.append("=== JARVIS ACTION REPLAY TIMELINE ===")
        
        for idx, evt in enumerate(events, 1):
            t_str = time_format = f"[{evt.timestamp:.2f}]"
            
            if evt.event_type == "action":
                timeline.append(
                    f"{idx}. 🚀 ACTION: {evt.action_name} | Inputs: {evt.inputs}"
                )
            elif evt.event_type == "observation":
                timeline.append(
                    f"{idx}. 👁️ OBSERVATION: {evt.observation_name} | Outputs: {evt.outputs}"
                )
            else:
                timeline.append(
                    f"{idx}. 🔔 EVENT: {evt.event_type}"
                )
                
        timeline.append("=====================================")
        return "\n".join(timeline)

    @staticmethod
    def get_summary_stats(stream: EventStream) -> Dict[str, Any]:
        """Tóm tắt thống kê nhanh về các công cụ được Agent sử dụng trong trajectory."""
        events = stream.get_events()
        actions = [e for e in events if e.event_type == "action"]
        observations = [e for e in events if e.event_type == "observation"]

        tool_counts = {}
        for act in actions:
            name = act.action_name
            tool_counts[name] = tool_counts.get(name, 0) + 1

        return {
            "total_events": len(events),
            "total_actions": len(actions),
            "total_observations": len(observations),
            "tool_calls": tool_counts
        }
