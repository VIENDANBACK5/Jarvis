"""Provider-neutral LLM interface for the agent loop.

The loop only ever sees the normalised events defined here, so swapping the
Anthropic backend for an OpenAI-compatible one changes nothing above this layer.

Message and content-block shapes follow Anthropic's schema (``text``,
``tool_use``, ``tool_result`` blocks) because it is the more expressive of the
two; the OpenAI-compatible backend translates in both directions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Union


class LLMError(Exception):
    """A provider call failed. ``retryable`` marks transient conditions."""

    def __init__(self, message: str, *, retryable: bool = False, status: Optional[int] = None):
        super().__init__(message)
        self.retryable = retryable
        self.status = status


# --------------------------------------------------------------------------- #
# Streamed events
# --------------------------------------------------------------------------- #

@dataclass
class TextChunk:
    """A piece of assistant prose."""
    text: str


@dataclass
class ThinkingChunk:
    """A piece of the model's reasoning, when the provider exposes it."""
    text: str


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0


@dataclass
class ToolCall:
    id: str
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Completion:
    """Terminal event of a stream: the assembled assistant turn.

    ``content`` is the full list of assistant content blocks, suitable for
    appending to history verbatim.
    """
    content: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    text: str = ""
    stop_reason: str = "end_turn"
    usage: TokenUsage = field(default_factory=TokenUsage)


StreamEvent = Union[TextChunk, ThinkingChunk, Completion]


class LLMBackend(ABC):
    """Streams one assistant turn, given history and tool schemas."""

    #: Model identifier, surfaced in the UI and used for cost estimation.
    model: str = ""
    #: Human-readable provider name for error messages.
    provider: str = ""

    @abstractmethod
    def stream(
        self,
        *,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Yield TextChunk/ThinkingChunk events, then exactly one Completion."""
        raise NotImplementedError

    async def close(self) -> None:
        """Release provider resources. Safe to call more than once."""
        return None
