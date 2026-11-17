"""Shared pytest fixtures."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import TaskRepository  # noqa: E402
from app.service import TaskService  # noqa: E402


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "test_tasks.db")


@pytest.fixture
def service(db_path) -> TaskService:
    return TaskService(TaskRepository(db_path))


@pytest.fixture
def future_date() -> date:
    return date.today() + timedelta(days=7)


@pytest.fixture
def client(db_path):
    """HTTP test client. Skipped automatically if FastAPI/httpx are not installed."""
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app(db_path)) as test_client:
        yield test_client
