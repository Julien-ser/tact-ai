from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Quadrant(str):
    IMPORTANT_URGENT = "important_urgent"
    IMPORTANT_NOT_URGENT = "important_not_urgent"
    NOT_IMPORTANT_URGENT = "not_important_urgent"
    NOT_IMPORTANT_NOT_URGENT = "not_important_not_urgent"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    estimated_duration_minutes: int = Field(default=60, ge=15, le=480)
    deadline: Optional[datetime] = None
    dependencies: List[str] = Field(default_factory=list)  # task IDs
    priority: int = Field(default=3, ge=1, le=5)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    estimated_duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    deadline: Optional[datetime] = None
    dependencies: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    quadrant: Optional[Quadrant] = None


class TaskResponse(TaskBase):
    id: str
    user_id: str
    quadrant: Quadrant
    created_at: datetime
    updated_at: Optional[datetime] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskChain(BaseModel):
    """Represents a sequence of dependent tasks"""

    tasks: List[TaskResponse]
    total_duration_minutes: int
    earliest_start: datetime
    latest_end: datetime


class ConflictReport(BaseModel):
    task_id: str
    conflict_type: str  # "overlap", "resource_overload", "missed_deadline"
    description: str
    conflicting_tasks: List[str]
    suggested_resolution: Optional[str] = None


class ScheduleResponse(BaseModel):
    tasks: List[TaskResponse]
    conflicts: List[ConflictReport]
    unscheduled_tasks: List[str]
    total_duration_minutes: int
    schedule_metadata: dict


class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
