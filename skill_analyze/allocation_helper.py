from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "employee_records.db"
)


def save_project_allocations(
    project: dict[str, Any],
    employees: list[dict[str, Any]],
    selected_employee_ids: list[str],
    manager_name: str,
) -> dict[str, Any]:
    """Save manager-selected employees to project_allocation."""

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Database file was not found at: {DB_PATH}"
        )

    if not selected_employee_ids:
        raise ValueError("At least one employee must be selected.")

    selected_ids = set(selected_employee_ids)

    selected_employees = [
        employee
        for employee in employees
        if employee["employee_id"] in selected_ids
    ]

    if len(selected_employees) != len(selected_ids):
        raise ValueError(
            "One or more selected employee IDs are invalid."
        )

    saved_records = []
    skipped_records = []

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        for employee in selected_employees:
            existing = connection.execute(
                """
                SELECT id
                FROM project_allocation
                WHERE employee_id = ?
                  AND project_id = ?
                """,
                (
                    employee["employee_id"],
                    project["project_id"],
                ),
            ).fetchone()

            if existing:
                skipped_records.append(
                    {
                        "employee_id": employee["employee_id"],
                        "reason": "Employee is already saved for this project.",
                    }
                )
                continue

            cursor = connection.execute(
                """
                INSERT INTO project_allocation (
                    employee_id,
                    employee_email,
                    project_id,
                    project_name,
                    selection_reason,
                    is_sent,
                    manager_name
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    employee["employee_id"],
                    employee["email"],
                    project["project_id"],
                    project["project_name"],
                    employee["description"],
                    0,
                    manager_name,
                ),
            )

            saved_records.append(
                {
                    "allocation_id": cursor.lastrowid,
                    "employee_id": employee["employee_id"],
                    "employee_name": employee["employee_name"],
                    "project_id": project["project_id"],
                }
            )

        connection.commit()

    return {
        "saved_count": len(saved_records),
        "skipped_count": len(skipped_records),
        "saved_records": saved_records,
        "skipped_records": skipped_records,
    }
