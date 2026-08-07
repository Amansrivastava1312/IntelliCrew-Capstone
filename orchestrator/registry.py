from resume_agent.resume_agent import resume_agent
from video_summarization.summarize import summarizer_agent   
from skill_analyze.matching_agent import matching_agent
from report_agent.report_graph import report_agent           



AGENTS = {
    "resume_agent": {
        "agent": resume_agent,
        "description": "Extracts details from an employee resume PDF and stores them.",
        "keywords": ["resume", "cv", "upload"],
        "needs_file": True,
    },
    # NEW: fires on video keywords (works for BOTH a video file and a link)
    "summarizer_agent": {
        "agent": summarizer_agent,
        "description": "Transcribes and summarizes an uploaded video or a video/YouTube link.",
        "keywords": ["video", "summarize video", "youtube", "transcribe", "summary"],
        "needs_file": False,
    },

    "matching_agent": {
        "agent": matching_agent,
        "description": (
            "Matches active employees with a selected project, "
            "calculates skill-match percentages, ranks employees, "
            "and generates short ranking descriptions."
        ),
        "keywords": ["match employees", "employee matching", "project matching", "skill matching", "skill gap", "rank employees", "project requirement", "find employees for project"],
        "needs_file": False,
    },

    # NEW: fires on report keywords — builds the org-wide PDF report
    "report_agent": {
        "agent": report_agent,
        "description": (
            "Generates a centralized organization-wide PDF report "
            "covering projects, employees, skills, and allocations."
        ),
        "keywords": ["centralized report", "generate report", "organization report", "org report", "download report", "overall report", "company report"],
        "needs_file": False,
    },

}

DEFAULT_AGENT = "resume_agent"