from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


PROMPT = """
You are an employee-project skill matching assistant.

Create a short professional description explaining why the employee received
the given rank for the selected project.

Rules:
- Write no more than two short sentences.
- Use only the supplied project and employee information.
- Do not change the rank, matching percentage, or skill counts.
- Do not invent experience, qualifications, performance, or personality.
- Mention the employee's important matched skills.
- Briefly mention the missing skills or skill gaps.
- If there are no missing skills, clearly state that all required skills match.
- Return only the description with no heading, JSON, or extra text.

Project name: {project_name}
Required project skills: {required_skills}

Employee ID: {employee_id}
Employee name: {employee_name}
Rank: {rank}
Matching percentage: {matching_percentage}%
Matched skill count: {matched_count}/{required_count}
Matched skills: {matched_skills}
Missing skills: {missing_skills}
"""


def fallback_description(employee: dict[str, Any]) -> str:
    """Create a deterministic description when the Gemini call fails."""

    matched_skills = employee.get("matched_skills", [])
    missing_skills = employee.get("missing_skills", [])

    matched_text = (
        ", ".join(matched_skills)
        if matched_skills
        else "none of the required skills"
    )

    if missing_skills:
        gap_text = "The identified skill gaps are " + ", ".join(missing_skills) + "."
    else:
        gap_text = "All required project skills are matched."

    return (
        f"{employee.get('full_name', 'The employee')} is ranked "
        f"{employee.get('rank')} with a "
        f"{employee.get('match_percentage')}% match, covering "
        f"{employee.get('matched_count')} of "
        f"{employee.get('required_count')} required skills, including "
        f"{matched_text}. {gap_text}"
    )


def generate_employee_description(
    project: dict[str, Any],
    employee: dict[str, Any],
    model_name: str = "gemini-3.5-flash-lite",
) -> str:
    """Generate a short description for one ranked employee using Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Gemini API key was not found. Using fallback description.")
        return fallback_description(employee)

    required_skills = project.get("required_skills", [])
    matched_skills = employee.get("matched_skills", [])
    missing_skills = employee.get("missing_skills", [])

    prompt = PROMPT.format(
        project_name=project.get("project_name", "Unknown project"),
        required_skills=(
            ", ".join(required_skills) if required_skills else "None"
        ),
        employee_id=employee.get("employee_id", "Unknown"),
        employee_name=employee.get("full_name", "Unknown employee"),
        rank=employee.get("rank", "Unknown"),
        matching_percentage=employee.get("match_percentage", 0),
        matched_count=employee.get("matched_count", 0),
        required_count=employee.get("required_count", 0),
        matched_skills=(
            ", ".join(matched_skills) if matched_skills else "None"
        ),
        missing_skills=(
            ", ".join(missing_skills) if missing_skills else "None"
        ),
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            google_api_key=api_key,
        )

        response = llm.invoke(prompt)
        description = str(response.content).strip()

        if not description:
            return fallback_description(employee)

        return description

    except Exception as error:
        print(
            f"Gemini description failed for "
            f"{employee.get('employee_id')}: {error}"
        )
        return fallback_description(employee)
