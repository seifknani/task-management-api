"""Business logic for task management."""
from __future__ import annotations

from typing import Optional

from app.database import TaskRepository
from app.models import Task, TaskCreate, TaskPriority, TaskStatus, TaskUpdate


class TaskNotFoundError(Exception):
    """Raised when a task id does not exist."""

    def __init__(self, task_id: int) -> None:
        super().__init__(f"Task {task_id} not found")
        self.task_id = task_id


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(self, payload: TaskCreate) -> Task:
        return self.repository.insert(payload.model_dump())

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
    ) -> list[Task]:
        return self.repository.list(
            status=status.value if status else None,
            priority=priority.value if priority else None,
        )

    def get_task(self, task_id: int) -> Task:
        task = self.repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def update_task(self, task_id: int, payload: TaskUpdate) -> Task:
        self.get_task(task_id)  # raises if missing
        changes = payload.model_dump()
        task = self.repository.update(task_id, changes)
        assert task is not None
        return task

    def delete_task(self, task_id: int) -> None:
        if not self.repository.delete(task_id):
            raise TaskNotFoundError(task_id)
