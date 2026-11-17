"""Application configuration."""
import os

DEFAULT_DB_PATH = "tasks.db"


def get_db_path() -> str:
    """Return the SQLite database path (override with TASK_API_DB)."""
    return os.environ.get("TASK_API_DB", DEFAULT_DB_PATH)
