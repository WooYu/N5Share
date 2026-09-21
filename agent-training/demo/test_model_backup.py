"""Fallback must be explicit, bounded, and preserve model-output validation."""
import importlib
import os
from pathlib import Path
import tempfile
import threading
import unittest


class BackupTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module('model_backup')
        except ModuleNotFoundError:
            self.fail('DeepSeek backup is not implemented')

    def test_transient_primary_failure_switches_once_and_keeps_evidence(self):
        backup = self.module()
        from outing_live import run_outing
        from model_gateway import ModelUnavailable

        class Primary:
            metadata = {'provider': 'Primary', 'model': 'primary'}
            def generate(self, *args):
                raise ModelUnavailable('连接超时')

        class Secondary:
            metadata = {'provider': 'DeepSeek', 'model': 'backup'}
            def generate(self, instruction, context, cancel):
                return {'summary': '备用模型回答', 'calls': [], 'plan': [], 'reflection': '', 'next_actor': '', 'result': None}, {}

        trace = run_outing({'stage': 1}, backup.ModelRouter(Primary(), Secondary()))
        self.assertEqual(trace['status'], 'completed')
        self.assertEqual(trace['metrics']['model_calls'], 2)
        self.assertEqual(trace['model']['provider'], 'DeepSeek')
        self.assertEqual(sum(e['phase'] == '模型切换' for e in trace['events']), 1)

    def test_validation_failure_and_cancel_do_not_use_backup(self):
        backup = self.module()
        from model_gateway import ModelError, ModelCancelled
        from outing_live import run_outing

        class Secondary:
            metadata = {'model': 'backup'}
            def generate(self, *args): raise AssertionError('Unexpected backup call')

        for error, status in [(ModelError('格式错误'), 'failed'), (ModelCancelled('cancel'), 'cancelled')]:
            class Primary:
                metadata = {'model': 'primary'}
                def generate(self, *args): raise error
            trace = run_outing({'stage': 1}, backup.ModelRouter(Primary(), Secondary()))
            self.assertEqual(trace['status'], status)
            self.assertEqual(trace['metrics']['model_calls'], 1)

    def test_fallback_respects_total_model_call_limit(self):
        backup = self.module()
        from model_gateway import ModelUnavailable
        from outing_live import run_outing
        class Broken:
            metadata = {'model': 'test'}
            def generate(self, *args): raise ModelUnavailable('timeout')
        trace = run_outing({'stage': 1}, backup.ModelRouter(Broken(), Broken()), max_calls=1)
        self.assertEqual(trace['status'], 'stopped')
        self.assertEqual(trace['metrics']['model_calls'], 1)

    def test_mid_run_fallback_keeps_observations_and_stays_on_backup(self):
        backup = self.module()
        from model_gateway import ModelUnavailable
        from outing_live import run_outing
        def answer(calls=None, result=None):
            return {'summary':'summary','calls':calls or [],'plan':[],'reflection':'','next_actor':'','result':result}, {}
        class Primary:
            metadata = {'provider':'primary','model':'test'}
            calls = 0
            def generate(self, *args):
                self.calls += 1
                if self.calls == 1:
                    return answer([{'name':'read_weather','place_id':''}])
                raise ModelUnavailable('timeout')
        seen = []
        class Secondary:
            metadata = {'provider':'DeepSeek','model':'test'}
            def generate(self, instruction, context, cancel):
                seen.append(context)
                if 'CAT01' not in context['observations']:
                    return answer([{'name':'read_catalog','place_id':''},{'name':'calculate_cost','place_id':'P03'}])
                return answer(result={'status':'recommended','place_id':'P03','total':210,'citations':['WX01','D01','D02','P03'],'text':'210元'})
        primary = Primary()
        trace = run_outing({'stage':4}, backup.ModelRouter(primary,Secondary()))
        self.assertTrue(trace['verified'])
        self.assertEqual(primary.calls, 2)
        self.assertIn('WX01', seen[0]['observations'])
        self.assertEqual(trace['metrics']['model_calls'], 4)

    @unittest.skipUnless(os.name == 'nt', 'Windows DPAPI storage')
    def test_credential_is_encrypted_at_rest(self):
        self.module()
        from secret_store import save_deepseek_key, load_deepseek_key
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'key.dpapi'
            save_deepseek_key('test-private-key', path)
            self.assertNotIn(b'test-private-key', path.read_bytes())
            self.assertEqual(load_deepseek_key(path), 'test-private-key')

    def test_official_api_json_output_and_sanitized_errors(self):
        backup = self.module()
        import httpx
        from model_gateway import ModelUnavailable
        def reply(request):
            self.assertEqual(request.url.host, 'api.deepseek.com')
            return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': '{"summary":"ok","calls":[],"plan":[],"reflection":"","next_actor":"","result":null}'}}], 'usage': {'prompt_tokens': 20, 'completion_tokens': 10}})
        model = backup.DeepSeekModel('test-secret', transport=httpx.MockTransport(reply))
        answer, usage = model.generate('test', {}, threading.Event())
        self.assertEqual(answer['summary'], 'ok')
        self.assertEqual(usage['input_tokens'], 20)
        model = backup.DeepSeekModel('test-secret', transport=httpx.MockTransport(lambda r: httpx.Response(401, text='test-secret')))
        with self.assertRaises(ModelUnavailable) as error:
            model.generate('test', {}, threading.Event())
        self.assertNotIn('test-secret', str(error.exception))

    def test_course_server_rejects_duplicate_listener(self):
        import server
        cls = getattr(server, 'TrainingHTTPServer', server.ThreadingHTTPServer)
        with cls(('127.0.0.1', 0), server.Handler) as first:
            with self.assertRaises(OSError):
                duplicate = cls(('127.0.0.1', first.server_port), server.Handler)
                duplicate.server_close()


if __name__ == '__main__':
    unittest.main()
