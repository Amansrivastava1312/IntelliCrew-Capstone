import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

PROMPT = """
You are a workforce analytics writer for a company called IntelliCrew.
Using ONLY the JSON data below, write a clear, professional organization report.

Write these sections as plain text (use "- " for bullet points):
1. Executive Summary (3-4 sentences on workforce size, active staff, projects).
2. Project Portfolio (comment on in-progress vs planned vs completed, and allocation coverage).
3. Skill Landscape (top skills, where the org is strong, any gaps).
4. Bench & Utilization (comment on employees not allocated to any project).
5. Recommendations (3-4 actionable bullet points).

Rules:
- Be factual and only use numbers present in the JSON.
- Keep it concise and business-friendly. No markdown headers with '#'.
- Separate sections with a blank line and a plain title line ending with ':'.

Organization data (JSON):
{report_json}
"""


def generate_report_narrative(report_data: dict,
                              model_name: str = "gemini-3.1-flash-lite") -> str:
    """Send the aggregated data to Gemini and get a narrative report back."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.2,
        google_api_key=api_key,
    )

    resp = llm.invoke(
        PROMPT.format(report_json=json.dumps(report_data, indent=2))
    )
    return resp.content.strip()