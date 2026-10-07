"""Fixed graph edges. Each node is a real model-backed role with tools."""
from langgraph.graph import StateGraph, START, END
from .state import State
from .agents import work


def build_graph(session):
    graph = StateGraph(State)
    graph.add_node('Researcher', lambda state: work(session, 'Researcher', state))
    graph.add_node('Analyst', lambda state: work(session, 'Analyst', state))
    graph.add_node('Writer', lambda state: work(session, 'Writer', state))
    graph.add_node('Critic', lambda state: work(session, 'Critic', state))

    graph.add_edge(START, 'Researcher')
    graph.add_edge('Researcher', 'Analyst')
    graph.add_edge('Analyst', 'Writer')
    graph.add_edge('Writer', 'Critic')
    graph.add_edge('Critic', END)
    # Deliberately no back edge: missing data finishes as needs_input.
    return graph.compile()


if __name__ == '__main__':
    from .runtime import main
    raise SystemExit(main('sequential'))
