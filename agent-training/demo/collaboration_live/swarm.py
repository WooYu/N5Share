"""Model-selected handoffs constrained by each active agent's allowed set."""
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from .state import State
from .agents import work

HANDOFFS = {
    'Researcher': ['Critic'],
    'Critic': ['Researcher', 'Analyst', 'Writer', 'END'],
    'Analyst': ['Writer'],
    'Writer': ['Critic'],
}


def build_graph(session):
    def agent_node(role):
        def node(state):
            updates = work(session, role, state, HANDOFFS[role])
            target = updates.get('next_role', state['next_role'])
            session.emit('handoff', role, target, updates.get('last_summary', '模型选择交接'))
            return Command(update=updates, goto=END if target == 'END' else target)
        return node

    graph = StateGraph(State)
    for role in HANDOFFS:
        graph.add_node(role, agent_node(role))
    graph.add_edge(START, 'Researcher')
    # No supervisor and no fixed round-robin edges.
    return graph.compile()


if __name__ == '__main__':
    from .runtime import main
    raise SystemExit(main('swarm'))
