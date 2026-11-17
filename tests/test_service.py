"""Business-logic and persistence tests (no HTTP layer)."""
import pytest

from app.database import TaskRepository
from app.models import TaskCreate, TaskPriority, TaskStatus, TaskUpdate
from app.service import TaskNotFoundError, TaskService


def make(service, title="Task", **kwargs):
    return service.create_task(TaskCreate(title=title, **kwargs))


def test_create_assigns_id_and_timestamp(service):
    task = make(service, "First")
    assert task.id == 1
    assert task.created_at is not None
    assert task.status == TaskStatus.PENDING


def test_create_persists_all_fields(service, future_date):
    task = make(
        service,
        "Full",
        description="desc",
        status="in_progress",
        priority="high",
        due_date=future_date,
    )
    stored = service.get_task(task.id)
    assert stored.title == "Full"
    assert stored.description == "desc"
    assert stored.status == TaskStatus.IN_PROGRESS
    assert stored.priority == TaskPriority.HIGH
    assert stored.due_date == future_date


def test_list_returns_all_in_id_order(service):
    for name in ("a", "b", "c"):
        make(service, name)
    assert [t.title for t in service.list_tasks()] == ["a", "b", "c"]


def test_list_empty(service):
    assert service.list_tasks() == []


def test_filter_by_status(service):
    make(service, "p1", status="pending")
    make(service, "c1", status="completed")
    make(service, "p2", status="pending")
    make(service, "i1", status="in_progress")
    pending = service.list_tasks(status=TaskStatus.PENDING)
    assert [t.title for t in pending] == ["p1", "p2"]
    assert all(t.status == TaskStatus.PENDING for t in pending)
    completed = service.list_tasks(status=TaskStatus.COMPLETED)
    assert [t.title for t in completed] == ["c1"]


def test_filter_by_priority(service):
    make(service, "low", priority="low")
    make(service, "high1", priority="high")
    make(service, "high2", priority="high")
    high = service.list_tasks(priority=TaskPriority.HIGH)
    assert [t.title for t in high] == ["high1", "high2"]


def test_filter_by_status_and_priority(service):
    make(service, "match", status="pending", priority="high")
    make(service, "wrong_status", status="completed", priority="high")
    make(service, "wrong_priority", status="pending", priority="low")
    result = service.list_tasks(status=TaskStatus.PENDING, priority=TaskPriority.HIGH)
    assert [t.title for t in result] == ["match"]


def test_get_missing_raises(service):
    with pytest.raises(TaskNotFoundError):
        service.get_task(999)


def test_update_changes_only_given_fields(service):
    task = make(service, "Original", description="keep me", priority="low")
    updated = service.update_task(task.id, TaskUpdate(status="completed"))
    assert updated.status == TaskStatus.COMPLETED
    assert updated.title == "Original"
    assert updated.description == "keep me"
    assert updated.priority == TaskPriority.LOW
    assert service.get_task(task.id).status == TaskStatus.COMPLETED


def test_update_multiple_fields(service, future_date):
    task = make(service, "Old")
    updated = service.update_task(
        task.id, TaskUpdate(title="New", priority="high", due_date=future_date)
    )
    assert (updated.title, updated.priority, updated.due_date) == (
        "New",
        TaskPriority.HIGH,
        future_date,
    )


def test_update_can_clear_description(service):
    task = make(service, "t", description="something")
    updated = service.update_task(task.id, TaskUpdate(description=None))
    assert updated.description is None


def test_update_missing_raises(service):
    with pytest.raises(TaskNotFoundError):
        service.update_task(42, TaskUpdate(title="x"))


def test_delete_removes_task(service):
    task = make(service)
    service.delete_task(task.id)
    with pytest.raises(TaskNotFoundError):
        service.get_task(task.id)


def test_delete_missing_raises(service):
    with pytest.raises(TaskNotFoundError):
        service.delete_task(123)


def test_delete_only_removes_target(service):
    keep = make(service, "keep")
    drop = make(service, "drop")
    service.delete_task(drop.id)
    assert [t.id for t in service.list_tasks()] == [keep.id]


def test_data_persists_across_service_instances(db_path):
    TaskService(TaskRepository(db_path)).create_task(TaskCreate(title="durable"))
    reloaded = TaskService(TaskRepository(db_path))
    assert [t.title for t in reloaded.list_tasks()] == ["durable"]
