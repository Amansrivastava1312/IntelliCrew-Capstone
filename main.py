"""Standalone test app — just to see the resume upload page on localhost."""

import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from agent.resume_agent import resume_agent          # compiled LangGraph agent

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Resume Upload Test")
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))


# ---------- page ----------
@app.get("/", response_class=HTMLResponse)
def resume_page(request: Request):
    # open the resume upload page directly
    return templates.TemplateResponse(request=request, name="resume.html", context={})


@app.post("/api/process-resume")
async def process_resume(
    file: UploadFile = File(...),
    full_name: str = Form(...),
    department: str = Form(...),
    designation: str = Form(...),
    employee_id: Optional[str] = Form(None),      # nvarchar, optional (sent only on re-submit)
):
    # keep the original extension (.pdf / .docx)
    ext = os.path.splitext(file.filename)[1].lower()

    # 1. save uploaded file with a TEMP name first (id not known yet)
    temp_path = os.path.join(UPLOAD_DIR, f"_tmp_{file.filename}")
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 2. build state — seed employee_id only if the user typed it in the form
    state = {
        "file_path": temp_path,
        "full_name": full_name,
        "department": department,
        "designation": designation,
        "raw_text": "",
        "extracted": {"employee_id": employee_id} if employee_id else {},
        "employee_id": None,
        "status": "started",
    }

    # 3. run the agent (load → extract → check → employee → skills → embed)
    result = resume_agent.invoke(state)

    # 4. if the resume had no id, ask the user — clean up the temp file
    if result["status"] == "need_employee_id":
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {
            "status": "need_employee_id",
            "message": "No Employee ID found in the resume. Please enter it manually.",
        }

    # 5. success → RENAME the temp file to <employee_id>.<ext>
    final_emp_id = result.get("employee_id")
    final_path = os.path.join(UPLOAD_DIR, f"{final_emp_id}{ext}")

    # if a file with that id already exists, overwrite it
    if os.path.exists(final_path):
        os.remove(final_path)
    os.rename(temp_path, final_path)

    return {
        "status": result["status"],
        "employee_id": final_emp_id,
        "saved_file": os.path.basename(final_path),      # e.g. "E1001.pdf"
        "skills_found": len(result.get("extracted", {}).get("skills", [])),
    }