import sqlite3
from pathlib import Path

# call the mail graph directly — a backend step doesn't need the LLM router
from mailAgent.mailAgent import build_graph

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"

# build the compiled graph once, when this module is imported
mail_graph = build_graph()


def run_mail_agent() -> dict:
    """Send project-assignment mails for every project_allocation row with is_sent = 0."""
    results = []

    # 1. pull every selection whose mail hasn't been sent yet
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM project_allocation WHERE is_sent = 0"
        ).fetchall()

    # ---------- loop + mail each selected employee ----------
    for row in rows:
        # employee_name is NOT stored in project_allocation -> fetch it from employees
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.row_factory = sqlite3.Row
            emp = conn.execute(
                "SELECT full_name FROM employees WHERE employee_id = ?",
                (row["employee_id"],),
            ).fetchone()

        # same keys as mailAgent's MailState
        state = {
            "employee_id":    row["employee_id"],
            "project_name":   row["project_name"],
            "employee_name":  emp["full_name"] if emp else "",
            "manager_name":   row["manager_name"],
            "selection_reason": row["selection_reason"],
            "employee_email": row["employee_email"],   # recipient
            "email_subject":  "",
            "email_body":     "",
            "send_status":    "",
        }

        # invoke the mail graph directly (generate_email -> send_email)
        result = mail_graph.invoke(state)

        # 2. mark as sent only if the mail actually went out (won't re-send next time)
        if result.get("send_status") == "sent":
            with sqlite3.connect(DATABASE_FILE) as conn:
                conn.execute(
                    "UPDATE project_allocation SET is_sent = 1 WHERE id = ?",
                    (row["id"],),
                )
                conn.commit()

        results.append({
            "id":          row["id"],
            "employee_id": row["employee_id"],
            "to":          result.get("employee_email"),
            "subject":     result.get("email_subject"),
            "status":      result.get("send_status"),
        })

    return {
        "total": len(rows),
        "sent": sum(1 for r in results if r["status"] == "sent"),
        "results": results,
    }
