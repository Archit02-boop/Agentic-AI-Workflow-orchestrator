from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowCreateRequest(BaseModel):
    goal: str


class WorkflowResponse(BaseModel):
    workflow_id: int
    status: WorkflowStatus
    result: Optional[Any] = None