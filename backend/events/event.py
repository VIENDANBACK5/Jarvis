import time
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


# Original Event Stream models for backward compatibility
class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{int(time.time() * 1000)}")
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class Action(Event):
    event_type: str = "action"
    action_name: str
    target: str = ""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)


class Observation(Event):
    event_type: str = "observation"
    observation_name: str = ""
    observation_type: str = "info"
    outputs: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True


# Standardized Public Event Types for UI-agnostic API Gateway
class PublicEventType(str, Enum):
    MISSION_STARTED = "MissionStarted"
    MISSION_FINISHED = "MissionFinished"
    FILE_OPENED = "FileOpened"
    FILE_EDITED = "FileEdited"
    PATCH_CREATED = "PatchCreated"
    PATCH_APPROVED = "PatchApproved"
    TOOL_EXECUTED = "ToolExecuted"
    TOOL_FAILED = "ToolFailed"
    MEMORY_RETRIEVED = "MemoryRetrieved"
    WORLD_MODEL_UPDATED = "WorldModelUpdated"


class PublicEvent(BaseModel):
    event_id: str
    session_id: str
    event_type: PublicEventType
    summary: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
