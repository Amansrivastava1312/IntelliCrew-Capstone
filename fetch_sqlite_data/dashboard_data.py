"""IntelliCrew — data access for the Manager dashboard (SQLite)."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

# dashboard_data.py lives inside dashboard_data/, so go UP one level to the
# project root, then into data/ — this matches where db.py / data_seed.py look.
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"


# ---------- helpers ----------
def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def _initials(name: str) -> str:
    """'Aarav Sharma' -> 'AS'."""
    parts = (name or "").split()
    return "".join(p[0] for p in parts[:2]).upper() or "NA"


# ---------- main entry point ----------
def get_manager_dashboard(manager_id: str) -> dict:
    """Return everything manager_dashboard.html needs, scoped to ONE manager."""
    conn = _connect()
    c = conn.cursor()

    # -- manager name --
    row = c.execute(
        "SELECT full_name FROM manager WHERE manager_id = ?", (manager_id,)
    ).fetchone()
    manager_name = row["full_name"] if row else "Manager"

    data = {
        "manager_id": manager_id,
        "manager_name": manager_name,
        "manager_initials": _initials(manager_name),
        "today": date.today().strftime("%a, %d %b %Y"),
        "stats": _stats(c, manager_id),
        "bench_employees": _bench_employees(c, manager_id),
        "top_skills": _top_skills(c, manager_id),
        "projects": _active_projects(c),
    }

    conn.close()
    return data


# ---------- stat cards ----------
def _stats(c: sqlite3.Cursor, manager_id: str) -> dict:
    total_employees = c.execute(
        "SELECT COUNT(*) FROM employees WHERE manager_id = ?", (manager_id,)
    ).fetchone()[0]

    # NOTE: db.py inserts status as lowercase 'active', so compare case-insensitively
    active_employees = c.execute(
        "SELECT COUNT(*) FROM employees WHERE manager_id = ? AND LOWER(status) = 'active'",
        (manager_id,),
    ).fetchone()[0]

    # bench = this manager's employees who are NOT in project_allocation at all
    on_bench = c.execute(
        """
        SELECT COUNT(*) FROM employees e
        WHERE e.manager_id = ?
          AND e.employee_id NOT IN (
              SELECT employee_id FROM project_allocation
          )
        """,
        (manager_id,),
    ).fetchone()[0]

    active_projects = c.execute(
        "SELECT COUNT(*) FROM projects WHERE LOWER(status) = 'in progress'"
    ).fetchone()[0]

    planned_projects = c.execute(
        "SELECT COUNT(*) FROM projects WHERE LOWER(status) = 'planned'"
    ).fetchone()[0]

    total_skills = c.execute(
        """
        SELECT COUNT(DISTINCT es.skill_id)
        FROM employee_skills es
        JOIN employees e ON e.employee_id = es.employee_id
        WHERE e.manager_id = ?
        """,
        (manager_id,),
    ).fetchone()[0]

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "on_bench": on_bench,
        "active_projects": active_projects,
        "planned_projects": planned_projects,
        "total_skills": total_skills,
    }


# ---------- employees on bench ----------
def _bench_employees(c: sqlite3.Cursor, manager_id: str, limit: int = 6) -> list:
    rows = c.execute(
        """
        SELECT e.employee_id, e.full_name, e.department, e.joining_date
        FROM employees e
        WHERE e.manager_id = ?
          AND e.employee_id NOT IN (
              SELECT employee_id FROM project_allocation
          )
        ORDER BY e.full_name
        LIMIT ?
        """,
        (manager_id, limit),
    ).fetchall()

    bench = []
    for r in rows:
        # experience (years) from joining_date, if present
        exp = "—"
        if r["joining_date"]:
            try:
                jd = date.fromisoformat(str(r["joining_date"])[:10])
                exp = round((date.today() - jd).days / 365.25, 1)
            except ValueError:
                exp = "—"

        bench.append(
            {
                "employee_id": r["employee_id"],
                "full_name": r["full_name"],
                "department": r["department"] or "—",
                "initials": _initials(r["full_name"]),
                "availability": "Available",   # on bench => available
                "allocation_percent": 0,
                "experience": exp,
            }
        )
    return bench


# ---------- top team skills ----------
def _top_skills(c: sqlite3.Cursor, manager_id: str, limit: int = 6) -> list:
    rows = c.execute(
        """
        SELECT s.skill_name AS skill_name, COUNT(*) AS cnt
        FROM employee_skills es
        JOIN skills s    ON s.skill_id = es.skill_id
        JOIN employees e ON e.employee_id = es.employee_id
        WHERE e.manager_id = ?
        GROUP BY s.skill_name
        ORDER BY cnt DESC
        LIMIT ?
        """,
        (manager_id, limit),
    ).fetchall()

    max_cnt = max((r["cnt"] for r in rows), default=1)
    return [
        {
            "skill_name": r["skill_name"],
            "count": r["cnt"],
            "percent": round(r["cnt"] / max_cnt * 100),
        }
        for r in rows
    ]


# ---------- active projects ----------
def _active_projects(c: sqlite3.Cursor, limit: int = 6) -> list:
    rows = c.execute(
        """
        SELECT p.project_name, p.client, p.required_skills, p.end_date, p.status,
               (SELECT COUNT(*) FROM project_allocation pa
                WHERE pa.project_id = p.project_id
               ) AS allocated_count
        FROM projects p
        WHERE LOWER(p.status) = 'in progress'
        ORDER BY p.end_date
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]