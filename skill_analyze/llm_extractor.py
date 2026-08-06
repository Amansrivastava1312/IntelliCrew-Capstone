from __future__ import annotations

import os
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


EMPLOYEE_PROMPT = """
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


SKILL_GAP_REPORT_PROMPT = """
You are an HR project skill-gap analysis assistant.

Analyze the skill-gap information of all ranked employees for one project and
create one consolidated skill-gap report for that project.

Rules:
- Use only the supplied project and employee matching information.
- Do not modify ranks, percentages, skill counts, or skill names.
- Do not invent employee experience, performance, qualifications, or behavior.
- Identify the most frequently missing required skills across the employees.
- Mention skills that have strong coverage across the employee group.
- Briefly explain the overall readiness of the employee group.
- Mention important training or upskilling areas based only on the missing skills.
- Do not make a final hiring, allocation, or promotion decision.
- Write one concise professional report of approximately 120 to 180 words.
- Return only the report text with no JSON and no extra heading.

Project name: {project_name}
Required project skills: {required_skills}
Total employees analyzed: {total_employees}

Employee skill-gap records:
{employee_records}
"""


def get_llm(model_name: str) -> ChatGoogleGenerativeAI | None:
    """Create and return the Gemini model."""

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return None

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        google_api_key=api_key,
    )


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
        gap_text = (
            "The identified skill gaps are "
            + ", ".join(missing_skills)
            + "."
        )
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
    """Generate a short description for one ranked employee."""

    required_skills = project.get("required_skills", [])
    matched_skills = employee.get("matched_skills", [])
    missing_skills = employee.get("missing_skills", [])

    prompt = EMPLOYEE_PROMPT.format(
        project_name=project.get("project_name", "Unknown project"),
        required_skills=(
            ", ".join(required_skills)
            if required_skills
            else "None"
        ),
        employee_id=employee.get("employee_id", "Unknown"),
        employee_name=employee.get("full_name", "Unknown employee"),
        rank=employee.get("rank", "Unknown"),
        matching_percentage=employee.get("match_percentage", 0),
        matched_count=employee.get("matched_count", 0),
        required_count=employee.get("required_count", 0),
        matched_skills=(
            ", ".join(matched_skills)
            if matched_skills
            else "None"
        ),
        missing_skills=(
            ", ".join(missing_skills)
            if missing_skills
            else "None"
        ),
    )

    llm = get_llm(model_name)

    if not llm:
        print("Gemini API key was not found. Using fallback description.")
        return fallback_description(employee)

    try:
        response = llm.invoke(prompt)
        description = str(response.content).strip()

        return description or fallback_description(employee)

    except Exception as error:
        print(
            f"Gemini description failed for "
            f"{employee.get('employee_id')}: {error}"
        )
        return fallback_description(employee)


def fallback_skill_gap_report(
    project: dict[str, Any],
    employees: list[dict[str, Any]],
) -> str:
    """Create a deterministic project skill-gap report."""

    if not employees:
        return (
            "No active employee records were available for project "
            "skill-gap analysis."
        )

    missing_skill_counts = Counter()
    matched_skill_counts = Counter()

    for employee in employees:
        missing_skill_counts.update(employee.get("missing_skills", []))
        matched_skill_counts.update(employee.get("matched_skills", []))

    total_employees = len(employees)

    frequent_gaps = [
        f"{skill} ({count}/{total_employees} employees)"
        for skill, count in missing_skill_counts.most_common()
    ]

    strongest_skills = [
        f"{skill} ({count}/{total_employees} employees)"
        for skill, count in matched_skill_counts.most_common()
    ]

    gap_text = (
        ", ".join(frequent_gaps)
        if frequent_gaps
        else "no recurring required skill gaps"
    )

    coverage_text = (
        ", ".join(strongest_skills)
        if strongest_skills
        else "no common matched skills"
    )

    average_match = round(
        sum(
            employee.get("matching_percentage", 0)
            for employee in employees
        ) / total_employees,
        2,
    )

    return (
        f"For {project.get('project_name', 'the selected project')}, "
        f"{total_employees} active employees were analyzed with an average "
        f"skill match of {average_match}%. The strongest skill coverage is "
        f"{coverage_text}. The recurring skill gaps are {gap_text}. "
        f"These missing required skills represent the main areas for focused "
        f"training or upskilling before project allocation. Final employee "
        f"selection should be completed by the manager after reviewing the "
        f"individual rankings and skill evidence."
    )


def generate_project_skill_gap_report(
    project: dict[str, Any],
    employees: list[dict[str, Any]],
    model_name: str = "gemini-3.5-flash-lite",
) -> str:
    """Generate one consolidated skill-gap report for the project."""

    if not employees:
        return fallback_skill_gap_report(project, employees)

    employee_records = []

    for employee in employees:
        matched_skills = employee.get("matched_skills", [])
        missing_skills = employee.get("missing_skills", [])

        employee_records.append(
            (
                f"- Employee ID: {employee.get('employee_id', 'Unknown')}\n"
                f"  Employee name: {employee.get('employee_name', 'Unknown')}\n"
                f"  Rank: {employee.get('rank', 'Unknown')}\n"
                f"  Matching percentage: "
                f"{employee.get('matching_percentage', 0)}%\n"
                f"  Matched count: "
                f"{employee.get('matched_count', 0)}/"
                f"{employee.get('required_count', 0)}\n"
                f"  Matched skills: "
                f"{', '.join(matched_skills) if matched_skills else 'None'}\n"
                f"  Missing skills: "
                f"{', '.join(missing_skills) if missing_skills else 'None'}"
            )
        )

    required_skills = project.get("required_skills", [])

    prompt = SKILL_GAP_REPORT_PROMPT.format(
        project_name=project.get("project_name", "Unknown project"),
        required_skills=(
            ", ".join(required_skills)
            if required_skills
            else "None"
        ),
        total_employees=len(employees),
        employee_records="\n\n".join(employee_records),
    )

    llm = get_llm(model_name)

    if not llm:
        print("Gemini API key was not found. Using fallback skill-gap report.")
        return fallback_skill_gap_report(project, employees)

    try:
        response = llm.invoke(prompt)
        report = str(response.content).strip()

        return report or fallback_skill_gap_report(
            project,
            employees,
        )

    except Exception as error:
        print(f"Gemini skill-gap report generation failed: {error}")

        return fallback_skill_gap_report(
            project,
            employees,
        )