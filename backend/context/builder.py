from typing import Any, Dict, List


class ContextBuilder:
    """Lắp ráp Context từ các nguồn khác nhau."""

    def build_context(self, state: Dict[str, Any]) -> str:
        messages = state.get("messages", [])
        plan = state.get("plan", "")
        agent_outputs = state.get("agent_outputs", {})

        context_parts = []
        if plan:
            context_parts.append(f"### Kế hoạch hiện tại:\n{plan}")

        if agent_outputs:
            context_parts.append("### Kết quả thực thi từ các bước trước:")
            for agent_name, output in agent_outputs.items():
                context_parts.append(f"- **{agent_name}**: {output}")

        if messages:
            context_parts.append("### Cuộc hội thoại gần đây:")
            # Lấy tối đa 5 tin nhắn cuối
            for msg in messages[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context_parts.append(f"- **{role}**: {content}")

        return "\n\n".join(context_parts)
