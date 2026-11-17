# Task Management API

Small FastAPI + SQLite service used as the target repository for RepoPilot.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# Swagger UI: http://127.0.0.1:8000/docs
```

Set `TASK_API_DB=/path/to/file.db` to choose the database file (default `tasks.db`).

## Test

```bash
pytest
```

## Endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET | /health | liveness |
| POST | /tasks | create (201) |
| GET | /tasks?status=&priority= | list, optional filters |
| GET | /tasks/{id} | 404 if missing |
| PATCH | /tasks/{id} | partial update |
| DELETE | /tasks/{id} | 204 |

Status: `pending`, `in_progress`, `completed`. Priority: `low`, `medium`, `high`.
