from langgraph.graph import END, START, StateGraph
from typing import TypedDict, Any

from skill_analyze.llm_extractor import (
    generate_employee_description,
    generate_project_skill_gap_report,
)
from skill_analyze.skill_match import get_matches


class MatchingState(TypedDict, total=False):
    project_id: int
    raw_result: dict
    employees: list
    skill_gap_report: str
    response: dict
    error: str


# 1. fetch matches from skill_match.py
def fetch_matches_node(state):
    project_id = state.get("project_id")

    if not project_id or project_id <= 0:
        return {"error": "A valid Project ID is required."}

    try:
        return {"raw_result": get_matches(project_id)}
    except (ValueError, FileNotFoundError) as error:
        return {"error": str(error)}
    except Exception as error:
        print("Employee matching failed:", error)
        return {"error": "Unable to generate employee matches."}


# 2. add LLM descriptions + one skill-gap report
def generate_descriptions_node(state):
    if state.get("error"):
        return {}

    raw_result = state["raw_result"]
    project = raw_result["project"]

    employees = []
    for emp in raw_result["matches"]:
        description = generate_employee_description(project=project, employee=emp)
        employees.append({
            "employee_id": emp["employee_id"],
            "employee_name": emp["full_name"],
            "email": emp["email"],
            "rank": emp["rank"],
            "matching_percentage": emp["match_percentage"],
            "matched_count": emp["matched_count"],
            "required_count": emp["required_count"],
            "matched_skills": emp["matched_skills"],
            "missing_skills": emp["missing_skills"],
            "description": description,
        })

    skill_gap_report = generate_project_skill_gap_report(
        project=project, employees=employees
    )

    return {"employees": employees, "skill_gap_report": skill_gap_report}


# 3. build the final response
def prepare_response_node(state):
    if state.get("error"):
        return {
            "response": {
                "success": False,
                "project_id": state.get("project_id"),
                "message": state["error"],
                "employees": [],
                "skill_gap_report": "",
            }
        }

    project = state["raw_result"]["project"]
    return {
        "response": {
            "success": True,
            "message": "Employee ranking and skill-gap report generated successfully.",
            "project": {
                "project_id": project["project_id"],
                "project_name": project["project_name"],
            },
            "total_employees": len(state["employees"]),
            "employees": state["employees"],
            "skill_gap_report": state["skill_gap_report"],
        }
    }


def create_matching_agent():
    graph = StateGraph(MatchingState)

    graph.add_node("fetch_matches", fetch_matches_node)
    graph.add_node("generate_descriptions", generate_descriptions_node)
    graph.add_node("prepare_response", prepare_response_node)

    graph.add_edge(START, "fetch_matches")
    graph.add_edge("fetch_matches", "generate_descriptions")
    graph.add_edge("generate_descriptions", "prepare_response")
    graph.add_edge("prepare_response", END)

    return graph.compile()


matching_agent = create_matching_agent()




