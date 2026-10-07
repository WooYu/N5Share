"""JSON state shared by parent graphs and callable team subgraphs."""
from typing import TypedDict


class State(TypedDict, total=False):
    weather: str
    budget: int
    evidence: dict
    research_rounds: int
    research_done: bool
    needs_research: bool
    analysis: list
    analyzed: bool
    proposal: dict | None
    approved: bool
    issues: list[str]
    last_actor: str
    last_summary: str
    next_role: str


def initial_state(weather='rain', budget=300):
    return State(weather=weather, budget=budget, evidence={}, research_rounds=0,
                 research_done=False, needs_research=False, analysis=[],
                 analyzed=False, proposal=None, approved=False, issues=[],
                 last_actor='', last_summary='', next_role='')
