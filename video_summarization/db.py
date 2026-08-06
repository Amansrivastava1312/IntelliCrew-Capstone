"""Database helper functions for video summarization logs."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import sqlite3


def get_database_path() -> Path:
    """Find the existing IntelliCrew database without creating a new one."""
    current_dir = Path(__file__).resolve().parent
    candidates = (
        current_dir / "data" / "employee_records.db",
        current_dir.parent / "data" / "employee_records.db",
    )

    for db_path in candidates:
        if db_path.is_file():
            return db_path

    checked_paths = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "employee_records.db was not found. Checked: " + checked_paths
    )




def save_video_summary_log(
    file_path: str,
    summary: str,
    session_id: Any,
) -> int:
    """Execute the insertion of one video summary log and return its ID."""
    source = (file_path or "").strip()
    summary_text = (summary or "").strip()

    if not source:
        raise ValueError("file path or video link is required.")

    if not summary_text:
        raise ValueError("summary is required to save the summary log.")

    db_path = get_database_path()
    #print(session_id)
    with sqlite3.connect(db_path) as connection:
        generated_by =session_id["user_id"]

        cursor = connection.execute(
            """
            INSERT INTO video_summarize_logs
                (file_path, summary, generated_by, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (source, summary_text, generated_by),
        )

        return int(cursor.lastrowid)
