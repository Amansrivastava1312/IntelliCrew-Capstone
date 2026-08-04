"""Create the IntelliCrew SQLite database and seed required records.

Running this file creates:
    data/employee_records.db

Employee IDs are supplied by the application/user, for example E001. SQLite
will not generate employee IDs automatically.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Final

from security import hash_password


DATA_DIR: Final[Path] = Path(__file__).resolve().parent / "data"
DB_PATH: Final[Path] = DATA_DIR / "employee_records.db"

MANAGERS: Final[tuple[tuple[str, str], ...]] = (
    ("M001", "Aarav Sharma"),
    ("M002", "Priya Nair"),
    ("M003", "Rohan Mehta"),
    ("M004", "Sneha Kulkarni"),
    ("M005", "Vikram Rao"),
    ("M006", "Ananya Iyer"),
    ("M007", "Rahul Verma"),
    ("M008", "Neha Joshi"),
    ("M009", "Arjun Patel"),
    ("M010", "Kavya Menon"),
)

HR_USERS: Final[tuple[tuple[str, str], ...]] = (
    ("H001", "Meera Desai"),
    ("H002", "Aditya Singh"),
    ("H003", "Pooja Reddy"),
    ("H004", "Karan Malhotra"),
    ("H005", "Ishita Kapoor"),
    ("H006", "Nikhil Bhat"),
    ("H007", "Divya Pillai"),
    ("H008", "Siddharth Jain"),
    ("H009", "Ritika Bose"),
    ("H010", "Manish Gupta"),
)

PROJECTS: Final[tuple[tuple[int, str, str, str, str, str, str], ...]] = (
    (1, "Cloud Infrastructure Modernization", "FinEdge Banking", "AWS, Terraform, Docker, Kubernetes, Python, DevOps", "2026-01-15", "2026-10-30", "In Progress"),
    (2, "AI Customer Support Assistant", "RetailSphere", "Python, FastAPI, LangChain, RAG, PostgreSQL, Azure OpenAI", "2026-02-01", "2026-09-15", "In Progress"),
    (3, "Enterprise Data Warehouse", "HealthFirst Systems", "SQL, Python, Apache Spark, Azure Data Factory, Power BI", "2025-11-10", "2026-08-31", "In Progress"),
    (4, "Cybersecurity Monitoring Platform", "SecureNet Solutions", "Python, SIEM, Splunk, Linux, Network Security, REST APIs", "2026-03-01", "2026-12-20", "In Progress"),
    (5, "E-Commerce Mobile Application", "ShopNest Commerce", "Flutter, Dart, Node.js, MongoDB, REST APIs, Firebase", "2026-04-10", "2027-01-31", "Planned"),
    (6, "Employee Skill Management Portal", "IntelliWorks Consulting", "Python, FastAPI, SQLite, HTML, CSS, JavaScript, Jinja2", "2026-01-05", "2026-07-31", "Completed"),
    (7, "IoT Predictive Maintenance System", "AutoCore Manufacturing", "Python, IoT, MQTT, Azure IoT Hub, Machine Learning, Time Series", "2026-05-01", "2027-02-28", "Planned"),
    (8, "Digital Payment Gateway Integration", "PayWave Technologies", "Java, Spring Boot, Microservices, Kafka, PostgreSQL, OAuth 2.0", "2025-09-15", "2026-06-30", "Completed"),
    (9, "Business Intelligence Analytics Dashboard", "GlobalLogix", "Power BI, SQL, Python, Data Modeling, ETL, DAX", "2026-03-20", "2026-11-15", "In Progress"),
    (10, "Legacy ERP Microservices Migration", "NovaTech Industries", "Java, Spring Boot, Docker, Kubernetes, Kafka, PostgreSQL, CI/CD", "2026-06-01", "2027-06-30", "Planned"),
)

SCHEMA_SQL: Final[str] = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(120),
    email VARCHAR(120),
    department VARCHAR(80),
    designation VARCHAR(80),
    location VARCHAR(80),
    manager_id VARCHAR(20),
    joining_date DATE,
    status VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (manager_id) REFERENCES manager(manager_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name VARCHAR(100),
    category VARCHAR(60),
    description TEXT
);

CREATE TABLE IF NOT EXISTS employee_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id VARCHAR(20) NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency_level VARCHAR(20),
    years_experience FLOAT,
    source VARCHAR(20),
    last_verified_date DATE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS certifications (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id VARCHAR(20) NOT NULL,
    cert_name VARCHAR(120),
    issuing_body VARCHAR(100),
    issue_date DATE,
    expiry_date DATE,
    cert_score FLOAT,
    verified_flag BOOLEAN,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id VARCHAR(20) NOT NULL,
    skill_id INTEGER NOT NULL,
    assessment_name VARCHAR(100),
    score FLOAT,
    date DATE,
    result_status VARCHAR(20),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR(120),
    client VARCHAR(100),
    required_skills TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS project_allocations (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id VARCHAR(20) NOT NULL,
    project_id INTEGER NOT NULL,
    role_on_project VARCHAR(80),
    allocation_percent FLOAT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(50),
    record_id VARCHAR(20),
    action VARCHAR(20),
    changed_by VARCHAR(60),
    changed_at DATETIME,
    old_value TEXT,
    new_value TEXT
);

CREATE TABLE IF NOT EXISTS manager (
    manager_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hr (
    hr_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_employees_manager_id ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employee_skills_employee_id ON employee_skills(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_skills_skill_id ON employee_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_certifications_employee_id ON certifications(employee_id);
CREATE INDEX IF NOT EXISTS idx_assessments_employee_id ON assessments(employee_id);
CREATE INDEX IF NOT EXISTS idx_assessments_skill_id ON assessments(skill_id);
CREATE INDEX IF NOT EXISTS idx_allocations_employee_id ON project_allocations(employee_id);
CREATE INDEX IF NOT EXISTS idx_allocations_project_id ON project_allocations(project_id);
"""


def recreate_legacy_auth_tables(connection: sqlite3.Connection) -> None:
    """Remove legacy auth tables that used separate password hash fields."""
    for table_name in ("manager", "hr"):
        columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table_name})")
        }
        if columns.intersection({"password_salt", "hash_iterations", "salt"}):
            connection.execute(f"DROP TABLE {table_name}")


def validate_employee_schema(connection: sqlite3.Connection) -> None:
    """Prevent an old INTEGER employee schema from being reused silently."""
    columns = connection.execute("PRAGMA table_info(employees)").fetchall()
    if not columns:
        return

    employee_id = next((row for row in columns if row[1] == "employee_id"), None)
    if employee_id and "CHAR" not in employee_id[2].upper() and "TEXT" not in employee_id[2].upper():
        raise RuntimeError(
            "The existing database uses the old INTEGER employee_id schema. "
            "Delete data/employee_records.db once, then run data_seed.py again."
        )


def seed_login_accounts(connection: sqlite3.Connection) -> None:
    """Insert ten Manager and ten HR login accounts."""
    for manager_id, full_name in MANAGERS:
        connection.execute(
            """INSERT OR IGNORE INTO manager
               (manager_id, full_name, email, password_hash)
               VALUES (?, ?, ?, ?)""",
            (
                manager_id,
                full_name,
                f"{manager_id.lower()}@intelli.local",
                hash_password(f"Intelli@{manager_id}"),
            ),
        )

    for hr_id, full_name in HR_USERS:
        connection.execute(
            """INSERT OR IGNORE INTO hr
               (hr_id, full_name, email, password_hash)
               VALUES (?, ?, ?, ?)""",
            (
                hr_id,
                full_name,
                f"{hr_id.lower()}@intelli.local",
                hash_password(f"Intelli@{hr_id}"),
            ),
        )


def seed_projects(connection: sqlite3.Connection) -> None:
    """Insert ten realistic IT projects without duplicates."""
    connection.executemany(
        """INSERT OR IGNORE INTO projects
           (project_id, project_name, client, required_skills,
            start_date, end_date, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        PROJECTS,
    )


def create_database(db_path: Path = DB_PATH) -> None:
    """Create the schema and seed required login and project records."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        validate_employee_schema(connection)
        recreate_legacy_auth_tables(connection)
        connection.executescript(SCHEMA_SQL)
        seed_login_accounts(connection)
        seed_projects(connection)

    print(f"Database created successfully: {db_path}")
    print("Employee IDs are user supplied, for example E001.")
    print("Manager accounts: M001 to M010")
    print("HR accounts: H001 to H010")
    print("Projects seeded: 10")


if __name__ == "__main__":
    create_database()
