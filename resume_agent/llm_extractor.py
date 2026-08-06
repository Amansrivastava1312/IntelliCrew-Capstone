import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

PROMPT = """
You are an HR resume parser. From the resume text below, return JSON ONLY.

Rules:
- "employee_id": the identifier EXACTLY as written (STRING, e.g. "EMP001").
  Look for labels like "EmployeeId", "Employee ID", "Emp Id". If none, use null.
- "full_name": the candidate's full name (usually the top heading).
- "department": the department/team if stated, else infer from role, else null.
- "designation": the job title / role (e.g. "Software Engineer"). If none, null.
- "manager_id": the manager's identifier EXACTLY as written (STRING, e.g. "M001").
  Look for labels like "ManagerId", "Manager ID", "Reports To", "Reporting Manager". If none, use null.
- "location": the work location / city / office (e.g. "Bengaluru"). If none, null.
- "joining_date": the date of joining in YYYY-MM-DD format if possible.
  Look for labels like "Joining Date", "Date of Joining", "DOJ", "Joined On". If none, use null.
- Return ONLY valid JSON, no extra text.

{{
  "employee_id": "string or null",
  "full_name": "string or null",
  "department": "string or null",
  "designation": "string or null",
  "manager_id": "string or null",
  "location": "string or null",
  "joining_date": "string or null",
  "email": "string or null",
  "skills": [
    {{"skill_name": "Python", "category": "Programming",
      "proficiency_level": "Expert", "years_experience": 3}}
  ]
}}

Resume text:
{resume_text}
"""


def extract_info(raw_text: str, model_name: str = "gemini-3.1-flash-lite") -> dict:
    """Send resume text to Gemini and get structured JSON back."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        google_api_key=api_key,
    )

    resp = llm.invoke(PROMPT.format(resume_text=raw_text[:6000]))

    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        start = resp.content.find("{")
        end = resp.content.rfind("}") + 1
        return json.loads(resp.content[start:end])