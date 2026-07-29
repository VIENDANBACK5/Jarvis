import pytest
from backend.api.streaming_api import StreamingManager
from backend.runtime.event import RuntimeEvent


def test_streaming_manager():
    manager = StreamingManager()
    assert len(manager.active_connections) == 0

    # Test disconnect safe handling for non-existent session
    manager.disconnect("non-existent-session")
    assert len(manager.active_connections) == 0
