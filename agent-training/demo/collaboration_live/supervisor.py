"""The model supervisor selects the next role after each worker returns."""
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from .state import State
from .agents import ROLES, decide, work


def build_graph(session):
    def supervisor(state):
        target, reason = decide(session, 'Supervisor', state, [*ROLES, 'END'])
        session.emit('dispatch', 'Supervisor', target, reason, state=state)
        return Command(goto=END if target == 'END' else target)

    def worker_node(role):
        def node(state):
            updates = work(session, role, state)
            session.emit('report', role, 'Supervisor', '成员返回主管，由主管重新决定下一步')
            return updates
        return node

    graph = StateGraph(State)
    graph.add_node('Supervisor', supervisor)
    for role in ROLES:
        graph.add_node(role, worker_node(role))
        graph.add_edge(role, 'Supervisor')
    graph.add_edge(START, 'Supervisor')
    return graph.compile()


if __name__ == '__main__':
    from .runtime import main
    raise SystemExit(main('supervisor'))
