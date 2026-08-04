"""IntelliCrew — Login + HR Resume Upload (single app)."""

import os
import shutil
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional

from fastapi import (
    Cookie, FastAPI, HTTPException, Request, Response, status,
    UploadFile, File, Form,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from security import verify_password

from Emp_DataAgent.resume_agent import resume_agent          # compiled LangGraph agent

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "data" / "employee_records.db"
COOKIE = "intellicrew_session_id"
HOURS = 8

UPLOAD_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="IntelliCrew")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

SESSIONS: dict[str, dict] = {}


# ---------- models ----------
class LoginRequest(BaseModel):
    login_type: Literal["manager", "hr"]
    user_id: str = Field(min_length=4, max_length=4)
    password: str = Field(min_length=1, max_length=128)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


# ---------- sessions ----------
def get_session(sid: str | None):
    s = SESSIONS.get(sid) if sid else None
    if s and s["expires"] > datetime.now(timezone.utc):
        return s
    SESSIONS.pop(sid, None) if sid else None
    return None


def require_session(sid: str | None):
    s = get_session(sid)
    if not s:
        raise HTTPException(401, "Please log in first.")
    return s


# ---------- pages ----------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request, sid: str | None = Cookie(None, alias=COOKIE)):
    if get_session(sid):
        return RedirectResponse("/home", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/home", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request, sid: str | None = Cookie(None, alias=COOKIE)):
    s = get_session(sid)
    if not s:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"userType": s["role"].lower(), "userId": s["user_id"], "userName": s["name"]},
    )


# ---------- auth API ----------
@app.post("/api/login")
def login(payload: LoginRequest, response: Response):
    uid = payload.user_id.strip().upper()

    if payload.login_type == "manager":
        prefix, role, table, id_column = "M", "MANAGER", "manager", "manager_id"
    else:
        prefix, role, table, id_column = "H", "HR", "hr", "hr_id"

    if not (uid.startswith(prefix) and uid[1:].isdigit()):
        raise HTTPException(400, f"ID must use the {prefix}001 format.")

    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        record = conn.execute(
            f"""
            SELECT {id_column} AS id, full_name AS name, password_hash
            FROM {table}
            WHERE {id_column} = ?
            """,
            (uid,),
        ).fetchone()

    if record is None or not verify_password(payload.password, record["password_hash"]):
        raise HTTPException(401, "Invalid login type, ID, or password.")

    sid = secrets.token_urlsafe(32)
    SESSIONS[sid] = {
        "user_id": record["id"],
        "role": role,
        "name": record["name"],
        "expires": datetime.now(timezone.utc) + timedelta(hours=HOURS),
    }
    response.set_cookie(COOKIE, sid, max_age=HOURS * 3600, httponly=True, samesite="lax", path="/")
    return {"message": "Login successful.", "role": role, "redirect_url": "/home"}


@app.post("/api/logout")
def logout(response: Response, sid: str | None = Cookie(None, alias=COOKIE)):
    SESSIONS.pop(sid, None) if sid else None
    response.delete_cookie(COOKIE, path="/")
    return {"message": "Logged out.", "redirect_url": "/"}


@app.get("/api/me")
def current_user(sid: str | None = Cookie(None, alias=COOKIE)):
    s = require_session(sid)
    return {"user_id": s["user_id"], "name": s["name"], "role": s["role"]}


# ---------- resume agent API (HR only) ----------
@app.post("/api/process-resume")
async def process_resume(
    file: UploadFile = File(...),
    employee_id: Optional[str] = Form(None),      # only on re-submit
    sid: str | None = Cookie(None, alias=COOKIE),
):
    s = require_session(sid)
    if s["role"] != "HR":
        raise HTTPException(403, "Only HR can upload resumes.")

    ext = os.path.splitext(file.filename)[1].lower()
    temp_path = os.path.join(UPLOAD_DIR, f"_tmp_{file.filename}")
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # only file_path + optional employee_id are seeded now
    state = {
        "file_path": temp_path,
        "raw_text": "",
        "extracted": {"employee_id": employee_id} if employee_id else {},
        "employee_id": None,
        "status": "started",
    }
    result = resume_agent.invoke(state)

    if result["status"] == "need_employee_id":
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"status": "need_employee_id",
                "message": "No Employee ID found in the resume. Please enter it manually."}

    final_emp_id = result.get("employee_id")
    final_path = os.path.join(UPLOAD_DIR, f"{final_emp_id}{ext}")
    if os.path.exists(final_path):
        os.remove(final_path)
    os.rename(temp_path, final_path)

    return {
        "status": result["status"],
        "employee_id": final_emp_id,
        "full_name": result["extracted"].get("full_name"),
        "designation": result["extracted"].get("designation"),
        "skills_found": len(result.get("extracted", {}).get("skills", [])),
    }
