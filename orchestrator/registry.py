"""Central registry of all agents. Each agent describes WHEN it should fire.
Add a new agent = add ONE entry here. No other file changes."""

from resume_agent.resume_agent import resume_agent
from video_summarization.summarize import summarizer_agent   # NEW
# from SkillAgent.skill_agent import skill_agent

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
}

DEFAULT_AGENT = "resume_agent"