"""LLM backends for the agent loop.

Only the provider-neutral types are re-exported here. ``factory`` is imported
explicitly by callers because it pulls in application settings, and this package
should stay importable from tests without any configuration present.
"""

from backend.core.llm.base import (
    Completion,
    LLMBackend,
    LLMError,
    StreamEvent,
    TextChunk,
    ThinkingChunk,
    TokenUsage,
    ToolCall,
)

__all__ = [
    "Completion",
    "LLMBackend",
    "LLMError",
    "StreamEvent",
    "TextChunk",
    "ThinkingChunk",
    "TokenUsage",
    "ToolCall",
]
