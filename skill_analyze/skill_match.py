import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "employee_records.db"


def normalize(skill):
    return " ".join(skill.strip().casefold().split())


def get_matches(project_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get the project
    project = conn.execute(
        "SELECT project_id, project_name, client, required_skills, status "
        "FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()

    if project is None:
        raise ValueError(f"Project ID {project_id} not found.")

    # Build the required skills set
    required = set()
    for skill in (project["required_skills"] or "").split(","):
        if skill.strip():
            required.add(normalize(skill))

    total = len(required)

    # Get all active employees with their skills
    rows = conn.execute(
        """
        SELECT e.employee_id, e.full_name, e.email, s.skill_name
        FROM employees e
        LEFT JOIN employee_skills es ON es.employee_id = e.employee_id
        LEFT JOIN skills s ON s.skill_id = es.skill_id
        WHERE LOWER(TRIM(e.status)) = 'active'
        """
    ).fetchall()
    conn.close()

    # Group skills per employee
    employees = {}
    for row in rows:
        emp_id = row["employee_id"]

        if emp_id not in employees:
            employees[emp_id] = {
                "employee_id": emp_id,
                "full_name": row["full_name"],
                "email": row["email"],
                "skills": set(),
            }

        if row["skill_name"]:
            employees[emp_id]["skills"].add(normalize(row["skill_name"]))

    # Build match results (keep only above 40%)
    results = []
    for emp in employees.values():
        matched = emp["skills"] & required

        if total > 0:
            match_percentage = round(len(matched) / total * 100, 2)
        else:
            match_percentage = 0

        if match_percentage <= 40:
            continue

        results.append({
            "employee_id": emp["employee_id"],
            "full_name": emp["full_name"],
            "email": emp["email"],
            "matched_count": len(matched),
            "required_count": total,
            "match_percentage": match_percentage,
            "matched_skills": sorted(matched),
            "missing_skills": sorted(required - emp["skills"]),
        })

    # Sort by highest percentage first
    results.sort(key=lambda x: (-x["match_percentage"], -x["matched_count"], x["employee_id"]))

    # Assign rank
    rank = 1
    for emp in results:
        emp["rank"] = rank
        rank += 1

    return {
        "project": {
            "project_id": project["project_id"],
            "project_name": project["project_name"],
            "client": project["client"],
            "status": project["status"],
            "required_skills": sorted(required),
            "required_skill_count": total,
        },
        "total_employees": len(results),
        "matches": results,
    }


