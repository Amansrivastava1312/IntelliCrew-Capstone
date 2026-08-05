import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from orchestrator.registry import AGENTS, DEFAULT_AGENT

load_dotenv()


PROMPT = """
You are a router for an HR platform. Pick the ONE best agent for the user's request.
Return JSON ONLY.

Available agents:
{agent_list}

Rules:
- "agent": must be EXACTLY one of these names: {valid_names}
- Pick the agent whose description best matches the user's request.
- If a file is attached and the request is about a resume, prefer the resume agent.
- If the request is about a video or a link, prefer the summarizer agent.
- Return ONLY valid JSON, no extra text.

{{
  "agent": "one of {valid_names}",
  "reason": "short reason why"
}}

User request: "{user_input}"
A file is attached: {has_file}
"""


def _keyword_fallback(text: str, has_file: bool) -> str:
    """Rule-based backup — used only if the LLM call fails."""
    text = (text or "").lower()
    best_agent, best_score = DEFAULT_AGENT, 0
    for name, info in AGENTS.items():
        score = sum(1 for kw in info.get("keywords", []) if kw in text)
        if info.get("needs_file") and has_file:
            score += 2
        if score > best_score:
            best_score, best_agent = score, name
    return best_agent


# def choose_agent(user_input: str = "", has_file: bool = False,
#                  agent: str | None = None,
#                  model_name: str = "gemini-3.1-flash-lite") -> str:
#     """Ask Gemini which agent should handle the request."""

#     # 0. explicit override always wins (no LLM needed)
#     if agent and agent in AGENTS:
#         return agent

#     # 1. build the agent list + valid names from the registry (auto-updates)
#     valid_names = list(AGENTS.keys())
#     agent_list = "\n".join(f"- {name}: {info['description']}"
#                            for name, info in AGENTS.items())

#     api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

#     llm = ChatGoogleGenerativeAI(
#         model=model_name,
#         temperature=0,
#         google_api_key=api_key,
#     )

#     try:
#         resp = llm.invoke(PROMPT.format(
#             agent_list=agent_list,
#             valid_names=valid_names,
#             user_input=user_input,
#             has_file=has_file,
#         ))

#         # parse JSON (same pattern as your extract_info)
#         try:
#             data = json.loads(resp.content)
#         except json.JSONDecodeError:
#             start = resp.content.find("{")
#             end = resp.content.rfind("}") + 1
#             data = json.loads(resp.content[start:end])

#         choice = data.get("agent", "")

#         # validate the LLM's answer against real agent names
#         if choice in AGENTS:
#             print(f"[router] LLM picked '{choice}' — {data.get('reason', '')}")
#             return choice

#     except Exception as e:
#         print("LLM router failed, using keyword fallback:", e)

#     # safety net
#     return _keyword_fallback(user_input, has_file)





from orchestrator.agent_log_helper import log_agent_run   # adjust path to where db.py lives


def choose_agent(user_input: str = "", has_file: bool = False,
                 agent: str | None = None,
                 model_name: str = "gemini-3.1-flash-lite") -> str:

    # 0. explicit override always wins
    if agent and agent in AGENTS:
        log_agent_run(agent, chosen_by="override",
                      user_input=user_input, has_file=has_file)
        return agent

    valid_names = list(AGENTS.keys())
    agent_list = "\n".join(f"- {name}: {info['description']}"
                           for name, info in AGENTS.items())

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, google_api_key=api_key)

    try:
        resp = llm.invoke(PROMPT.format(
            agent_list=agent_list, valid_names=valid_names,
            user_input=user_input, has_file=has_file,
        ))
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            start = resp.content.find("{")
            end = resp.content.rfind("}") + 1
            data = json.loads(resp.content[start:end])

        choice = data.get("agent", "")
        if choice in AGENTS:
            log_agent_run(choice, chosen_by="llm",
                          reason=data.get("reason", ""),
                          user_input=user_input, has_file=has_file)
            print(f"[router] LLM picked '{choice}' — {data.get('reason', '')}")
            return choice

    except Exception as e:
        print("LLM router failed, using keyword fallback:", e)

    # safety net
    picked = _keyword_fallback(user_input, has_file)
    log_agent_run(picked, chosen_by="keyword",
                  user_input=user_input, has_file=has_file)
    return picked