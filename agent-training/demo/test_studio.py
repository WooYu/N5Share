"""Studio graphs expose real node boundaries and resumable local state."""
import importlib
import unittest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class ClassroomModel:
    metadata = {'provider': 'Test', 'model': 'controlled-model'}

    def generate(self, instruction, context, cancel):
        answer = {'summary': '基于证据的结果', 'calls': [], 'plan': [], 'reflection': '', 'next_actor': '', 'result': None}
        call = lambda name, place='': {'name': name, 'place_id': place}
        if '你是主管' in instruction:
            answer.update(plan=['天气角色收集天气', '费用角色核算成本', '汇总验收'], next_actor='weather')
        elif context.get('role') and not context['observations']:
            answer['calls'] = [call('read_weather'), call('read_catalog')] if context['role'] == 'weather' else [call('read_catalog')] + [call('calculate_cost', p) for p in ['P01', 'P02', 'P03']]
        elif context.get('role'):
            pass
        elif not context.get('observations'):
            answer['calls'] = [call('read_weather'), call('read_catalog'), call('calculate_cost', 'P03')]
        else:
            answer['result'] = {'status': 'recommended', 'place_id': 'P03', 'total': 210,
                                'citations': ['WX01', 'D01', 'D02', 'P03'], 'text': '城市博物馆210元'}
        return answer, {'input_tokens': 10, 'output_tokens': 10}


class StudioTests(unittest.IsolatedAsyncioTestCase):
    def graph(self, kind, **kwargs):
        try:
            module = importlib.import_module('studio_graphs')
        except ModuleNotFoundError:
            self.fail('Studio graphs are not implemented')
        return module.build_graph(kind, model_factory=ClassroomModel, **kwargs)

    async def test_react_has_separate_decision_tool_and_validation_steps(self):
        graph = self.graph('react')
        visited = []
        async for chunk in graph.astream({'weather': 'rain', 'budget': 300}, stream_mode='updates'):
            visited.extend(chunk)
            result = next(iter(chunk.values()))
        self.assertIn('call_tools', visited)
        self.assertEqual(visited.count('decide'), 2)
        self.assertIn('verify', visited)
        self.assertTrue(result['trace']['verified'])
        self.assertEqual(result['trace']['result']['total'], 210)

    async def test_supervisor_can_pause_before_summary_and_resume_without_repeating_roles(self):
        graph = self.graph('supervisor', checkpointer=InMemorySaver())
        config = {'configurable': {'thread_id': 'classroom-test'}}
        paused = await graph.ainvoke({'weather': 'rain', 'budget': 300, 'pause_before_summary': True}, config)
        self.assertTrue(paused.get('__interrupt__'))
        self.assertEqual(paused['trace']['metrics']['model_calls'], 5)
        final = await graph.ainvoke(Command(resume=True), config)
        self.assertTrue(final['trace']['verified'])
        self.assertEqual(final['trace']['metrics']['model_calls'], 6)
        self.assertEqual(len(final['trace']['shared_state']['messages']), 2)

    async def test_resume_can_stop_without_requesting_summary(self):
        graph = self.graph('supervisor', checkpointer=InMemorySaver())
        config = {'configurable': {'thread_id': 'stop-test'}}
        await graph.ainvoke({'pause_before_summary': True}, config)
        final = await graph.ainvoke(Command(resume=False), config)
        self.assertEqual(final['trace']['status'], 'cancelled')
        self.assertEqual(final['trace']['metrics']['model_calls'], 5)

    async def test_model_call_budget_is_preserved_across_graph_nodes(self):
        graph = self.graph('react')
        result = await graph.ainvoke({'max_model_calls': 1})
        self.assertEqual(result['trace']['status'], 'stopped')
        self.assertFalse(result['trace']['verified'])
        self.assertEqual(result['trace']['metrics']['model_calls'], 1)


if __name__ == '__main__':
    unittest.main()
