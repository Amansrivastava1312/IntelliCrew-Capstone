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

# --- create table (columns you asked for) ---
cur.execute(
    """CREATE TABLE IF NOT EXISTS project_allocation (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,   -- primary key
        employee_id      TEXT    NOT NULL,
        employee_email   TEXT    NOT NULL,
        project_id       INTEGER,
        project_name     TEXT,
        selection_reason TEXT,
        is_sent          INTEGER NOT NULL DEFAULT 0,          -- 0 = not sent, 1 = sent
        manager_name     TEXT,
        created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
    )"""
)

# employee_id, employee_email, project_id, project_name, selection_reason, manager_name
SELECTIONS = [
    ("E106", "amanrajasthan123@gmail.com", 1, "IntelliCrew HR Automation",
     "Strong Python & FastAPI background", "Nikita Dash"),
    ("E107", "aman@yopmail.com", 1, "IntelliCrew HR Automation",
     "Good data analysis & reporting skills", "Nikita Dash"),
    ("E108", "e108@intelli.local", 2, "Cloud Migration",
     "Hands-on AWS / Azure experience", "Nikita Dash"),
]

# --- insert project allocations ---
for emp_id, email, pid, pname, reason, mgr in SELECTIONS:
    cur.execute(
        """INSERT INTO project_allocation
           (employee_id, employee_email, project_id, project_name,
            selection_reason, manager_name)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (emp_id, email, pid, pname, reason, mgr),
    )

conn.commit()
conn.close()
print(f"Created project_allocation table and inserted {len(SELECTIONS)} dummy selections (is_sent = 0).")
 