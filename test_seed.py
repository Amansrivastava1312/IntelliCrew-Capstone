"""Insert a few dummy employees under manager M001, with some allocations."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB = Path(__file__).resolve().parent / "data" / "employee_records.db"

# employee_id, full_name, department, designation
EMPLOYEES = [
    ("E106", "Aditi Sharma",  "Engineering",      "Software Engineer"),
    ("E107", "Rishabh Verma", "Data & Analytics", "Data Analyst"),
    ("E108", "Naina Nair",    "Cloud Services",   "Cloud Engineer"),
    ("E109", "Kabir Mehta",   "Cybersecurity",    "Security Analyst"),
    ("E1010", "Tanya Bose",    "AI & ML",          "ML Engineer"),
]

# employee_id, project_id, role, allocation_percent  (these become "Active")
ALLOCATIONS = [
    ("E101", 1, "Developer", 100),
    ("E102", 3, "Analyst",   75),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()
today = date.today()

# --- insert employees ---
for emp_id, name, dept, desig in EMPLOYEES:
    cur.execute(
        """INSERT OR IGNORE INTO employees
           (employee_id, full_name, email, department, designation,
            location, manager_id, joining_date, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'Bengaluru', 'M001', ?, 'active',
                   datetime('now'), datetime('now'))""",
        (emp_id, name, f"{emp_id.lower()}@intelli.local", dept, desig,
         today.isoformat()),
    )

# --- insert project allocations ---
for emp_id, project_id, role, percent in ALLOCATIONS:
    exists = cur.execute(
        "SELECT 1 FROM project_allocations WHERE employee_id = ? AND project_id = ?",
        (emp_id, project_id),
    ).fetchone()
    if not exists:
        cur.execute(
            """INSERT INTO project_allocations
               (employee_id, project_id, role_on_project, allocation_percent,
                start_date, end_date, status)
               VALUES (?, ?, ?, ?, ?, ?, 'Active')""",
            (emp_id, project_id, role, percent,
             today.isoformat(), (today + timedelta(days=120)).isoformat()),
        )

conn.commit()
conn.close()
print(f"Inserted {len(EMPLOYEES)} employees and {len(ALLOCATIONS)} allocations under M001.")