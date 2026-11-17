"""FastAPI application: HTTP layer only."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status as http_status

from app.config import get_db_path
from app.database import TaskRepository
from app.models import Task, TaskCreate, TaskPriority, TaskStatus, TaskUpdate
from app.service import TaskNotFoundError, TaskService


def create_app(db_path: Optional[str] = None) -> FastAPI:
    app = FastAPI(
        title="Task Management API",
        version="1.0.0",
        description="Simple task manager used as the RepoPilot target repository.",
    )
    app.state.service = TaskService(TaskRepository(db_path or get_db_path()))

    def get_service(request: Request) -> TaskService:
        return request.app.state.service

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/tasks", response_model=Task, status_code=http_status.HTTP_201_CREATED)
    def create_task(payload: TaskCreate, service: TaskService = Depends(get_service)) -> Task:
        return service.create_task(payload)

    @app.get("/tasks", response_model=list[Task])
    def list_tasks(
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        service: TaskService = Depends(get_service),
    ) -> list[Task]:
        return service.list_tasks(status=status, priority=priority)

    @app.get("/tasks/{task_id}", response_model=Task)
    def get_task(task_id: int, service: TaskService = Depends(get_service)) -> Task:
        try:
            return service.get_task(task_id)
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.patch("/tasks/{task_id}", response_model=Task)
    def update_task(
        task_id: int, payload: TaskUpdate, service: TaskService = Depends(get_service)
    ) -> Task:
        return service.update_task(task_id, payload)

    @app.delete("/tasks/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
    def delete_task(task_id: int, service: TaskService = Depends(get_service)) -> Response:
        try:
            service.delete_task(task_id)
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return Response(status_code=http_status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
