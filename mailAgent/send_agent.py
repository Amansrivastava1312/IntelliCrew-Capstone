import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"


def get_pending_employees() -> list[dict]:
    """Return all project allocations whose emails have not been sent."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                pa.*,
                e.full_name AS employee_name
            FROM project_allocation AS pa
            LEFT JOIN employees AS e
                ON e.employee_id = pa.employee_id
            WHERE pa.is_sent = 0
            """
        ).fetchall()

    return [dict(row) for row in rows]


def mark_as_sent(allocation_id: int) -> None:
    """Mark one project-allocation email as successfully sent."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.execute(
            """
            UPDATE project_allocation
            SET is_sent = 1
            WHERE id = ?
            """,
            (allocation_id,),
        )
        conn.commit()
