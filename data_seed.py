"""Create the IntelliCrew SQLite database and seed login accounts.

Running this file creates:
    data/employee_records.db

All business tables remain empty. Ten Manager accounts and ten HR accounts
are inserted with realistic fictional names. Password hashing is handled only
by security.py and stored in one database column named password_hash.
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

SCHEMA_SQL: Final[str] = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(120),
    email VARCHAR(120),
    department VARCHAR(80),
    designation VARCHAR(80),
    location VARCHAR(80),
    manager_id INTEGER,
    joining_date DATE,
    status VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name VARCHAR(100),
    category VARCHAR(60),
    description TEXT
);

CREATE TABLE IF NOT EXISTS employee_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
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
    employee_id INTEGER NOT NULL,
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
    employee_id INTEGER NOT NULL,
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
    employee_id INTEGER NOT NULL,
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
    record_id INTEGER,
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

CREATE INDEX IF NOT EXISTS idx_employees_manager_id
    ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employee_skills_employee_id
    ON employee_skills(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_skills_skill_id
    ON employee_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_certifications_employee_id
    ON certifications(employee_id);
CREATE INDEX IF NOT EXISTS idx_assessments_employee_id
    ON assessments(employee_id);
CREATE INDEX IF NOT EXISTS idx_assessments_skill_id
    ON assessments(skill_id);
CREATE INDEX IF NOT EXISTS idx_allocations_employee_id
    ON project_allocations(employee_id);
CREATE INDEX IF NOT EXISTS idx_allocations_project_id
    ON project_allocations(project_id);
"""


def recreate_legacy_auth_tables(connection: sqlite3.Connection) -> None:
    """Remove old PBKDF2 auth schemas so only one scrypt hash field remains.

    This affects only manager and hr login tables. Business tables are not
    deleted. Existing login rows are reseeded by seed_login_accounts().
    """
    for table_name in ("manager", "hr"):
        columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table_name})")
        }
        legacy_columns = {"password_salt", "hash_iterations", "salt"}
        if columns.intersection(legacy_columns):
            connection.execute(f"DROP TABLE {table_name}")


def seed_login_accounts(connection: sqlite3.Connection) -> None:
    """Insert 10 Managers and 10 HR users with scrypt password hashes."""
    for manager_id, full_name in MANAGERS:
        password = f"Intelli@{manager_id}"
        connection.execute(
            """
            INSERT OR IGNORE INTO manager (
                manager_id, full_name, email, password_hash
            ) VALUES (?, ?, ?, ?)
            """,
            (
                manager_id,
                full_name,
                f"{manager_id.lower()}@intelli.local",
                hash_password(password),
            ),
        )

    for hr_id, full_name in HR_USERS:
        password = f"Intelli@{hr_id}"
        connection.execute(
            """
            INSERT OR IGNORE INTO hr (
                hr_id, full_name, email, password_hash
            ) VALUES (?, ?, ?, ?)
            """,
            (
                hr_id,
                full_name,
                f"{hr_id.lower()}@intelli.local",
                hash_password(password),
            ),
        )


def create_database(db_path: Path = DB_PATH) -> None:
    """Create the data folder, schema, and scrypt-based login accounts."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        recreate_legacy_auth_tables(connection)
        connection.executescript(SCHEMA_SQL)
        seed_login_accounts(connection)

    print(f"Database created successfully: {db_path}")
    print("Manager accounts: M001 to M010")
    print("HR accounts: H001 to H010")
    print("Password pattern: Intelli@<LoginID>")
    print("Password storage: scrypt$<salt_hex>$<digest_hex>")
    print("All business-data tables remain empty.")


if __name__ == "__main__":
    create_database()
