from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


# skill_match.py is inside agent/, while data/ is in the project root.
DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "employee_records.db"
)


def normalize(skill: str) -> str:
    """Normalize a skill name for comparison."""
    return " ".join(skill.strip().casefold().split())


def get_matches(project_id: int) -> dict[str, Any]:
    """
    Fetch a project's required skills, compare them with every employee's
    skills, and return employees sorted by highest matching percentage.
    """

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Database file was not found at: {DB_PATH}"
        )

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")

        # Fetch the selected project.
        project = connection.execute(
            """
            SELECT
                project_id,
                project_name,
                client,
                required_skills,
                status
            FROM projects
            WHERE project_id = ?
            """,
            (project_id,),
        ).fetchone()

        if project is None:
            raise ValueError(
                f"Project ID {project_id} was not found."
            )

        # Convert comma-separated required skills into a normalized set.
        required_skills = {
            normalize(skill)
            for skill in (project["required_skills"] or "").split(",")
            if skill.strip()
        }

        if not required_skills:
            raise ValueError(
                f"Project ID {project_id} has no required skills."
            )

        # Fetch only active employees and their skills.
        rows = connection.execute(
            """
            SELECT
                e.employee_id,
                e.full_name,
                e.email,
                s.skill_name
            FROM employees AS e
            LEFT JOIN employee_skills AS es
                ON es.employee_id = e.employee_id
            LEFT JOIN skills AS s
                ON s.skill_id = es.skill_id
            WHERE LOWER(TRIM(e.status)) = 'active'
            ORDER BY e.employee_id
            """
        ).fetchall()

        # Group skills employee-wise.
        employees: dict[str, dict[str, Any]] = {}

        for row in rows:
            employee_id = row["employee_id"]

            if employee_id not in employees:
                employees[employee_id] = {
                    "employee_id": employee_id,
                    "full_name": row["full_name"],
                    "email": row["email"],
                    "skills": set(),
                }

            if row["skill_name"]:
                employees[employee_id]["skills"].add(
                    normalize(row["skill_name"])
                )

        results: list[dict[str, Any]] = []
        total_required = len(required_skills)

        # Compare every employee with the selected project.
        for employee in employees.values():
            employee_skills = employee["skills"]

            matched_skills = employee_skills & required_skills
            missing_skills = required_skills - employee_skills

            matched_count = len(matched_skills)

            match_percentage = round(
                matched_count / total_required * 100,
                2,
            )

            results.append(
                {
                    "employee_id": employee["employee_id"],
                    "full_name": employee["full_name"],
                    "email": employee["email"],
                    "matched_count": matched_count,
                    "required_count": total_required,
                    "match_percentage": match_percentage,
                    "matched_skills": sorted(matched_skills),
                    "missing_skills": sorted(missing_skills),
                }
            )

        # Sort by highest percentage first.
        results.sort(
            key=lambda item: (
                -item["match_percentage"],
                -item["matched_count"],
                item["employee_id"],
            )
        )

        # Assign rank after sorting.
        for rank, employee in enumerate(results, start=1):
            employee["rank"] = rank

        return {
            "project": {
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "client": project["client"],
                "status": project["status"],
                "required_skills": sorted(required_skills),
                "required_skill_count": total_required,
            },
            "total_employees": len(results),
            "matches": results,
        }


if __name__ == "__main__":
    from pprint import pprint

    result = get_matches(project_id=2)
    pprint(result, sort_dicts=False)