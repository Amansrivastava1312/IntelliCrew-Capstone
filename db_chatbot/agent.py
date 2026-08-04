import json
from typing import TypedDict, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from config import settings
from db_chatbot.tools import validate_sql, execute_sql
from db_chatbot.db import get_all_table_names, get_schema_for_tables


# ---------------------------------------------------------------------------
# 1. The shared state that flows through every node
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    question: str                 # user's natural-language question
    tables: list                  # tables the LLM picked
    schema: str                   # SMALL schema text (only selected tables)
    sql: str                      # current SQL query
    rows: Optional[list]          # query results (on success)
    error: Optional[str]          # DB error message (on failure)
    attempts: int                 # how many fixes we've tried
    answer: str                   # final natural-language answer


# ---------------------------------------------------------------------------
# 2. The LLM (Gemini). temperature=0 => deterministic, precise output
# ---------------------------------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0,
)


def _clean_sql(raw: str) -> str:
    """Strip markdown fences like ```sql ... ``` that LLMs often add."""
    return raw.replace("```sql", "").replace("```", "").strip()


def _pick_tables(raw: str, valid_tables: list[str]) -> list:
    """Read the LLM's JSON reply and keep only REAL table names.
    Simple + safe: grab the [...] part, load it as JSON, filter to
    tables that actually exist. Returns [] if anything goes wrong.
    """
    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
        names = json.loads(raw[start:end])          # e.g. ["employees","skills"]
    except Exception:
        return []

    names = [str(n).lower() for n in names]
    # Keep real tables only, in their canonical order (drops hallucinations)
    return [t for t in valid_tables if t.lower() in names]


# ---------------------------------------------------------------------------
# 3. NODES
# ---------------------------------------------------------------------------
def select_tables(state: AgentState) -> AgentState:
    """
    Step 1: send ONLY the table names + question to the LLM.
    Step 2: keep the real tables it returns.
    Step 3: fetch the schema for ONLY those tables.
    """
    all_tables = get_all_table_names()

    prompt = f"""You are a database assistant.
Your job: pick the tables needed to answer the question.

Available tables:
{", ".join(all_tables)}

Question: {state['question']}

Rules:
- Return ONLY a JSON array of table names, nothing else.
- Use the exact table names from the list above.
- Include every table needed for JOINs.
- Do not add explanations or markdown.

Example output: ["employees", "skills"]"""

    raw = llm.invoke(prompt).content
    tables = _pick_tables(raw, all_tables)

    # Fallback: if nothing valid came back, use all tables (never break)
    if not tables:
        tables = all_tables

    state["tables"] = tables
    state["schema"] = get_schema_for_tables(tables)
    return state


def generate_sql(state: AgentState) -> AgentState:
    """LLM writes the first SQL query from the question and SMALL schema."""
    prompt = f"""You are an expert SQLite analyst.
Given the schema and a question, write ONE valid SQLite SELECT query.
Return ONLY the SQL, no explanation, no markdown.

Schema:
{state['schema']}

Question: {state['question']}

SQL:"""
    state["sql"] = _clean_sql(llm.invoke(prompt).content)
    return state


def validate_node(state: AgentState) -> AgentState:
    """Run the safety guardrail. If unsafe, record it as an error."""
    is_safe, reason = validate_sql(state["sql"])
    state["error"] = None if is_safe else f"BLOCKED: {reason}"
    return state


def execute_node(state: AgentState) -> AgentState:
    """Run the SQL. Store rows on success, or the error on failure."""
    if state.get("error"):          # validation already blocked it
        return state

    result = execute_sql(state["sql"])
    if result["ok"]:
        state["rows"] = result["rows"]
        state["error"] = None
    else:
        state["error"] = result["error"]
    return state


def fix_sql(state: AgentState) -> AgentState:
    """LLM rewrites the broken SQL using the exact DB error message."""
    state["attempts"] += 1
    prompt = f"""The following SQLite query failed.
Fix it. Return ONLY the corrected SQL, no explanation, no markdown.

Schema:
{state['schema']}

Question: {state['question']}

Broken SQL:
{state['sql']}

Error message:
{state['error']}

Corrected SQL:"""
    state["sql"] = _clean_sql(llm.invoke(prompt).content)
    state["error"] = None           # clear so we retry execution fresh
    return state


def format_answer(state: AgentState) -> AgentState:
    """LLM turns the raw rows into a friendly, readable answer."""
    prompt = f"""Answer the user's question using the SQL result below.
Be concise and clear.

Question: {state['question']}
SQL used: {state['sql']}
Result rows: {state['rows']}

Answer:"""
    state["answer"] = llm.invoke(prompt).content.strip()
    return state


# ---------------------------------------------------------------------------
# 4. CONDITIONAL EDGE: decide what to do after execute
# ---------------------------------------------------------------------------
def route_after_execute(state: AgentState) -> str:
    """
    error + attempts left -> fix
    error + no attempts   -> give up
    no error              -> format the answer
    """
    if state.get("error"):
        if state["attempts"] < settings.MAX_FIX_ATTEMPTS:
            return "fix"
        return "give_up"
    return "answer"


def give_up(state: AgentState) -> AgentState:
    """After max retries, return a graceful message instead of crashing."""
    state["answer"] = (
        "Sorry, I couldn't build a working query for that. "
        f"Last error: {state['error']}"
    )
    state["rows"] = []
    return state


# ---------------------------------------------------------------------------
# 5. BUILD THE GRAPH
# ---------------------------------------------------------------------------
def build_agent():
    g = StateGraph(AgentState)

    g.add_node("select_tables", select_tables)
    g.add_node("generate_sql", generate_sql)
    g.add_node("validate", validate_node)
    g.add_node("execute", execute_node)
    g.add_node("fix_sql", fix_sql)
    g.add_node("format_answer", format_answer)
    g.add_node("give_up", give_up)

    g.set_entry_point("select_tables")             # start by picking tables
    g.add_edge("select_tables", "generate_sql")
    g.add_edge("generate_sql", "validate")
    g.add_edge("validate", "execute")

    g.add_conditional_edges(
        "execute",
        route_after_execute,
        {"fix": "fix_sql", "answer": "format_answer", "give_up": "give_up"},
    )

    g.add_edge("fix_sql", "execute")               # self-correcting loop
    g.add_edge("format_answer", END)
    g.add_edge("give_up", END)

    return g.compile()


# Compile once at import so the API reuses it
agent = build_agent()


def ask_agent(question: str) -> dict:
    """
    Public entry point used by the API.
    Runs the full agent and returns the picked tables, sql, rows, and answer.
    """
    initial: AgentState = {
        "question": question,
        "tables": [],
        "schema": "",       # filled by the select_tables node
        "sql": "",
        "rows": None,
        "error": None,
        "attempts": 0,
        "answer": "",
    }
    final = agent.invoke(initial)
    return {
        "question": question,
        "tables": final.get("tables", []),   # handy to show in the UI/debug
        "sql": final["sql"],
        "rows": final.get("rows") or [],
        "answer": final["answer"],
    }