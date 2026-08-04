from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel

from db_chatbot.agent import ask_agent
from db_chatbot.tools import schema_tool

app = FastAPI(title="IntelliCrew · Agentic Text-to-SQL")

# Serve CSS/JS files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


class QueryRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Serve the sidebar UI. userType decides which bars render."""
    # 🔑 change to "employee" ,"manager" to test, or read from DB/session/login later
    userType = "manager"

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "userType": userType}   # <-- passed to HTML
    )


@app.post("/api/query")
def query(req: QueryRequest):
    """Natural-language question -> SQL, rows, answer."""
    if not req.question.strip():
        return {"error": "Please enter a question."}
    return ask_agent(req.question)


@app.get("/api/schema")
def schema():
    """Return the DB schema (debugging / UI hint)."""
    return {"schema": schema_tool()}