import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

from mailAgent.send_agent import get_pending_employees, mark_as_sent


# ---------------------------------------------------------------------------
# 1. SHARED STATE
# ---------------------------------------------------------------------------
class MailState(TypedDict, total=False):
    status: str
    employees: list[dict]
    total: int
    sent: int
    failed: int
    results: list[dict]


# ---------------------------------------------------------------------------
# 2. LOAD KEYS FROM .env
# ---------------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
sender_email = os.getenv("SENDER_EMAIL")
app_password = os.getenv("SENDER_PASSWORD")


def get_llm():
    """Returns the Gemini LLM model."""
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0,
        api_key=api_key,
    )


# ---------------------------------------------------------------------------
# 3. STRUCTURED OUTPUT
# ---------------------------------------------------------------------------
class EmailContent(BaseModel):
    subject: str = Field(description="A short, formal subject line")
    body: str = Field(description="The full formal email body")


# ---------------------------------------------------------------------------
# 4. NODE 1: LOAD ALL PENDING EMPLOYEES
# ---------------------------------------------------------------------------
def load_employees(state: MailState) -> dict:
    """Load selected employees whose assignment emails are pending."""
    employees = get_pending_employees()

    return {
        "status": "loaded",
        "employees": employees,
        "total": len(employees),
        "sent": 0,
        "failed": 0,
        "results": [],
    }


# ---------------------------------------------------------------------------
# 5. NODE 2: GENERATE AND SEND EMAILS
# ---------------------------------------------------------------------------
def process_emails(state: MailState) -> dict:
    """Generate and send a project-assignment email to every employee."""
    llm = get_llm().with_structured_output(EmailContent)
    results = []

    for employee in state.get("employees", []):
        email_subject = ""

        try:
            prompt = f"""
Write a short and professional project allocation email.

Details:
Employee Name: {employee["employee_name"]}
Employee ID: {employee["employee_id"]}
Project Name: {employee["project_name"]}
Manager Name: {employee["manager_name"]}
Skills to Improve: {employee["selection_reason"]}

Requirements:
- Confirm that the employee has been allocated to the project.
- Mention the manager's name.
- Briefly mention the required skills the employee should strengthen.
- Politely ask the employee to complete the necessary upskilling.
- Keep the body under 80 words.
- Use supportive and professional language.
- Do not invent any information.
- Sign off as "IntelliCrew HR Team".
- Return only the subject and body.
"""

            email = llm.invoke(prompt)
            email_subject = email.subject

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = employee["employee_email"]
            message["Subject"] = email.subject
            message.attach(MIMEText(email.body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.send_message(message)

            mark_as_sent(employee["id"])
            send_status = "sent"
            print(f"Email sent successfully to {employee['employee_email']}")

        except Exception as error:
            send_status = f"failed: {error}"
            print(
                f"Failed to send email to "
                f"{employee.get('employee_email', '')}: {error}"
            )

        results.append({
            "id": employee["id"],
            "employee_id": employee["employee_id"],
            "to": employee["employee_email"],
            "subject": email_subject,
            "status": send_status,
        })

    sent_count = sum(
        1 for result in results if result["status"] == "sent"
    )

    return {
        "status": "completed",
        "total": len(results),
        "sent": sent_count,
        "failed": len(results) - sent_count,
        "results": results,
    }


# ---------------------------------------------------------------------------
# 6. GRAPH
# ---------------------------------------------------------------------------
def build_graph():
    """Build the batch mail graph used by the central orchestrator."""
    graph = StateGraph(MailState)

    graph.add_node("load_employees", load_employees)
    graph.add_node("process_emails", process_emails)

    graph.add_edge(START, "load_employees")
    graph.add_edge("load_employees", "process_emails")
    graph.add_edge("process_emails", END)

    return graph.compile()


# Compiled mail agent registered with the central orchestrator.
mail_agent = build_graph()
