"""A parent CEO graph invokes two actual compiled LangGraph subgraphs."""
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from .state import State
from .agents import decide, work


def build_research_team(session):
    def lead(state):
        target, reason = decide(session, 'ResearchLead', state, ['Researcher', 'END'])
        session.emit('dispatch' if target != 'END' else 'report', 'ResearchLead', target, reason)
        return Command(goto=END if target == 'END' else target)

    graph = StateGraph(State)
    graph.add_node('ResearchLead', lead)
    graph.add_node('Researcher', lambda state: work(session, 'Researcher', state))
    graph.add_edge(START, 'ResearchLead')
    graph.add_edge('Researcher', 'ResearchLead')
    return graph.compile()


def build_delivery_team(session):
    def lead(state):
        target, reason = decide(session, 'DeliveryLead', state, ['Analyst', 'Writer', 'Critic', 'ESCALATE', 'END'])
        if target == 'ESCALATE':
            session.emit('escalate', 'DeliveryLead', 'CEO', reason)
            return Command(update={'needs_research': True}, goto=END)
        session.emit('dispatch' if target != 'END' else 'report', 'DeliveryLead', target, reason)
        return Command(goto=END if target == 'END' else target)

    graph = StateGraph(State)
    graph.add_node('DeliveryLead', lead)
    for role in ('Analyst', 'Writer', 'Critic'):
        graph.add_node(role, lambda state, role=role: work(session, role, state))
        graph.add_edge(role, 'DeliveryLead')
    graph.add_edge(START, 'DeliveryLead')
    return graph.compile()


def build_graph(session):
    def ceo(state):
        target, reason = decide(session, 'CEO', state, ['research_team', 'delivery_team', 'END'])
        session.emit('dispatch', 'CEO', target, reason)
        updates = {'research_done': False} if target == 'research_team' else {}
        return Command(update=updates, goto=END if target == 'END' else target)

    graph = StateGraph(State)
    graph.add_node('CEO', ceo)
    graph.add_node('research_team', build_research_team(session))
    graph.add_node('delivery_team', build_delivery_team(session))
    graph.add_edge(START, 'CEO')
    graph.add_edge('research_team', 'CEO')
    graph.add_edge('delivery_team', 'CEO')
    return graph.compile()


if __name__ == '__main__':
    from .runtime import main
    raise SystemExit(main('hierarchical'))
