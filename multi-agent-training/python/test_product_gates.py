"""Real LangGraph routing and tool regressions, without paid model calls."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import labs
import common


class Router:
    def with_structured_output(self, schema, **kwargs):
        return SimpleNamespace(invoke=lambda _: SimpleNamespace(verdict='pass', summary='controlled review')
                               if schema.__name__ == 'Review' else SimpleNamespace(next_agent='END'))


class NetworkGateTests(unittest.TestCase):
    def test_end_without_execution_is_refused_and_budget_stops(self):
        visited = []
        def worker(model, name, tools, prompt):
            def invoke(state, **kwargs):
                visited.append(name)
                return {'messages': [AIMessage(content='claim only', id=name + str(len(visited)))]}
            return SimpleNamespace(invoke=invoke)
        with tempfile.TemporaryDirectory() as directory, patch.object(labs, 'OUTPUT', Path(directory)), patch.object(labs, 'worker', worker):
            graph = labs.build_network(Router(), 3)
            with self.assertRaisesRegex(RuntimeError, 'budget'):
                graph.invoke({'messages': [HumanMessage(content='write a report')], 'steps': 0})
        self.assertEqual(visited[0], 'planner')
        self.assertIn('executor', visited)

    def test_end_requires_saved_artifact_and_structured_review(self):
        visited = []
        with tempfile.TemporaryDirectory() as directory, patch.object(labs, 'OUTPUT', Path(directory)):
            def worker(model, name, tools, prompt):
                def invoke(state, **kwargs):
                    visited.append(name)
                    if name == 'executor':
                        path = Path(directory) / 'agent_report.md'
                        path.write_text('A real proposal with sources and acceptance.', encoding='utf-8')
                        return {'messages': [ToolMessage(content=str(path), name='write_tool', tool_call_id='write-1', id='actual-write')]}
                    return {'messages': [AIMessage(content='controlled worker', id=name)]}
                return SimpleNamespace(invoke=invoke)
            with patch.object(labs, 'worker', worker):
                result = labs.build_network(Router(), 4).invoke({'messages': [HumanMessage(content='write a report')], 'steps': 0})
        self.assertEqual(visited, ['planner', 'executor', 'reviewer'])
        self.assertTrue(result['artifact_sha256'])
        self.assertEqual(result['reviewed_sha256'], result['artifact_sha256'])

    def test_fixed_code_and_syntax_only_tools_are_no_longer_available(self):
        with patch.dict('os.environ', {'TRAINING_PRODUCT_RUN_DIR': ''}):
            with self.assertRaisesRegex(ValueError, 'host'):
                common.code_tool.invoke({'spec': 'inventory'})
            with self.assertRaisesRegex(ValueError, 'host'):
                common.test_tool.invoke({})


if __name__ == '__main__':
    unittest.main()
