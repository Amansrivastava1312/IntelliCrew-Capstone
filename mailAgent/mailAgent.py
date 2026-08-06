import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI


# ---------------------------------------------------------------------------
# 1. STATE
# ---------------------------------------------------------------------------
class MailState(TypedDict):
    employee_id: str
    project_name: str
    employee_name: str
    manager_name: str
    selection_reason: str    # reason from DB, comes into the prompt
    employee_email: str      # recipient (jisko mail bhejni hai)
    email_subject: str       # filled by the LLM
    email_body: str          # filled by the LLM
    send_status: str         # filled by send_email node


# ---------------------------------------------------------------------------
# 2. LOAD KEYS FROM .env
# ---------------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
sender_email = os.getenv("SENDER_EMAIL")     # aapka gmail
app_password = os.getenv("SENDER_PASSWORD")     # 16-char gmail app password


def get_llm():
    """Returns the Gemini LLM model."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0,
        api_key=api_key,
    )
    return llm


# ---------------------------------------------------------------------------
# 3. STRUCTURED OUTPUT (forces LLM to return subject + body)
# ---------------------------------------------------------------------------
class EmailContent(BaseModel):
    subject: str = Field(description="A short, formal subject line")
    body: str = Field(description="The full formal email body")


# ---------------------------------------------------------------------------
# 4. NODE 1 -> generate the email text
# ---------------------------------------------------------------------------
def generate_email(state: MailState):
    """Uses the LLM to write the email subject and body."""
    llm = get_llm().with_structured_output(EmailContent)

    prompt = f"""
Write a short, formal PROJECT ASSIGNMENT email for a company called IntelliCrew.

Details:
Employee Name: {state["employee_name"]}
Employee ID: {state["employee_id"]}
Project Name: {state["project_name"]}
Manager Name: {state["manager_name"]}
Selection Reason: {state["selection_reason"]}

Rules:
- Greet the employee by name.
- Clearly say that {state["manager_name"]} has selected them for the project "{state["project_name"]}".
- In one or two lines, explain WHY the employee was selected, based on this reason: {state["selection_reason"]}.
- Mention their Employee ID ({state["employee_id"]}) once.
- Keep the body under 120 words.
- Sign off as "IntelliCrew HR Team".
- Return only the subject and the body.
"""

    result = llm.invoke(prompt)

    return {
        "email_subject": result.subject,
        "email_body": result.body,
    }


# ---------------------------------------------------------------------------
# 5. NODE 2 -> actually SEND the email via Gmail SMTP
# ---------------------------------------------------------------------------
def send_email(state: MailState):
    """Sends the generated email using Gmail SMTP."""

    # Build the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = state["employee_email"]
    message["Subject"] = state["email_subject"]
    message.attach(MIMEText(state["email_body"], "plain"))

    try:
        # Connect to Gmail's SMTP server (SSL, port 465)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(message)

        print(f"✅ Email sent successfully to {state['employee_email']}")
        return {"send_status": "sent"}

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return {"send_status": f"failed: {e}"}


# ---------------------------------------------------------------------------
# 6. GRAPH
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(MailState)

    graph.add_node("generate_email", generate_email)
    graph.add_node("send_email", send_email)

    graph.add_edge(START, "generate_email")
    graph.add_edge("generate_email", "send_email")
    graph.add_edge("send_email", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# 7. Quick test if run directly
# ---------------------------------------------------------------------------
# if __name__ == "__main__":
#     app = build_graph()
#     test_state = {
#         "employee_id": "IN93412",
#         "project_name": "IntelliCrew HR Automation",
#         "employee_name": "Shubham Sahadev Prabhu",
#         "manager_name": "Nikita Dash",
#         "employee_email": "shubhamprabhu02@gmail.com",
#         "email_subject": "",
#         "email_body": "",
#         "send_status": "",
#     }
#     final = app.invoke(test_state)
#     print("Subject:", final["email_subject"])
#     print("Status :", final["send_status"])
