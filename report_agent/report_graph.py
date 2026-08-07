"""LangGraph agent that builds the centralized organization report."""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from report_agent.report_data import fetch_report_data
from report_agent.llm_report import generate_report_narrative
from report_agent.pdf_builder import build_report_pdf


# shared state passed between nodes
class ReportState(TypedDict):
    report_data: dict
    narrative: str
    pdf_bytes: Optional[bytes]
    status: str


# 1. pull all org data from the related tables
def node_fetch(state):
    state["report_data"] = fetch_report_data()
    return state


# 2. LLM writes the narrative from the data
def node_narrative(state):
    try:
        state["narrative"] = generate_report_narrative(state["report_data"])
    except Exception as error:
        print("Narrative generation failed:", error)
        state["narrative"] = (
            "Executive Summary:\n"
            "This report summarizes the current workforce and project portfolio.\n"
        )
    return state


# 3. build the PDF bytes
def node_pdf(state):
    state["pdf_bytes"] = build_report_pdf(state["report_data"], state["narrative"])
    state["status"] = "done"
    return state


def build_graph():
    g = StateGraph(ReportState)

    # NOTE: node names MUST differ from state keys
    # (state keys are: report_data, narrative, pdf_bytes, status)
    g.add_node("fetch_node", node_fetch)
    g.add_node("narrative_node", node_narrative)
    g.add_node("pdf_node", node_pdf)

    g.set_entry_point("fetch_node")
    g.add_edge("fetch_node", "narrative_node")
    g.add_edge("narrative_node", "pdf_node")
    g.add_edge("pdf_node", END)
    return g.compile()


report_agent = build_graph()


def run_report_agent() -> bytes:
    """Convenience runner — returns the PDF bytes."""
    state = {"report_data": {}, "narrative": "", "pdf_bytes": None, "status": "started"}
    result = report_agent.invoke(state)
    return result["pdf_bytes"]