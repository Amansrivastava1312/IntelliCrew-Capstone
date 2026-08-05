"""IntelliCrew — data access for the Create Requirement page (SQLite)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

# requirement_data.py lives inside fetch_sqlite_data/, so go UP one level
# to the project root, then into data/ — same logic as dashboard_data.py
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"


def _connect() -> sqlite3.Connection:
    # clear error if the DB path is ever wrong again
    if not DATABASE_FILE.exists():
        raise FileNotFoundError(f"DB not found at: {DATABASE_FILE}")
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    return conn


def _split_skills(raw: str) -> list:
    """'AWS, Terraform, Docker' -> ['AWS', 'Terraform', 'Docker']"""
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def get_projects() -> list:
    """Return every project with its required skills already split into a list."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT project_id, project_name, client, required_skills
        FROM projects
        ORDER BY project_name
        """
    ).fetchall()
    conn.close()

    projects = []
    for r in rows:
        projects.append(
            {
                "project_id": r["project_id"],
                "project_name": r["project_name"],
                "client": r["client"],
                "skills": _split_skills(r["required_skills"]),  # list of skills
            }
        )
    return projects


def get_project_skills(project_id: int) -> list:
    """Return only the skills list for one project (handy for later use)."""
    conn = _connect()
    row = conn.execute(
        "SELECT required_skills FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    conn.close()
    return _split_skills(row["required_skills"]) if row else []