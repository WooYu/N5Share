"""Each peer executes its role and chooses the next peer inside its node."""
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from .state import State
from .agents import ROLES, work


def build_graph(session):
    def peer_node(role):
        def node(state):
            # Full connection is this example's choice, not a Network requirement.
            allowed = [peer for peer in ROLES if peer != role] + ['END']
            updates = work(session, role, state, allowed)
            target = updates.get('next_role', state['next_role'])
            session.emit('route', role, target, updates.get('last_summary', '模型选择下一跳'))
            return Command(update=updates, goto=END if target == 'END' else target)
        return node

    graph = StateGraph(State)
    for role in ROLES:
        graph.add_node(role, peer_node(role))
    graph.add_edge(START, 'Writer')
    # Decisions belong to the active node; there is no central Router node.
    return graph.compile()


if __name__ == '__main__':
    from .runtime import main
    raise SystemExit(main('network'))
