"""
seed_data.py
------------
Builds the ENTIRE IntelliCrew database from scratch using RAW SQL only.
No classes, no ORM models — just CREATE TABLE + INSERT statements run
through the shared engine from db.py.

Run once:
    python seed_data.py

Creates 9 connected tables and fills them with a large, realistic dataset:
  - 8   departments
  - 60  employees
  - ~180 skills
  - 12  projects
  - ~90 allocations
  - ~70 certifications
  - 40  candidates
  - 30  documents
  - 50  email logs
"""

import os
import random
from datetime import date, timedelta

from sqlalchemy import text
from db_chatbot.db import engine

# Fixed seed => everyone on the team gets the exact same data
random.seed(42)

# Make sure the data/ folder exists before SQLite writes the file
os.makedirs("data", exist_ok=True)


# ---------------------------------------------------------------------------
# 1. SCHEMA — all tables defined as raw SQL (no classes)
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
DROP TABLE IF EXISTS email_logs;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS certifications;
DROP TABLE IF EXISTS allocations;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    head      TEXT NOT NULL,
    location  TEXT NOT NULL
);

CREATE TABLE employees (
    id                INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    email             TEXT NOT NULL,
    department_id     INTEGER,
    role              TEXT NOT NULL,
    location          TEXT NOT NULL,
    experience_years  REAL NOT NULL,
    salary            REAL NOT NULL,
    status            TEXT NOT NULL,
    join_date         DATE NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE skills (
    id           INTEGER PRIMARY KEY,
    employee_id  INTEGER,
    skill_name   TEXT NOT NULL,
    proficiency  TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE projects (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    client      TEXT NOT NULL,
    status      TEXT NOT NULL,
    start_date  DATE NOT NULL,
    budget      REAL NOT NULL
);

CREATE TABLE allocations (
    id               INTEGER PRIMARY KEY,
    employee_id      INTEGER,
    project_id       INTEGER,
    allocation_pct   INTEGER NOT NULL,
    role_on_project  TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (project_id)  REFERENCES projects(id)
);

CREATE TABLE certifications (
    id           INTEGER PRIMARY KEY,
    employee_id  INTEGER,
    cert_name    TEXT NOT NULL,
    issuer       TEXT NOT NULL,
    issued_date  DATE NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE candidates (
    id                INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    applied_role      TEXT NOT NULL,
    match_score       REAL NOT NULL,
    status            TEXT NOT NULL,
    experience_years  REAL NOT NULL
);

CREATE TABLE documents (
    id              INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    doc_type        TEXT NOT NULL,
    uploaded_by     INTEGER,
    summary_status  TEXT NOT NULL,
    FOREIGN KEY (uploaded_by) REFERENCES employees(id)
);

CREATE TABLE email_logs (
    id             INTEGER PRIMARY KEY,
    recipient      TEXT NOT NULL,
    subject        TEXT NOT NULL,
    trigger_event  TEXT NOT NULL,
    status         TEXT NOT NULL,
    sent_date      DATE NOT NULL
);
"""


# ---------------------------------------------------------------------------
# 2. REFERENCE DATA POOLS (used to randomly build realistic rows)
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    ("Engineering",  "Rajesh Kumar",  "Bengaluru"),
    ("Data Science", "Priya Sharma",  "Bengaluru"),
    ("Design",       "Neha Gupta",    "Hyderabad"),
    ("Product",      "Arjun Mehta",   "Pune"),
    ("HR",           "Kavya Reddy",   "Bengaluru"),
    ("DevOps",       "Suresh Nair",   "Pune"),
    ("QA",           "Divya Iyer",    "Chennai"),
    ("Sales",        "Vikram Singh",  "Mumbai"),
]

FIRST_NAMES = [
    "Aman", "Anuj", "Shubham", "Anjali", "Lakshya", "Pranay", "Rahul", "Sneha",
    "Karan", "Pooja", "Rohit", "Meera", "Aditya", "Nisha", "Varun", "Ishita",
    "Sagar", "Tanvi", "Nikhil", "Riya", "Harsh", "Ananya", "Yash", "Kritika",
    "Dev", "Simran", "Manish", "Aarti", "Gaurav", "Payal", "Siddharth", "Neelam",
    "Akash", "Deepa", "Vivek", "Shreya", "Naveen", "Priyanka", "Rohan", "Swati",
    "Abhishek", "Komal", "Sameer", "Nandini", "Tarun", "Bhavya", "Kunal", "Ritu",
    "Vishal", "Ayesha", "Mohit", "Sakshi", "Ashish", "Diksha", "Rakesh", "Juhi",
    "Piyush", "Megha", "Sanjay", "Preeti",
]
LAST_NAMES = [
    "Srivastava", "Jagtap", "Prabhu", "Lalwani", "Garg", "Ambade", "Sharma",
    "Verma", "Reddy", "Nair", "Iyer", "Singh", "Mehta", "Gupta", "Kumar",
    "Patel", "Joshi", "Rao", "Desai", "Kulkarni", "Bose", "Chopra", "Malhotra",
]

ROLES = [
    "ML Engineer", "Backend Developer", "Frontend Developer",
    "Full Stack Developer", "Data Analyst", "Data Scientist",
    "DevOps Engineer", "UI/UX Designer", "QA Engineer",
    "Product Manager", "Business Analyst", "Cloud Engineer",
]
LOCATIONS = ["Bengaluru", "Pune", "Hyderabad", "Chennai", "Mumbai", "Delhi"]
STATUSES = ["Allocated", "Available"]

SKILL_POOL = [
    "Python", "SQL", "JavaScript", "React", "FastAPI", "Flask", "Django",
    "LangChain", "LangGraph", "TensorFlow", "PyTorch", "Docker", "Kubernetes",
    "AWS", "Azure", "Machine Learning", "Deep Learning", "NLP", "Pandas",
    "Git", "MongoDB", "PostgreSQL", "Figma", "Java", "C++", "Power BI",
]
PROFICIENCY = ["Beginner", "Intermediate", "Expert"]

PROJECTS = [
    ("IntelliCrew Platform",  "Internal",      "Active"),
    ("Retail Analytics",      "ShopMart",      "Active"),
    ("Fraud Detection",       "SafeBank",      "Active"),
    ("Chatbot Assistant",     "TechCorp",      "Completed"),
    ("Sales Forecasting",     "GrowMax",       "Active"),
    ("HR Automation",         "PeopleFirst",   "On Hold"),
    ("Recommendation Engine", "StreamNow",     "Active"),
    ("Vision QC System",      "AutoParts Ltd", "Completed"),
    ("Document Summarizer",   "LegalEase",     "Active"),
    ("Demand Planning",       "SupplyChainX",  "On Hold"),
    ("Customer Churn Model",  "TelConnect",    "Active"),
    ("Voice Analytics",       "CallCenterPro", "Completed"),
]

CERTS = [
    ("AWS Certified Solutions Architect",  "Amazon"),
    ("Google Professional ML Engineer",    "Google"),
    ("Azure AI Engineer Associate",        "Microsoft"),
    ("Certified Kubernetes Administrator", "CNCF"),
    ("TensorFlow Developer Certificate",   "Google"),
    ("Deep Learning Specialization",       "Coursera"),
    ("Scrum Master Certified",             "Scrum.org"),
    ("Data Science Professional",          "IBM"),
]

DOC_TYPES = ["Report", "Resume", "Video", "Policy"]
DOC_TITLES = [
    "Q3 Performance Report", "Employee Handbook", "AI Strategy Deck",
    "Onboarding Guide", "Security Policy", "Project Retro Video",
    "Candidate Resume Batch", "Market Analysis", "Training Manual",
    "Client Proposal", "Tech Talk Recording", "Compliance Report",
]

EMAIL_EVENTS = [
    "Resume Screened", "Skill Gap Found", "Certification Added",
    "Project Allocated", "Summary Ready", "Approval Requested",
    "Onboarding Reminder", "Assessment Completed",
]
EMAIL_SUBJECTS = [
    "Your resume was screened",
    "Skill gap detected in your profile",
    "New certification recorded",
    "You have been allocated to a project",
    "Your document summary is ready",
    "Approval needed for allocation",
]


def random_date(start_year=2021, end_year=2025):
    """Return a random ISO date string between the two years."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


# ---------------------------------------------------------------------------
# 3. BUILD THE DATA IN PYTHON (plain lists of tuples), then bulk INSERT
# ---------------------------------------------------------------------------
def seed():
    with engine.begin() as conn:
        # --- Create all tables (raw SQL, statement by statement) ---
        for statement in SCHEMA_SQL.strip().split(";"):
            if statement.strip():
                conn.execute(text(statement))

        # --- 1. Departments ---
        for i, (name, head, loc) in enumerate(DEPARTMENTS, start=1):
            conn.execute(
                text("INSERT INTO departments (id, name, head, location) "
                     "VALUES (:id, :name, :head, :loc)"),
                {"id": i, "name": name, "head": head, "loc": loc},
            )
        dept_ids = list(range(1, len(DEPARTMENTS) + 1))

        # --- 2. Employees (60) ---
        used_names = set()
        for i in range(1, 61):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            while name in used_names:
                fn = random.choice(FIRST_NAMES)
                ln = random.choice(LAST_NAMES)
                name = f"{fn} {ln}"
            used_names.add(name)

            exp = round(random.uniform(0.5, 12.0), 1)
            salary = float(round(500000 + exp * 90000 +
                                 random.randint(-50000, 120000), -3))
            conn.execute(
                text("""INSERT INTO employees
                    (id, name, email, department_id, role, location,
                     experience_years, salary, status, join_date)
                    VALUES
                    (:id, :name, :email, :dept, :role, :loc,
                     :exp, :salary, :status, :jd)"""),
                {
                    "id": i, "name": name,
                    "email": f"{fn.lower()}.{ln.lower()}@intellicrew.com",
                    "dept": random.choice(dept_ids),
                    "role": random.choice(ROLES),
                    "loc": random.choice(LOCATIONS),
                    "exp": exp, "salary": salary,
                    "status": random.choices(STATUSES, weights=[65, 35])[0],
                    "jd": random_date(2019, 2025),
                },
            )
        emp_ids = list(range(1, 61))

        # --- 3. Skills (each employee gets 2-5) ---
        skill_id = 1
        for eid in emp_ids:
            for skill_name in random.sample(SKILL_POOL, random.randint(2, 5)):
                conn.execute(
                    text("""INSERT INTO skills
                        (id, employee_id, skill_name, proficiency)
                        VALUES (:id, :eid, :sn, :prof)"""),
                    {"id": skill_id, "eid": eid, "sn": skill_name,
                     "prof": random.choice(PROFICIENCY)},
                )
                skill_id += 1

        # --- 4. Projects (12) ---
        for i, (name, client, status) in enumerate(PROJECTS, start=1):
            conn.execute(
                text("""INSERT INTO projects
                    (id, name, client, status, start_date, budget)
                    VALUES (:id, :name, :client, :status, :sd, :budget)"""),
                {"id": i, "name": name, "client": client, "status": status,
                 "sd": random_date(2022, 2025),
                 "budget": float(random.randint(20, 200) * 100000)},
            )
        proj_ids = list(range(1, len(PROJECTS) + 1))

        # --- 5. Allocations (only for 'Allocated' employees) ---
        alloc_id = 1
        # Re-read each employee's status to keep allocations realistic
        statuses = conn.execute(
            text("SELECT id, status FROM employees")).fetchall()
        for eid, status in statuses:
            if status == "Allocated":
                for pid in random.sample(proj_ids, random.randint(1, 2)):
                    conn.execute(
                        text("""INSERT INTO allocations
                            (id, employee_id, project_id,
                             allocation_pct, role_on_project)
                            VALUES (:id, :eid, :pid, :pct, :role)"""),
                        {"id": alloc_id, "eid": eid, "pid": pid,
                         "pct": random.choice([25, 50, 75, 100]),
                         "role": random.choice(ROLES)},
                    )
                    alloc_id += 1

        # --- 6. Certifications (~70) ---
        for i in range(1, 71):
            cert_name, issuer = random.choice(CERTS)
            conn.execute(
                text("""INSERT INTO certifications
                    (id, employee_id, cert_name, issuer, issued_date)
                    VALUES (:id, :eid, :cn, :iss, :idt)"""),
                {"id": i, "eid": random.choice(emp_ids),
                 "cn": cert_name, "iss": issuer,
                 "idt": random_date(2021, 2025)},
            )

        # --- 7. Candidates (40) ---
        for i in range(1, 41):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            score = round(random.uniform(35, 98), 1)
            if score >= 75:
                status = "Shortlisted"
            elif score >= 50:
                status = "Pending"
            else:
                status = "Rejected"
            conn.execute(
                text("""INSERT INTO candidates
                    (id, name, applied_role, match_score,
                     status, experience_years)
                    VALUES (:id, :name, :role, :score, :status, :exp)"""),
                {"id": i, "name": f"{fn} {ln}",
                 "role": random.choice(ROLES), "score": score,
                 "status": status,
                 "exp": round(random.uniform(0.0, 10.0), 1)},
            )

        # --- 8. Documents (30) ---
        for i in range(1, 31):
            conn.execute(
                text("""INSERT INTO documents
                    (id, title, doc_type, uploaded_by, summary_status)
                    VALUES (:id, :title, :dt, :ub, :ss)"""),
                {"id": i, "title": random.choice(DOC_TITLES),
                 "dt": random.choice(DOC_TYPES),
                 "ub": random.choice(emp_ids),
                 "ss": random.choice(["Pending", "Summarized"])},
            )

        # --- 9. Email logs (50) ---
        emails = conn.execute(
            text("SELECT email FROM employees")).fetchall()
        email_list = [e[0] for e in emails]
        for i in range(1, 51):
            conn.execute(
                text("""INSERT INTO email_logs
                    (id, recipient, subject, trigger_event,
                     status, sent_date)
                    VALUES (:id, :rec, :subj, :ev, :status, :sd)"""),
                {"id": i, "rec": random.choice(email_list),
                 "subj": random.choice(EMAIL_SUBJECTS),
                 "ev": random.choice(EMAIL_EVENTS),
                 "status": random.choices(["Sent", "Failed"],
                                          weights=[90, 10])[0],
                 "sd": random_date(2025, 2026)},
            )

    # --- Print a summary so you can confirm it worked ---
    with engine.connect() as conn:
        def count(tbl):
            return conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()

        print("✅ Database seeded successfully!")
        print(f"   Departments   : {count('departments')}")
        print(f"   Employees     : {count('employees')}")
        print(f"   Skills        : {count('skills')}")
        print(f"   Projects      : {count('projects')}")
        print(f"   Allocations   : {count('allocations')}")
        print(f"   Certifications: {count('certifications')}")
        print(f"   Candidates    : {count('candidates')}")
        print(f"   Documents     : {count('documents')}")
        print(f"   Email logs    : {count('email_logs')}")


if __name__ == "__main__":
    seed()
