"""Standalone agent-logging DB module — separate from the main db.py.
Creates its own agent_logs table and provides insert/read helpers.
Uses the SAME SQLite file (employee_records.db) so everything stays in one db.
"""

import sqlite3
from pathlib import Path

# this file lives inside a package folder, go up ONE level to reach project root, then data/
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"   # same db as data_seed.py


# ---------- table definition (self-contained) ----------
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS agent_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name VARCHAR(60) NOT NULL,       -- which agent ran
    chosen_by VARCHAR(20),                 -- 'llm' / 'keyword' / 'override' / 'run'
    reason TEXT,                           -- LLM reason or note
    user_input TEXT,                       -- the request text (if any)
    has_file INTEGER NOT NULL DEFAULT 0,   -- 1 if a file was attached
    source TEXT,                           -- file path / link / query
    status VARCHAR(30),                    -- final status: done / need_employee_id / error
    handled_by VARCHAR(60),                -- agent that returned the result
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent   ON agent_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created ON agent_logs(created_at);
"""


def get_conn():
    # open a connection, rows accessible by column name
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the agent_logs table + indexes if they don't exist."""
    conn = get_conn()
    conn.executescript(CREATE_SQL)
    conn.commit()
    conn.close()


# ---------- write ----------
def log_agent_run(agent_name, chosen_by=None, reason=None,
                  user_input=None, has_file=False, source=None,
                  status=None, handled_by=None):
    """Insert one row into agent_logs. Returns log_id."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO agent_logs
           (agent_name, chosen_by, reason, user_input, has_file,
            source, status, handled_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (agent_name, chosen_by, reason, user_input,
         1 if has_file else 0, source, status, handled_by),
    )
    conn.commit()
    log_id = cur.lastrowid
    conn.close()
    return log_id


# ---------- read ----------
def get_agent_logs(limit=50):
    """Return the most recent agent logs (newest first)."""
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT log_id, agent_name, chosen_by, reason, user_input,
                  has_file, source, status, handled_by, created_at
           FROM agent_logs
           ORDER BY created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# auto-create the table the first time this module is imported
init_db()
