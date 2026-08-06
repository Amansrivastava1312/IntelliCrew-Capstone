"""Raw SQLite helper to save selected employees into project_allocation — no ORM class, just functions."""
import sqlite3
from pathlib import Path


# this file sits inside skill_analyze/, so go up ONE level to reach project root, then data/
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"   # ✅ matches data_seed.py


def get_conn():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def save_project_allocations(project_id, selected_employees, manager_name):
    """
    Insert ONLY the selected employees into project_allocation,
    and mark each saved employee's status as 'Allocated' in employees table.
    """

    if not selected_employees:
        raise ValueError("At least one employee must be selected.")

    conn = get_conn()
    cur = conn.cursor()

    project = cur.execute(
        "SELECT project_id, project_name FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()

    if not project:
        conn.close()
        raise ValueError("Project not found.")

    saved_records = []
    skipped_records = []

    for employee in selected_employees:
        employee_id = employee.get("employee_id")
        rank = employee.get("rank")
        matching_percentage = employee.get("matching_percentage")
        description = employee.get("description")          # full reason text

        emp_row = cur.execute(
            "SELECT employee_id, full_name, email FROM employees WHERE employee_id = ?",
            (employee_id,),
        ).fetchone()

        if not emp_row:
            skipped_records.append(
                {"employee_id": employee_id, "reason": "Employee not found."}
            )
            continue

        existing = cur.execute(
            "SELECT id FROM project_allocation WHERE employee_id = ? AND project_id = ?",
            (employee_id, project_id),
        ).fetchone()

        if existing:
            skipped_records.append(
                {"employee_id": employee_id, "reason": "Already allocated to this project."}
            )
            continue

        # save the FULL description as the reason; fall back if empty
        if description and description.strip():
            selection_reason = description.strip()
        elif rank is not None and matching_percentage is not None:
            selection_reason = f"Rank {rank} | Match {matching_percentage}%"
        else:
            selection_reason = "Selected by manager from project matching."

        # 1. insert allocation row
        cur.execute(
            """INSERT INTO project_allocation
               (employee_id, employee_email, project_id, project_name,
                selection_reason, is_sent, manager_name)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                emp_row["employee_id"],
                emp_row["email"],
                project["project_id"],
                project["project_name"],
                selection_reason,
                0,
                manager_name,
            ),
        )

        allocation_id = cur.lastrowid

        # 2. 👇 mark this employee as Allocated in employees table
        cur.execute(
            """UPDATE employees
               SET status = 'Allocated',
                   updated_at = datetime('now')
               WHERE employee_id = ?""",
            (emp_row["employee_id"],),
        )

        saved_records.append(
            {
                "allocation_id": allocation_id,
                "employee_id": emp_row["employee_id"],
                "employee_name": emp_row["full_name"],
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "status": "Allocated",
            }
        )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Employee allocation saved successfully.",
        "saved_count": len(saved_records),
        "skipped_count": len(skipped_records),
        "saved_records": saved_records,
        "skipped_records": skipped_records,
    }