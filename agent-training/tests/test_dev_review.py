"""Review contracts: real evidence, revision-bound gates, and fixed acceptance tests."""
import _bootstrap
import asyncio
import copy
from http.server import ThreadingHTTPServer
import json
import tempfile
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from demo.dev_team.contracts import validate_review, delivery_gate, ContractError
from demo.dev_team.tools import prepare_workspace, collect_context, run_tests, fingerprint


class ReviewContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        prepare_workspace(self.root, 'buggy')
        self.context = collect_context(self.root)

    def report(self):
        lines = self.context['files']['board.py'].splitlines()
        line = next(i + 1 for i, text in enumerate(lines) if 'status = status.strip()' in text)
        return {'verdict': 'request_changes', 'summary': '非法状态未校验', 'findings': [
            {'id': 'R1', 'severity': 'high', 'file': 'board.py', 'line': line,
             'end_line': line, 'title': '非法状态写入数据库', 'evidence': lines[line - 1].strip(),
             'impact': '破坏状态契约', 'suggestion': '写入前校验 STATUS',
             'test_name': 'test_invalid_status_is_rejected'}]}

    def test_evidence_must_exist_at_reported_lines(self):
        report = self.report()
        validate_review(report, self.context)
        for mutation in ({'file': '../secret.txt'}, {'line': 999}, {'evidence': 'invented()'}):
            bad = copy.deepcopy(report)
            bad['findings'][0].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ContractError):
                validate_review(bad, self.context)

    def test_incomplete_context_cannot_pass(self):
        context = collect_context(self.root, incomplete=True)
        with self.assertRaises(ContractError):
            validate_review({'verdict': 'pass', 'summary': '通过', 'findings': []}, context)

    def test_tests_detect_bug_then_accept_fixed_candidate(self):
        failed = run_tests(self.root)
        self.assertFalse(failed['passed'])
        self.assertIn('test_invalid_status_is_rejected', failed['output'])
        prepare_workspace(self.root, 'clean')
        self.assertTrue(run_tests(self.root)['passed'])

    def test_gate_requires_same_revision_tests_review_and_human(self):
        prepare_workspace(self.root, 'clean')
        revision = fingerprint(self.root)
        report = {'verdict': 'pass', 'summary': '检查通过', 'findings': [], 'revision': revision}
        tests = run_tests(self.root)
        self.assertTrue(tests['passed'], tests)
        self.assertEqual(delivery_gate(self.root, report, tests)['status'], 'waiting_approval')
        self.assertEqual(delivery_gate(self.root, report, tests, 'approve', revision)['status'], 'completed')
        self.assertEqual(delivery_gate(self.root, report, tests, 'reject', revision)['status'], 'rejected')
        with (self.root / 'candidate' / 'board.py').open('a', encoding='utf-8') as stream:
            stream.write('\n# changed after review\n')
        self.assertEqual(delivery_gate(self.root, report, tests, 'approve', revision)['status'], 'stale')

    def test_delivered_board_http_flow_persists_and_rejects_invalid_state(self):
        from product_team.delivery import proxy_handler, approve, approved_release
        from product_team.sandbox import Sandbox
        from dev_team.tools import write_json
        prepare_workspace(self.root, 'clean')
        version = fingerprint(self.root)
        write_json(self.root / 'state.json', {'status': 'waiting_approval',
            'review': {'revision': version, 'verdict': 'pass', 'findings': []}})
        approved = approve(self.root, 'approve', version)
        self.assertEqual(approved['status'], 'completed', approved)
        release, approval = approved_release(self.root)
        box = self.enterContext(Sandbox(release / 'candidate', approval['image'], legacy=True))
        server = ThreadingHTTPServer(('127.0.0.1', 0), proxy_handler(box))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def request(path, method='GET', body=None):
            data = None if body is None else json.dumps(body).encode('utf-8')
            try:
                with urlopen(Request(f'http://127.0.0.1:{server.server_port}' + path, data=data,
                                     method=method, headers={'Content-Type': 'application/json'}), timeout=5) as response:
                    return response.status, json.load(response)
            except HTTPError as error:
                return error.code, json.load(error)
        try:
            code, task = request('/api/tasks', 'POST', {'title': '验收看板'})
            self.assertEqual(code, 201)
            updated = request(f"/api/tasks/{task['id']}", 'PATCH', {'status': 'done'})
            self.assertEqual(updated, (200, {'id': task['id'], 'title': '验收看板', 'status': 'done'}))
            self.assertEqual(request('/api/tasks')[1][0]['status'], 'done')
            self.assertEqual(request(f"/api/tasks/{task['id']}", 'PATCH', {'status': 'deleted'})[0], 400)
            self.assertEqual(request('/api/tasks')[1][0]['status'], 'done')
            self.assertEqual(request('/api/tasks/999', 'PATCH', {'status': 'done'})[0], 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_late_model_result_cannot_be_accepted(self):
        from dev_team.session import Session
        with patch('dev_team.session.time.monotonic', return_value=0) as timer:
            class SlowModel:
                metadata = {'provider': 'controlled-test'}
                def generate_json(self, *args):
                    timer.return_value = 2
                    return {'summary': '迟到的通过意见'}, {}
            session = Session(self.root, max_seconds=1, model=SlowModel())
            with self.assertRaises(ValueError):
                asyncio.run(session.ask('Reviewer', 'check', {}, {}))
            self.assertFalse(any(e['kind'] == 'model_result' for e in session.state['events']))


if __name__ == '__main__':
    unittest.main()
