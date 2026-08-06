from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from skill_analyze.llm_extractor import generate_employee_description
from skill_analyze.skill_match import get_matches


class MatchingState(TypedDict, total=False):
    """State shared between the matching agent nodes."""

    project_id: int
    raw_result: dict[str, Any]
    employees: list[dict[str, Any]]
    response: dict[str, Any]
    error: str


def validate_project_node(state: MatchingState) -> dict[str, Any]:
    """Validate the selected project ID."""

    project_id = state.get("project_id")

    if project_id is None:
        return {"error": "Project ID is required."}

    if not isinstance(project_id, int):
        return {"error": "Project ID must be an integer."}

    if project_id <= 0:
        return {"error": "Project ID must be greater than zero."}

    return {"project_id": project_id}


def fetch_matches_node(state: MatchingState) -> dict[str, Any]:
    """Fetch employee matches using skill_match.py."""

    try:
        result = get_matches(state["project_id"])
        return {"raw_result": result}

    except (ValueError, FileNotFoundError) as error:
        return {"error": str(error)}

    except Exception as error:
        print(f"Employee matching failed: {error}")
        return {"error": "Unable to generate employee matches."}


def generate_descriptions_node(state: MatchingState) -> dict[str, Any]:
    """Add an LLM-generated description to every employee result."""

    raw_result = state["raw_result"]
    project = raw_result["project"]
    employees = []

    for employee in raw_result["matches"]:
        description = generate_employee_description(
            project=project,
            employee=employee,
        )

        employees.append(
            {
                "employee_id": employee["employee_id"],
                "employee_name": employee["full_name"],
                "email": employee["email"],
                "rank": employee["rank"],
                "matching_percentage": employee["match_percentage"],
                "matched_count": employee["matched_count"],
                "required_count": employee["required_count"],
                "matched_skills": employee["matched_skills"],
                "missing_skills": employee["missing_skills"],
                "description": description,
            }
        )

    return {"employees": employees}


def prepare_response_node(state: MatchingState) -> dict[str, Any]:
    """Prepare the final response for app.py."""

    if state.get("error"):
        return {
            "response": {
                "success": False,
                "project_id": state.get("project_id"),
                "message": state["error"],
                "employees": [],
            }
        }

    project = state["raw_result"]["project"]

    return {
        "response": {
            "success": True,
            "message": "Employee ranking generated successfully.",
            "project": {
                "project_id": project["project_id"],
                "project_name": project["project_name"],
            },
            "total_employees": len(state["employees"]),
            "employees": state["employees"],
        }
    }


def route_next(state: MatchingState, success_node: str) -> str:
    """Route to the response node if an error exists."""

    if state.get("error"):
        return "prepare_response"

    return success_node


def route_after_validation(state: MatchingState) -> str:
    return route_next(state, "fetch_matches")


def route_after_matching(state: MatchingState) -> str:
    return route_next(state, "generate_descriptions")


def create_matching_agent():
    """Build and compile the matching workflow."""

    graph = StateGraph(MatchingState)

    graph.add_node("validate_project", validate_project_node)
    graph.add_node("fetch_matches", fetch_matches_node)
    graph.add_node("generate_descriptions", generate_descriptions_node)
    graph.add_node("prepare_response", prepare_response_node)

    graph.add_edge(START, "validate_project")

    graph.add_conditional_edges(
        "validate_project",
        route_after_validation,
        {
            "fetch_matches": "fetch_matches",
            "prepare_response": "prepare_response",
        },
    )

    graph.add_conditional_edges(
        "fetch_matches",
        route_after_matching,
        {
            "generate_descriptions": "generate_descriptions",
            "prepare_response": "prepare_response",
        },
    )

    graph.add_edge("generate_descriptions", "prepare_response")
    graph.add_edge("prepare_response", END)

    return graph.compile()


matching_agent = create_matching_agent()


def run_matching_agent(project_id: int) -> dict[str, Any]:
    """Run the matching agent for the selected project."""

    final_state = matching_agent.invoke({"project_id": project_id})
    return final_state["response"]


if __name__ == "__main__":
    from pprint import pprint

    result = run_matching_agent(project_id=2)
    pprint(result, sort_dicts=False)