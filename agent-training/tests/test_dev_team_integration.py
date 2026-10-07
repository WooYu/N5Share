"""Exercise actual MetaGPT subscriptions and repair gates with controlled model responses."""
import _bootstrap
import asyncio
import contextlib
import importlib.util
import io
import tempfile
from pathlib import Path
import unittest


class ControlledModel:
    metadata = {'provider': 'test-double', 'model': 'controlled-contract', 'using_backup': False}
    timeout = 30

    def generate_json(self, instruction, context, cancel, schema):
        from dev_team.tools import FIXTURES
        fields = set(schema['properties'])
        if fields == {'document'}:
            answer = {'document': '固定需求与设计：任务看板使用SQLite保存，独立评审和固定测试验证状态契约，交付前由人工批准。'}
        elif fields == {'tools', 'summary'}:
            answer = {'tools': ['read_diff', 'read_context', 'run_fixed_tests'], 'summary': '请求固定检查'}
        elif fields == {'source', 'summary'}:
            answer = {'source': (FIXTURES / 'board.py').read_text(encoding='utf-8'), 'summary': '恢复非法状态校验'}
        else:
            observed = context['observations']
            if not observed['read_context']['complete']:
                answer = {'verdict': 'needs_context', 'summary': '缺少需求契约', 'findings': []}
            elif observed['run_fixed_tests']['passed']:
                answer = {'verdict': 'pass', 'summary': '本轮没有阻断问题，固定验收通过', 'findings': []}
            else:
                lines = observed['read_context']['numbered_files']['board.py'].splitlines()
                code_line = next(text for text in lines if 'status = status.strip()' in text)
                number, code = code_line.split(': ', 1)
                answer = {'verdict': 'request_changes', 'summary': '移除非法状态校验导致契约失败', 'findings': [
                    {'id': 'R1', 'severity': 'high', 'file': 'board.py', 'line': int(number), 'end_line': int(number),
                     'title': '非法状态会写入SQLite', 'evidence': code.strip(), 'impact': '允许deleted等非法状态',
                     'suggestion': '写入前检查STATUSES', 'test_name': 'test_invalid_status_is_rejected'}]}
        return answer, {'input_tokens': 1, 'output_tokens': 1}


@unittest.skipUnless(importlib.util.find_spec('metagpt'), 'requires the dedicated MetaGPT environment')
class MetaGPTIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dev_team.bootstrap import prepare_runtime
        prepare_runtime(Path(__file__).resolve().parents[1] / 'test-results' / 'metagpt-integration')

    def execute(self, scenario='buggy', max_repairs=2, max_calls=12, model=None):
        from dev_team.session import Session
        from dev_team.team import run_team
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        session = Session(Path(self.tmp.name), scenario=scenario, max_repairs=max_repairs,
                          max_calls=max_calls, model=model or ControlledModel())
        with contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(run_team(session))
        return session

    def test_real_messages_trigger_review_repair_and_fresh_review(self):
        session = self.execute()
        self.assertEqual(session.state['status'], 'waiting_approval')
        self.assertEqual(session.state['repair_round'], 1)
        reviews = [e['report'] for e in session.state['events'] if e['kind'] == 'review']
        self.assertEqual([r['verdict'] for r in reviews], ['request_changes', 'pass'])
        self.assertNotEqual(reviews[0]['revision'], reviews[1]['revision'])
        actors = [e['actor'] for e in session.state['events'] if e['kind'] == 'action']
        self.assertEqual(actors, ['PM', 'Architect', 'Developer', 'Reviewer', 'Tester', 'RepairDeveloper', 'Reviewer', 'Tester'])

    def test_clean_incomplete_and_exhausted_exits(self):
        for scenario, limit, expected in [('clean', 2, 'waiting_approval'), ('incomplete', 2, 'needs_context'),
                                           ('buggy', 0, 'needs_human')]:
            with self.subTest(scenario=scenario):
                session = self.execute(scenario, limit)
                self.assertEqual(session.state['status'], expected)
                self.assertEqual(session.state['repair_round'], 0)

    def test_invalid_repair_syntax_gets_one_contract_retry(self):
        class InitiallyInvalidModel(ControlledModel):
            attempts = 0
            def generate_json(self, instruction, context, cancel, schema):
                if set(schema['properties']) == {'source', 'summary'}:
                    self.attempts += 1
                    if self.attempts == 1:
                        return {'source': 'def broken(\n' + '# invalid repair\n' * 20, 'summary': '无效源码'}, {}
                return super().generate_json(instruction, context, cancel, schema)
        model = InitiallyInvalidModel()
        session = self.execute(model=model)
        self.assertEqual(session.state['status'], 'waiting_approval')
        self.assertEqual(model.attempts, 2)
        self.assertTrue(any(e['kind'] == 'invalid_output' for e in session.state['events']))


if __name__ == '__main__':
    unittest.main()
