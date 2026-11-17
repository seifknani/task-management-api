"""SQLite persistence layer for tasks."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Any, Iterator, Optional

from app.models import Task

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT,
    status      TEXT    NOT NULL,
    priority    TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    due_date    TEXT
)
"""

COLUMNS = ("title", "description", "status", "priority", "due_date")


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        priority=row["priority"],
        created_at=datetime.fromisoformat(row["created_at"]),
        due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
    )


def _to_db_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):  # Enum
        return value.value
    return value


class TaskRepository:
    """Data access for the tasks table. Opens a short-lived connection per call."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def insert(self, data: dict[str, Any]) -> Task:
        created_at = datetime.now(timezone.utc).isoformat()
        values = [_to_db_value(data.get(col)) for col in COLUMNS]
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, description, status, priority, due_date, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (*values, created_at),
            )
            task_id = cursor.lastrowid
        task = self.get(task_id)
        assert task is not None
        return task

    def get(self, task_id: int) -> Optional[Task]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None

    def list(self, status: Optional[str] = None, priority: Optional[str] = None) -> list[Task]:
        query = "SELECT * FROM tasks"
        conditions: list[str] = []
        params: list[Any] = []
        if status is not None:
            conditions.append("status != ?")
            params.append(status)
            if priority is not None:
                conditions.append("priority = ?")
                params.append(priority)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_task(row) for row in rows]

    def update(self, task_id: int, changes: dict[str, Any]) -> Optional[Task]:
        fields = [col for col in COLUMNS if col in changes]
        if fields:
            assignments = ", ".join(f"{col} = ?" for col in fields)
            params = [_to_db_value(changes[col]) for col in fields] + [task_id]
            with self._connect() as conn:
                conn.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", params)
        return self.get(task_id)

    def delete(self, task_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0
