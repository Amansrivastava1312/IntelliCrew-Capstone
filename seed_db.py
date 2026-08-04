"""IntelliCrew development database seeder.

Requested design:
- Separate managers and employees tables.
- Manager IDs: M001, M002, ...
- Employee IDs: E001, E002, ...
- Each employee references one manager through employees.manager_id.
- Employee resume path: uploads/<employee_id>.pdf.
- Temporary development password: Intelli@<record_id>.
- Passwords are stored only as salted hashes.
- Both managers and employees have empty `certification` and `skills` text columns.
- `skills` and `certifications` remain independent dropdown master tables.
- Managers and allocated employees store a project ID in `allocation`.
- Available employees have `allocation` set to NULL.
- No separate allocations table.
- No documents table.

WARNING: This script drops and recreates all tables. Development use only.
"""

import hashlib
import os
import random
import secrets
from datetime import date, timedelta

from sqlalchemy import text
from db_chatbot.db import engine

random.seed(42)
os.makedirs("data", exist_ok=True)
os.makedirs("uploads", exist_ok=True)


def random_date(start_year=2021, end_year=2025):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return (start + timedelta(days=random.randint(0, (end - start).days))).isoformat()


def temporary_password(record_id):
    """Return a development-only initial password, such as Intelli@E001."""
    return f"Intelli@{record_id}"


def hash_password(password):
    """Store a salted scrypt hash, never the readable password."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return f"scrypt${salt.hex()}${digest.hex()}"


SCHEMA_SQL = """
DROP TABLE IF EXISTS email_logs;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS allocations;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS managers;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS certifications;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    head TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    client TEXT NOT NULL,
    status TEXT NOT NULL,
    start_date DATE NOT NULL,
    budget REAL NOT NULL CHECK (budget >= 0)
);

CREATE TABLE managers (
    id TEXT PRIMARY KEY CHECK (id GLOB 'M[0-9][0-9][0-9]'),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department_id INTEGER NOT NULL UNIQUE,
    designation TEXT NOT NULL DEFAULT 'Department Manager',
    location TEXT NOT NULL,
    experience_years REAL NOT NULL CHECK (experience_years >= 0),
    salary REAL NOT NULL CHECK (salary >= 0),
    employment_status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (employment_status IN ('ACTIVE','INACTIVE','NOTICE_PERIOD')),
    join_date DATE NOT NULL,
    certification TEXT NOT NULL DEFAULT '',
    skills TEXT NOT NULL DEFAULT '',
    allocation INTEGER,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (allocation) REFERENCES projects(id)
);

CREATE TABLE employees (
    id TEXT PRIMARY KEY CHECK (id GLOB 'E[0-9][0-9][0-9]'),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department_id INTEGER NOT NULL,
    manager_id TEXT NOT NULL,
    designation TEXT NOT NULL,
    location TEXT NOT NULL,
    experience_years REAL NOT NULL CHECK (experience_years >= 0),
    salary REAL NOT NULL CHECK (salary >= 0),
    status TEXT NOT NULL CHECK (status IN ('Allocated','Available')),
    join_date DATE NOT NULL,
    resume_path TEXT NOT NULL UNIQUE,
    certification TEXT NOT NULL DEFAULT '',
    skills TEXT NOT NULL DEFAULT '',
    allocation INTEGER,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (manager_id) REFERENCES managers(id),
    FOREIGN KEY (allocation) REFERENCES projects(id)
);

CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE certifications (
    id INTEGER PRIMARY KEY,
    cert_name TEXT NOT NULL UNIQUE
);

CREATE TABLE candidates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_role TEXT NOT NULL,
    match_score REAL NOT NULL CHECK (match_score BETWEEN 0 AND 100),
    status TEXT NOT NULL,
    experience_years REAL NOT NULL CHECK (experience_years >= 0)
);

CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    trigger_event TEXT NOT NULL,
    status TEXT NOT NULL,
    sent_date DATE NOT NULL
);

CREATE INDEX ix_managers_department ON managers(department_id);
CREATE INDEX ix_managers_allocation ON managers(allocation);
CREATE INDEX ix_employees_department ON employees(department_id);
CREATE INDEX ix_employees_manager ON employees(manager_id);
CREATE INDEX ix_employees_allocation ON employees(allocation);
"""

DEPARTMENTS = [("Engineering","Rajesh Kumar","Bengaluru"),("Data Science","Priya Sharma","Bengaluru"),("Design","Neha Gupta","Hyderabad"),("Product","Arjun Mehta","Pune"),("HR","Kavya Reddy","Bengaluru"),("DevOps","Suresh Nair","Pune"),("QA","Divya Iyer","Chennai"),("Sales","Vikram Singh","Mumbai")]
FIRST_NAMES = ["Aman","Anuj","Shubham","Anjali","Lakshya","Pranay","Rahul","Sneha","Karan","Pooja","Rohit","Meera","Aditya","Nisha","Varun","Ishita","Sagar","Tanvi","Nikhil","Riya","Harsh","Ananya","Yash","Kritika","Dev","Simran","Manish","Aarti","Gaurav","Payal","Siddharth","Neelam","Akash","Deepa","Vivek","Shreya","Naveen","Priyanka","Rohan","Swati"]
LAST_NAMES = ["Srivastava","Jagtap","Prabhu","Lalwani","Garg","Ambade","Sharma","Verma","Reddy","Nair","Iyer","Singh","Mehta","Gupta","Kumar","Patel","Joshi","Rao","Desai","Kulkarni"]
ROLES = ["ML Engineer","Backend Developer","Frontend Developer","Full Stack Developer","Data Analyst","Data Scientist","DevOps Engineer","UI/UX Designer","QA Engineer","Product Manager","Business Analyst","Cloud Engineer"]
LOCATIONS = ["Bengaluru","Pune","Hyderabad","Chennai","Mumbai","Delhi"]
SKILLS = ["Python","SQL","JavaScript","React","FastAPI","Flask","Django","LangChain","LangGraph","TensorFlow","PyTorch","Docker","Kubernetes","AWS","Azure","Machine Learning","Deep Learning","NLP","Pandas","Git","MongoDB","PostgreSQL","Figma","Java","C++","Power BI"]
CERTIFICATIONS = ["AWS Certified Solutions Architect","Google Professional ML Engineer","Azure AI Engineer Associate","Certified Kubernetes Administrator","TensorFlow Developer Certificate","Deep Learning Specialization","Scrum Master Certified","IBM Data Science Professional"]
PROJECTS = [("IntelliCrew Platform","Internal","Active"),("Retail Analytics","ShopMart","Active"),("Fraud Detection","SafeBank","Active"),("Chatbot Assistant","TechCorp","Completed"),("Sales Forecasting","GrowMax","Active"),("HR Automation","PeopleFirst","On Hold"),("Recommendation Engine","StreamNow","Active"),("Vision QC System","AutoParts Ltd","Completed"),("Document Summarizer","LegalEase","Active"),("Demand Planning","SupplyChainX","On Hold"),("Customer Churn Model","TelConnect","Active"),("Voice Analytics","CallCenterPro","Completed")]
EMAIL_EVENTS = ["Resume Screened","Skill Gap Found","Certification Added","Project Allocated","Summary Ready","Approval Requested","Onboarding Reminder","Assessment Completed"]
EMAIL_SUBJECTS = ["Your resume was screened","Skill gap detected in your profile","New certification recorded","You have been allocated to a project","Your document summary is ready","Approval needed for allocation"]


def seed():
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        for statement in SCHEMA_SQL.strip().split(";"):
            if statement.strip():
                conn.execute(text(statement))

        for did, (name, head, location) in enumerate(DEPARTMENTS, 1):
            conn.execute(text("INSERT INTO departments VALUES (:id,:name,:head,:location)"), {"id":did,"name":name,"head":head,"location":location})

        # Projects are inserted before managers and employees because allocation is a project FK.
        for pid, (name, client, status) in enumerate(PROJECTS, 1):
            conn.execute(text("INSERT INTO projects VALUES (:id,:name,:client,:status,:start_date,:budget)"), {"id":pid,"name":name,"client":client,"status":status,"start_date":random_date(2022,2025),"budget":float(random.randint(20,200)*100000)})

        manager_rows = []
        for number, (_, name, location) in enumerate(DEPARTMENTS, 1):
            mid = f"M{number:03d}"
            first, last = name.split(" ", 1)
            exp = round(random.uniform(7, 15), 1)
            manager_rows.append({"id":mid,"name":name,"email":f"{first.lower()}.{last.lower()}@intellicrew.com","department_id":number,"location":location,"experience_years":exp,"salary":float(round(900000+exp*100000,-3)),"join_date":random_date(2016,2021),"certification":"","skills":"","allocation":random.randint(1,len(PROJECTS)),"username":mid,"password_hash":hash_password(temporary_password(mid))})
        conn.execute(text("""INSERT INTO managers
            (id,name,email,department_id,location,experience_years,salary,join_date,certification,skills,allocation,username,password_hash)
            VALUES (:id,:name,:email,:department_id,:location,:experience_years,:salary,:join_date,:certification,:skills,:allocation,:username,:password_hash)"""), manager_rows)

        used_names = {department[1] for department in DEPARTMENTS}
        employee_rows = []
        for number in range(1, 61):
            while True:
                first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
                name = f"{first} {last}"
                if name not in used_names:
                    used_names.add(name)
                    break
            eid = f"E{number:03d}"
            did = random.randint(1, 8)
            exp = round(random.uniform(0.5, 12), 1)
            employee_status = random.choices(["Allocated","Available"], weights=[65,35])[0]
            employee_rows.append({"id":eid,"name":name,"email":f"{first.lower()}.{last.lower()}@intellicrew.com","department_id":did,"manager_id":f"M{did:03d}","designation":random.choice(ROLES),"location":random.choice(LOCATIONS),"experience_years":exp,"salary":float(round(500000+exp*90000+random.randint(-50000,120000),-3)),"status":employee_status,"join_date":random_date(2019,2025),"resume_path":f"uploads/{eid}.pdf","certification":"","skills":"","allocation":random.randint(1,len(PROJECTS)) if employee_status == "Allocated" else None,"username":eid,"password_hash":hash_password(temporary_password(eid))})
        conn.execute(text("""INSERT INTO employees
            (id,name,email,department_id,manager_id,designation,location,experience_years,salary,status,join_date,resume_path,certification,skills,allocation,username,password_hash)
            VALUES (:id,:name,:email,:department_id,:manager_id,:designation,:location,:experience_years,:salary,:status,:join_date,:resume_path,:certification,:skills,:allocation,:username,:password_hash)"""), employee_rows)

        conn.execute(text("INSERT INTO skills (id,skill_name) VALUES (:id,:skill_name)"), [{"id":i,"skill_name":v} for i,v in enumerate(SKILLS,1)])
        conn.execute(text("INSERT INTO certifications (id,cert_name) VALUES (:id,:cert_name)"), [{"id":i,"cert_name":v} for i,v in enumerate(CERTIFICATIONS,1)])

        for cid in range(1, 41):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            score = round(random.uniform(35,98),1)
            status = "Shortlisted" if score >= 75 else "Pending" if score >= 50 else "Rejected"
            conn.execute(text("INSERT INTO candidates VALUES (:id,:name,:role,:score,:status,:exp)"), {"id":cid,"name":f"{first} {last}","role":random.choice(ROLES),"score":score,"status":status,"exp":round(random.uniform(0,10),1)})

        recipients = [row["email"] for row in manager_rows + employee_rows]
        for log_id in range(1, 51):
            conn.execute(text("INSERT INTO email_logs VALUES (:id,:recipient,:subject,:event,:status,:sent_date)"), {"id":log_id,"recipient":random.choice(recipients),"subject":random.choice(EMAIL_SUBJECTS),"event":random.choice(EMAIL_EVENTS),"status":random.choices(["Sent","Failed"],weights=[90,10])[0],"sent_date":random_date(2025,2026)})

    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        errors = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
        if errors:
            raise RuntimeError(f"Foreign key validation failed: {errors}")

        manager_profile_errors = conn.execute(text("SELECT id FROM managers WHERE certification <> '' OR skills <> ''")).fetchall()
        employee_profile_errors = conn.execute(text("SELECT id FROM employees WHERE certification <> '' OR skills <> ''")).fetchall()
        if manager_profile_errors or employee_profile_errors:
            raise RuntimeError("Expected empty certification and skills columns after seeding.")

        allocation_errors = conn.execute(text("""
            SELECT id FROM employees
            WHERE (status = 'Allocated' AND allocation IS NULL)
               OR (status = 'Available' AND allocation IS NOT NULL)
        """)).fetchall()
        if allocation_errors:
            raise RuntimeError(f"Employee allocation validation failed: {allocation_errors}")

        print("Database seeded successfully")
        print("Managers: M001-M008, passwords Intelli@M001-Intelli@M008")
        print("Employees: E001-E060, passwords Intelli@E001-Intelli@E060")
        print("Passwords are stored as salted hashes")
        print("Employee resumes: uploads/E001.pdf-uploads/E060.pdf")
        print("Skill dropdown values: independent skills table")
        print("Certification dropdown values: independent certifications table")
        print("Manager and employee certification/skills columns are empty")
        print("Project IDs are stored in managers.allocation and employees.allocation")


if __name__ == "__main__":
    seed()
