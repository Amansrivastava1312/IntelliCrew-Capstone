"""Central registry of all agents. Each agent describes WHEN it should fire.
Add a new agent = add ONE entry here. No other file changes."""

from resume_agent.resume_agent import resume_agent
# from SkillAgent.skill_agent import skill_agent

AGENTS = {
    "resume_agent": {
        "agent": resume_agent,
        "description": "Extracts details from an employee resume PDF and stores them.",
        "keywords": ["resume", "cv", "upload"],
        "needs_file": True,          # fires when a file is attached
    },
    # "skill_agent": {
    #     "agent": skill_agent,
    #     "description": "Finds employees who match a given set of skills.",
    #     "keywords": ["skill", "who knows", "expert in", "find employee", "people who"],
    #     "needs_file": False,
    # },
    # later, e.g.:
    # "sql_agent": {
    #     "agent": sql_agent,
    #     "description": "Answers employee-data questions using text-to-SQL.",
    #     "keywords": ["how many", "list", "count", "query", "report"],
    #     "needs_file": False,
    # },
}

# used when nothing scores above 0
DEFAULT_AGENT = "resume_agent"