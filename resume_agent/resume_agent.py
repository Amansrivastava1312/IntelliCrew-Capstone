from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from resume_agent.db import upsert_employee, get_or_create_skill, add_employee_skill
from document_loader.doc_loader import load_text, embed_text
from resume_agent.llm_extractor import extract_info


# shared state passed between nodes
class ResumeState(TypedDict):
    file_path: str
    raw_text: str
    extracted: dict
    employee_id: Optional[str]      # nvarchar → string (e.g. "EMP001")
    status: str


# 1. load raw text
def node_load(state):
    state["raw_text"] = load_text(state["file_path"])
    return state


# 2. LLM structured extraction (name/dept/designation/id/skills all from resume)
def node_extract(state):
    parsed = extract_info(state["raw_text"])
    # if the user already supplied an employee_id (manual re-submit), keep it
    if state["extracted"].get("employee_id"):
        parsed["employee_id"] = state["extracted"]["employee_id"]
    state["extracted"] = parsed
    return state


# 3. check if employee_id exists — branch point
def node_check_id(state):
    eid = state["extracted"].get("employee_id")
    if not eid or str(eid).strip() == "":
        state["status"] = "need_employee_id"
    return state


def route_after_check(state):
    return "stop" if state["status"] == "need_employee_id" else "continue"


# 4. insert / get employee — all fields now come from extracted
def node_employee(state):
    ex = state["extracted"]
    state["employee_id"] = upsert_employee(
        ex.get("full_name"),
        ex.get("email"),
        ex.get("department"),
        ex.get("designation"),
        employee_id=ex.get("employee_id"),
    )
    return state


# 5. insert skills + link in employee_skills
def node_skills(state):
    emp_id = state["employee_id"]
    for sk in state["extracted"].get("skills", []):
        skill_id = get_or_create_skill(sk["skill_name"].strip(), sk.get("category"))
        add_employee_skill(
            emp_id, skill_id, sk.get("proficiency_level"), sk.get("years_experience")
        )
    return state


# 6. embed raw text into Chroma
def node_embed(state):
    embed_text(state["raw_text"], state["employee_id"], state["extracted"].get("full_name"))
    state["status"] = "done"
    return state


def build_graph():
    g = StateGraph(ResumeState)
    g.add_node("load", node_load)
    g.add_node("extract", node_extract)
    g.add_node("check", node_check_id)
    g.add_node("employee", node_employee)
    g.add_node("skills", node_skills)
    # g.add_node("embed", node_embed)

    g.set_entry_point("load")
    g.add_edge("load", "extract")
    g.add_edge("extract", "check")
    g.add_conditional_edges("check", route_after_check,
                            {"continue": "employee", "stop": END})
    g.add_edge("employee", "skills")
    g.add_edge("skills",END)
    # g.add_edge("embed", END)
    return g.compile()


resume_agent = build_graph()