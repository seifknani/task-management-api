"""Validation tests for task models."""
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.models import TaskCreate, TaskPriority, TaskStatus, TaskUpdate


def test_defaults_applied():
    task = TaskCreate(title="Write report")
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM
    assert task.description is None
    assert task.due_date is None


def test_title_is_trimmed():
    assert TaskCreate(title="  Buy milk  ").title == "Buy milk"


@pytest.mark.parametrize("title", ["", "   "])
def test_blank_title_rejected(title):
    with pytest.raises(ValidationError):
        TaskCreate(title=title)


def test_title_too_long_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="x" * 201)


def test_title_max_length_accepted():
    assert len(TaskCreate(title="x" * 200).title) == 200


def test_description_too_long_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="ok", description="d" * 2001)


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="ok", status="done")


def test_invalid_priority_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="ok", priority="urgent")


def test_past_due_date_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="ok", due_date=date.today() - timedelta(days=1))


def test_today_due_date_accepted():
    assert TaskCreate(title="ok", due_date=date.today()).due_date == date.today()


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="ok", owner="bob")


def test_empty_update_rejected():
    with pytest.raises(ValidationError):
        TaskUpdate()


def test_update_null_title_rejected():
    with pytest.raises(ValidationError):
        TaskUpdate(title=None)


def test_update_null_status_rejected():
    with pytest.raises(ValidationError):
        TaskUpdate(status=None)


def test_update_tracks_only_set_fields():
    update = TaskUpdate(status="completed")
    assert update.model_dump(exclude_unset=True) == {"status": TaskStatus.COMPLETED}
