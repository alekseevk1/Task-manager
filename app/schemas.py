from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum
from typing import Optional
from datetime import datetime


class TaskStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskBase(BaseModel):
    title: str = Field(..., max_length=100, description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    status: TaskStatus = Field(TaskStatus.CREATED, description="Статус задачи")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100, description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    status: Optional[TaskStatus] = Field(None, description="Статус задачи")


class Task(TaskBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    success: bool
    data: Task
    message: Optional[str] = None


class TasksResponse(BaseModel):
    success: bool
    data: list[Task]
    count: int
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[dict] = None