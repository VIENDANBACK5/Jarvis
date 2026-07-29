class ContextCompressor:
    """Cắt tỉa và nén ngữ cảnh cũ tránh vượt quá giới hạn token."""

    def compress(self, context: str, max_chars: int = 4000) -> str:
        if len(context) <= max_chars:
            return context
        # Cắt bớt phần ở giữa, giữ lại đầu và cuối
        half_limit = max_chars // 2
        return f"{context[:half_limit]}\n\n... [Đã nén bớt nội dung] ...\n\n{context[-half_limit:]}"
