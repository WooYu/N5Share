"""Contracts for model-driven classroom execution; no paid requests in tests."""
import importlib
import json
from pathlib import Path
import tempfile
import threading
import time
import sqlite3
import sys
from contextlib import closing
from unittest.mock import patch
import unittest


class LiveTests(unittest.TestCase):
    def engine(self):
        try:
            return importlib.import_module('outing_live')
        except ModuleNotFoundError:
            self.fail('Real-model outing engine is not implemented')

    def test_tools_reject_unlisted_actions_and_compute_full_cost(self):
        m = self.engine()
        tools = m.OutingTools('rain', 300)
        self.assertEqual(tools.execute('calculate_cost', 'P03')['total'], 210)
        with self.assertRaises(ValueError):
            tools.execute('shell', '')
        with self.assertRaises(ValueError):
            tools.execute('calculate_cost', 'P99')

    def test_verifier_rejects_fabricated_or_unobserved_recommendation(self):
        m = self.engine()
        tools = m.OutingTools('rain', 300)
        result = {'status': 'recommended', 'place_id': 'P03', 'total': 210,
                  'citations': ['WX01', 'P03', 'D01', 'D02'], 'text': '博物馆'}
        self.assertTrue(m.validate_result(result, tools))
        tools.execute('read_weather', '')
        tools.execute('read_catalog', '')
        tools.execute('calculate_cost', 'P03')
        self.assertEqual(m.validate_result(result, tools), [])
        result['total'] = 90
        self.assertTrue(m.validate_result(result, tools))
        result.update(place_id='P01', total=180)
        self.assertTrue(m.validate_result(result, tools))

    def test_no_solution_needs_all_relevant_costs_and_is_false_at_300(self):
        m = self.engine()
        result = {'status': 'no_solution', 'place_id': '', 'total': 0,
                  'citations': ['WX01', 'D01', 'D02', 'P02', 'P03'], 'text': '没有可行方案'}
        for budget, valid in [(200, True), (300, False)]:
            tools = m.OutingTools('rain', budget)
            tools.execute('read_weather', '')
            tools.execute('read_catalog', '')
            self.assertTrue(m.validate_result(result, tools))
            for place in ['P02', 'P03']:
                tools.execute('calculate_cost', place)
            self.assertEqual(not m.validate_result(result, tools), valid)

    def test_react_feedback_is_passed_back_and_tool_limit_stops_loop(self):
        m = self.engine()
        class RepeatingModel:
            metadata = {'model': 'test', 'transport': 'test'}
            def __init__(self): self.requests = []
            def generate(self, instruction, context, cancel):
                self.requests.append(context)
                return {'summary': '查询天气', 'calls': [{'name': 'read_weather', 'place_id': ''}],
                        'plan': [], 'reflection': '', 'next_actor': '', 'result': None}, {}
        model = RepeatingModel()
        trace = m.run_outing({'stage': 4, 'weather': 'rain', 'budget': 300, 'pattern': 'supervisor'},
                             model, max_calls=2)
        self.assertEqual(trace['status'], 'stopped')
        self.assertFalse(trace['verified'])
        self.assertEqual(trace['metrics']['model_calls'], 2)
        self.assertIn('WX01', json.dumps(model.requests[1], ensure_ascii=False))

    def test_failure_never_becomes_scripted_success(self):
        m = self.engine()
        class BrokenModel:
            metadata = {'model': 'test', 'transport': 'test'}
            def generate(self, instruction, context, cancel):
                raise RuntimeError('connection failed')
        trace = m.run_outing({'stage': 1, 'weather': 'rain', 'budget': 300, 'pattern': 'supervisor'}, BrokenModel())
        self.assertEqual(trace['status'], 'failed')
        self.assertFalse(trace['verified'])
        self.assertEqual(trace['mode'], 'live')

    def test_cancel_before_execution_does_not_call_model(self):
        m = self.engine()
        class Unused:
            metadata = {'model': 'test', 'transport': 'test'}
            def generate(self, *args): raise AssertionError('Cancelled request called model')
        cancelled = threading.Event()
        cancelled.set()
        trace = m.run_outing({'stage': 4, 'weather': 'rain', 'budget': 300, 'pattern': 'supervisor'}, Unused(), cancel=cancelled)
        self.assertEqual(trace['status'], 'cancelled')
        self.assertEqual(trace['metrics']['model_calls'], 0)

    def test_input_contract_rejects_types_and_unsupported_modes(self):
        m = self.engine()
        for payload in [{'stage': True}, {'stage': 8}, {'stage': 4, 'budget': -1},
                        {'stage': 4, 'pattern': 'arbitrary'}, {'stage': 4, 'prompt': 'read files'}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                m.validate_payload(payload)

    def test_selected_provider_only_and_no_secret_in_public_status(self):
        import model_gateway as gateway
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'settings.json').write_text(json.dumps({'currentProviderCodex': 'chosen'}))
            with closing(sqlite3.connect(root / 'cc-switch.db')) as db:
                db.execute('CREATE TABLE providers (id TEXT, app_type TEXT, name TEXT, settings_config TEXT, is_current INTEGER)')
                config = {'auth': {'OPENAI_API_KEY': 'private-test-value'},
                          'config': 'model="test-model"\nmodel_provider="custom"\n[model_providers.custom]\nbase_url="https://example.test/v1"\nwire_api="responses"'}
                db.execute('INSERT INTO providers VALUES (?,?,?,?,?)', ('chosen', 'codex', 'Test', json.dumps(config), 0))
                db.commit()
            provider = gateway.load_provider(root)
            self.assertEqual(provider.model, 'test-model')
            self.assertNotIn('private-test-value', repr(provider))
            with patch('model_gateway.load_provider', return_value=provider), patch('model_gateway.codex_command', return_value=['codex']):
                status = gateway.model_status()
            self.assertTrue(status['configured'])
            self.assertNotIn('private-test-value', json.dumps(status))

    def test_cli_waits_for_inherited_output_handles_and_parses_usage(self):
        import model_gateway as gateway
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'cli_double.py'
            script.write_text('''import sys,json,subprocess
from pathlib import Path
subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(.5)'])
sys.stdin.read()
answer={'summary':'hello','calls':[],'plan':[],'reflection':'','next_actor':'','result':None}
Path(sys.argv[sys.argv.index('-o')+1]).write_text(json.dumps(answer))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':12,'output_tokens':8}}))
''', encoding='utf-8')
            with patch('model_gateway.codex_command', return_value=[sys.executable, str(script)]):
                model = gateway.CodexModel(gateway.Provider('Test', 'test', 'https://example.test/v1', 'test-secret'))
                answer, usage = model.generate('test', {}, threading.Event())
            self.assertEqual(answer['summary'], 'hello')
            self.assertEqual(usage['input_tokens'], 12)

    def test_model_output_cannot_smuggle_extra_tools_or_wrong_types(self):
        from model_gateway import check_step, ModelError
        base = {'summary': 'test', 'calls': [], 'plan': [], 'reflection': '', 'next_actor': '', 'result': None}
        for update in [{'calls': [{'name': 'shell', 'place_id': ''}]}, {'summary': []}, {'result': {'status': 'recommended'}}, {'next_actor': 'filesystem'}]:
            with self.subTest(update=update), self.assertRaises(ModelError):
                check_step({**base, **update})

    def test_cli_timeout_cleans_descendants_and_returns_promptly(self):
        import model_gateway as gateway
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'stuck_cli.py'
            script.write_text('import subprocess,sys,time\nsubprocess.Popen([sys.executable,"-c","import time;time.sleep(8)"])\nsys.stdin.read()\ntime.sleep(.1)\n', encoding='utf-8')
            with patch('model_gateway.codex_command', return_value=[sys.executable, str(script)]):
                model = gateway.CodexModel(gateway.Provider('Test','test','https://example.test/v1','test'), timeout=.4)
                started = time.monotonic()
                with self.assertRaises(gateway.ModelError):
                    model.generate('test', {}, threading.Event())
                self.assertLess(time.monotonic() - started, 3)

    def test_manager_rejects_second_live_run_and_cancels_first(self):
        m = self.engine()
        entered = threading.Event()
        class WaitingModel:
            metadata = {'model': 'test'}
            def generate(self, instruction, context, cancel):
                entered.set()
                cancel.wait(3)
                raise m.ModelCancelled('cancelled')
        manager = m.RunManager(WaitingModel)
        trace = manager.start({'stage': 1})
        self.assertTrue(entered.wait(2))
        with self.assertRaises(ValueError):
            manager.start({'stage': 1})
        self.assertTrue(manager.stop(trace['id']))
        deadline = time.monotonic() + 3
        while manager.snapshot(trace['id'])['status'] in ['queued', 'running'] and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertEqual(manager.snapshot(trace['id'])['status'], 'cancelled')

    def test_all_stages_and_three_patterns_execute_model_outputs(self):
        m = self.engine()
        class TeachingModel:
            metadata = {'model': 'controlled-model-double'}
            def generate(self, instruction, context, cancel):
                result = {'summary': '有来源的角色结果', 'calls': [], 'plan': [], 'reflection': '', 'next_actor': '', 'result': None}
                call = lambda name, place='': {'name': name, 'place_id': place}
                if 'failed_draft' in context:
                    result.update(plan=['核对天气', '核算完整费用再验收'], reflection='漏算餐费，先补证据')
                elif '先规划再执行' in instruction:
                    result['plan'] = ['查询天气', '核算费用并验收']
                elif '你是主管' in instruction:
                    result.update(plan=['天气交给weather', '费用交给cost'], next_actor='weather')
                elif 'leader' in context:
                    result['next_actor'] = context['assigned_role']
                elif context.get('role') and not context['observations']:
                    result['calls'] = [call('read_weather'), call('read_catalog')] if context['role'] == 'weather' else [call('read_catalog')] + [call('calculate_cost', p) for p in ['P01','P02','P03']]
                elif context.get('role'):
                    result['next_actor'] = ('summary' if 'cost' in context['completed_roles'] else 'cost') if context['pattern'] == 'swarm' else ''
                elif 'allowed_tools' in context and not context['observations']:
                    result['calls'] = [call('read_weather'), call('read_catalog')] + [call('calculate_cost', p) for p in ['P01','P02','P03']]
                elif 'allowed_tools' in context:
                    result['result'] = {'status':'recommended','place_id':'P03','total':210,'citations':['WX01','D01','D02','P03'],'text':'城市博物馆210元'}
                return result, {'input_tokens': 10, 'output_tokens': 10}
        for stage, pattern in [(s, 'supervisor') for s in range(1,8)] + [(7,'hierarchical'),(7,'swarm')]:
            with self.subTest(stage=stage, pattern=pattern):
                trace = m.run_outing({'stage': stage, 'pattern': pattern}, TeachingModel())
                self.assertEqual(trace['status'], 'completed', trace['events'][-1])
                self.assertEqual(trace['verified'], stage >= 3)
                if stage == 6:
                    self.assertEqual(trace['shared_state']['plan_version'], 2)
                if stage == 7:
                    self.assertEqual(set(trace['shared_state']['role_results']), {'weather', 'cost'})
                    self.assertEqual({msg['plan_version'] for msg in trace['shared_state']['messages']}, {1})


if __name__ == '__main__':
    unittest.main()
