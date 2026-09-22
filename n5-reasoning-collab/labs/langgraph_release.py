"""Run: python labs/langgraph_release.py [blocked|missing|ready]. No LLM calls."""
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from common import collect_reports, evaluate, sample, show


class ReleaseState(TypedDict, total=False):
    source: dict
    reports: list[dict]
    result: dict


def collect_findings(state: ReleaseState):
    return {"reports": collect_reports(state["source"])}


def release_route(state: ReleaseState):
    return evaluate(state["reports"], state["source"])["decision"]


def mark_block(state: ReleaseState):
    return {"result": evaluate(state["reports"], state["source"])}


def mark_allow(state: ReleaseState):
    return {"result": evaluate(state["reports"], state["source"])}


def mark_missing(state: ReleaseState):
    return {"result": evaluate(state["reports"], state["source"])}


def build_graph():
    graph = StateGraph(ReleaseState)
    graph.add_node("collect", collect_findings)
    graph.add_node("block", mark_block)
    graph.add_node("allow", mark_allow)
    graph.add_node("missing", mark_missing)
    graph.add_edge(START, "collect")
    graph.add_conditional_edges("collect", release_route, {
        "BLOCK": "block", "READY_FOR_MANUAL_REVIEW": "allow", "NEEDS_EVIDENCE": "missing"})
    for target in ("block", "allow", "missing"):
        graph.add_edge(target, END)
    return graph.compile()


if __name__ == "__main__":
    source = sample(sys.argv[1] if len(sys.argv) > 1 else "blocked")
    for update in build_graph().stream({"source": source}, stream_mode="updates"):
        show(update)
