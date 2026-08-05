"""Orchestrator: decide which agent handles the request, run it, tag the result."""

from orchestrator.registry import AGENTS
from orchestrator.router import choose_agent


def run(state: dict, user_input: str = "", has_file: bool = False) -> dict:
    # 1. decide which agent should handle this
    agent_name = choose_agent(user_input, has_file)

    # 2. fetch that agent from the registry
    agent = AGENTS[agent_name]["agent"]

    # 3. run it and record who handled it
    result = agent.invoke(state)
    result["handled_by"] = agent_name
    return result