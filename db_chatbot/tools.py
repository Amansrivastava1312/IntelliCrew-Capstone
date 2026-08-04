import re
from db_chatbot.db import get_schema_for_tables, run_query

# Keywords we never allow — this is read-only text-to-SQL, so only SELECT is fine
FORBIDDEN = [
    "insert", "update", "delete", "drop", "alter",
    "truncate", "create", "replace", "pragma", "attach",
]


def schema_tool() -> str:
    """Return the database schema text for the LLM to reason over."""
    return get_schema_for_tables()


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Guardrail. Returns (is_safe, reason).
    Rejects anything that is not a single read-only SELECT statement.
    """
    cleaned = sql.strip().strip(";").lower()

    # Must start with SELECT
    if not cleaned.startswith("select"):
        return False, "Only SELECT queries are allowed."

    # Block any forbidden keyword (word-boundary match to avoid false hits)
    for word in FORBIDDEN:
        if re.search(rf"\b{word}\b", cleaned):
            return False, f"Forbidden keyword detected: '{word}'."

    # Block multiple statements (stops SQL injection like: SELECT ..; DROP ..)
    if ";" in sql.strip().rstrip(";"):
        return False, "Multiple SQL statements are not allowed."

    return True, "ok"


def execute_sql(sql: str) -> dict:
    """
    Run the SQL and return a structured dict.
    On success: {"ok": True,  "rows": [...]}
    On failure: {"ok": False, "error": "the database error message"}
    The agent uses the error message to auto-fix the query.
    """
    try:
        rows = run_query(sql)
        return {"ok": True, "rows": rows}
    except Exception as e:
        return {"ok": False, "error": str(e)}
