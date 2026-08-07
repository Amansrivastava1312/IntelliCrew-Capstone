"""IntelliCrew — data fetch for the centralized organization report."""

import sqlite3
from pathlib import Path

# report_data.py is inside report_agent/, go UP one level then into data/
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"


def get_conn():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_report_data():
    """Pull org-wide numbers from related tables into one dict."""
    conn = get_conn()
    cur = conn.cursor()

    # ---- headline counts ----
    total_employees = cur.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    active_employees = cur.execute(
        "SELECT COUNT(*) FROM employees WHERE LOWER(status) = 'active'"
    ).fetchone()[0]
    total_skills = cur.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    total_projects = cur.execute("SELECT COUNT(*) FROM projects").fetchone()[0]

    # ---- project status breakdown ----
    status_rows = cur.execute(
        "SELECT status, COUNT(*) AS cnt FROM projects GROUP BY status"
    ).fetchall()
    project_status = {r["status"]: r["cnt"] for r in status_rows}

    # ---- per-project detail with allocated employee count ----
    project_rows = cur.execute(
        """
        SELECT p.project_id, p.project_name, p.client, p.required_skills,
               p.start_date, p.end_date, p.status,
               (SELECT COUNT(*) FROM project_allocation pa
                WHERE pa.project_id = p.project_id) AS allocated_count
        FROM projects p
        ORDER BY p.status, p.project_name
        """
    ).fetchall()
    projects = [dict(r) for r in project_rows]

    # ---- top skills across the organization ----
    skill_rows = cur.execute(
        """
        SELECT s.skill_name AS skill_name, COUNT(*) AS cnt
        FROM employee_skills es
        JOIN skills s ON s.skill_id = es.skill_id
        GROUP BY s.skill_name
        ORDER BY cnt DESC
        LIMIT 15
        """
    ).fetchall()
    top_skills = [{"skill_name": r["skill_name"], "count": r["cnt"]} for r in skill_rows]

    # ---- employees on bench (no allocation) ----
    bench_count = cur.execute(
        """
        SELECT COUNT(*) FROM employees e
        WHERE e.employee_id NOT IN (SELECT employee_id FROM project_allocation)
        """
    ).fetchone()[0]

    conn.close()

    return {
        "totals": {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "total_skills": total_skills,
            "total_projects": total_projects,
            "bench_count": bench_count,
        },
        "project_status": project_status,
        "projects": projects,
        "top_skills": top_skills,
    }
