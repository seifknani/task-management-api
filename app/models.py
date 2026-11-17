"""Pydantic data models for tasks."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _clean_title(value: str) -> str:
    if not value:
        raise ValueError("title must not be blank")
    value = value.strip()
    if len(value) > TITLE_MAX_LENGTH:
        raise ValueError(f"title must be at most {TITLE_MAX_LENGTH} characters")
    return value


def _check_due_date(value: Optional[date]) -> Optional[date]:
    if value is not None and value < date.today():
        raise ValueError("due_date must not be in the past")
    return value


class TaskCreate(BaseModel):
    """Payload for creating a task."""

    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _clean_title(value)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: Optional[date]) -> Optional[date]:
        return _check_due_date(value)


class TaskUpdate(BaseModel):
    """Payload for partially updating a task. Only provided fields change."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            raise ValueError("title cannot be null")
        return _clean_title(value)

    @field_validator("status", "priority")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: Optional[date]) -> Optional[date]:
        return _check_due_date(value)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "TaskUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class Task(BaseModel):
    """A stored task."""

    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    due_date: Optional[date]
