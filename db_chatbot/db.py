from sqlalchemy import create_engine, inspect, text

from config import settings

# The single shared connection to the SQLite file
engine = create_engine(
    settings.DB_URL,
    connect_args={"check_same_thread": False},
)


def get_all_table_names() -> list[str]:
    """Return the list of all table names in the database."""
    return inspect(engine).get_table_names()


def get_schema_for_tables(tables: list[str]) -> str:
    """
    Build schema text for ONLY the given tables.
    This is what we feed the LLM instead of the whole database.
    Reads columns + foreign keys directly from the live DB each time.
    """
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    lines = []

    for table in tables:
        if table not in existing:
            continue

        lines.append(f"Table: {table}")

        # Columns (name + type)
        for col in inspector.get_columns(table):
            lines.append(f"  - {col['name']} ({col['type']})")

        # Foreign keys, so the LLM knows how to JOIN
        for fk in inspector.get_foreign_keys(table):
            src = ", ".join(fk["constrained_columns"])
            tgt_table = fk["referred_table"]
            tgt = ", ".join(fk["referred_columns"])
            lines.append(f"  FK: {src} -> {tgt_table}.{tgt}")

        lines.append("")  # blank line between tables

    return "\n".join(lines).strip()


def run_query(sql: str) -> list[dict]:
    """Execute a raw SELECT and return rows as a list of dictionaries."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = result.keys()
        rows = [dict(zip(columns, r)) for r in result.fetchall()]
    return rows
