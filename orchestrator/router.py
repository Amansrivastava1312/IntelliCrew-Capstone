"""Dynamic rule-based router. Reads triggers from the registry — no per-agent code.
Works the same whether you have 2 agents or 50."""

from orchestrator.registry import AGENTS, DEFAULT_AGENT


def choose_agent(user_input: str = "", has_file: bool = False) -> str:
    text = (user_input or "").lower()

    best_agent = DEFAULT_AGENT
    best_score = 0

    # loop over EVERY registered agent — nothing hardcoded
    for name, info in AGENTS.items():
        score = 0

        # +1 for each keyword found in the request
        for kw in info.get("keywords", []):
            if kw in text:
                score += 1

        # strong signal: agent wants a file and one was attached
        if info.get("needs_file") and has_file:
            score += 2

        # keep the highest scorer
        if score > best_score:
            best_score = score
            best_agent = name

    return best_agent