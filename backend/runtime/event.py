import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RuntimeEvent(BaseModel):
    event_type: str = Field(..., description="Loại sự kiện: TASK_CREATED | FILE_READ | SEARCH_COMPLETED | PATCH_GENERATED | TEST_PASSED | MISSION_COMPLETED")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Dữ liệu truyền kèm sự kiện.")
    timestamp: float = Field(default_factory=time.time, description="Dấu thời gian phát sự kiện.")
