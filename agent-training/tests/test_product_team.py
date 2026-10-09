"""Regression probes for the production-readiness audit; actual Docker where noted."""
import _bootstrap
import asyncio
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dev_team.tools import prepare_workspace, fingerprint, run_tests, write_json, FIXTURES
from product_team.acceptance import board_cases, execute_cases, assert_response
from product_team.delivery import approved_release, approve, evidence_digest, run_lock
from product_team.gates import delivery_gate
from product_team.sandbox import Sandbox, SandboxError, resolve_image
from product_team.spec import load_spec, validate_spec
from product_team.workspace import read_sources, snapshot, safe_name, validate_bundle, write_bundle


class ProductPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        prepare_workspace(self.root, 'clean')
        self.version = fingerprint(self.root)
        self.review = {'revision': self.version, 'verdict': 'pass', 'findings': []}
        self.tests = {'revision': self.version, 'passed': True, 'tool': 'external_http_acceptance',
                      'executed': 6, 'cases': [{'id': c['id'], 'passed': True} for c in board_cases()],
                      'image': 'sha256:' + 'a' * 64}

    def seed_approval(self):
        _, release = snapshot(self.root)
        state = {'status': 'completed', 'review': self.review, 'tests': self.tests, 'release': self.version}
        approval = {'decision': 'approve', 'revision': self.version, 'actor': 'controlled-test',
                    'expires': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                    'image': self.tests['image'], 'evidence_sha256': evidence_digest(state)}
        state['human_decision'] = approval
        write_json(self.root / 'state.json', state)
        write_json(self.root / 'approval.json', approval)
        write_json(release / 'approval.json', approval)
        return state, approval, release

    def test_zero_tests_stdout_and_missing_cases_cannot_pass(self):
        for change in ({'executed': 0, 'cases': [], 'output': 'Ran 5 tests\nOK'},
                       {'cases': self.tests['cases'][:-1], 'executed': 5},
                       {'tool': 'fixed_unittest'}, {'image': ''}):
            with self.subTest(change=change):
                result = delivery_gate(self.root, self.review, {**self.tests, **change}, 'approve', self.version)
                self.assertEqual(result['status'], 'needs_fix')

    def test_blocking_review_or_business_failure_never_completes(self):
        self.review['findings'] = [{'severity': 'high'}]
        self.assertEqual(delivery_gate(self.root, self.review, self.tests)['status'], 'needs_fix')
        self.review['findings'] = []
        self.tests['cases'][0]['passed'] = False
        self.assertEqual(delivery_gate(self.root, self.review, self.tests)['status'], 'needs_fix')

    def test_unapproved_and_modified_versions_refuse_start_before_container(self):
        with self.assertRaises(OSError):
            approved_release(self.root)
        state, approval, release = self.seed_approval()
        self.assertEqual(approved_release(self.root)[0], release)
        (self.root / 'candidate' / 'board.py').write_text('raise SystemExit(0)', encoding='utf-8')
        with self.assertRaises(ValueError):
            approved_release(self.root)

    def test_expired_rejected_evidence_and_release_tampering_refuse_start(self):
        for mutation in ('expired', 'rejected', 'evidence', 'snapshot'):
            with self.subTest(mutation=mutation):
                state, approval, release = self.seed_approval()
                if mutation == 'expired':
                    approval['expires'] = '2000-01-01T00:00:00+00:00'
                    state['human_decision'] = approval
                    write_json(self.root / 'approval.json', approval)
                elif mutation == 'rejected':
                    state['status'] = 'rejected'
                elif mutation == 'evidence':
                    state['tests'] = {**state['tests'], 'output': 'tampered'}
                else:
                    (release / 'candidate' / 'board.py').write_text('# tampered', encoding='utf-8')
                write_json(self.root / 'state.json', state)
                with self.assertRaises(ValueError):
                    approved_release(self.root)

    def test_docker_unavailable_fails_closed(self):
        with patch('product_team.acceptance.resolve_image', side_effect=SandboxError('unavailable')):
            result = run_tests(self.root)
        self.assertFalse(result['passed'])
        self.assertEqual(result['executed'], 0)

    def test_write_paths_are_bounded(self):
        for name in ('../app.py', '/app.py', 'C:/x.py', 'a/../../x.py', 'NUL.py', 'a\\b.py', '.env'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_name(name)

    def test_requirements_block_unresolved_and_zero_business_or_browser_tests(self):
        spec = load_spec(Path(__file__).parents[1] / 'demo/product_team/examples/inventory.json')
        for change in ({'unresolved': ['谁可以扣减库存']}, {'acceptance': []}, {'browser': []}, {'legacy': True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_spec({**spec, **change})

    def test_null_return_and_wrong_json_types_fail(self):
        for raw in (b'null', b'{"id":true,"title":"x","status":"done"}'):
            with self.subTest(raw=raw), self.assertRaises((AssertionError, TypeError)):
                assert_response({'status': 200, 'raw': raw}, {'status': 200, 'types': {'id': 'integer'}})

    def test_no_candidate_imports_for_multifile_write(self):
        files = {'app.py': 'raise RuntimeError("must never import")', 'domain.py': 'x=1',
                 'index.html': '<html></html>', 'README.md': 'run with Docker', 'requirements.lock': '# stdlib'}
        write_bundle(self.root, {'summary': 'controlled bundle', 'files': [{'path': k, 'content': v} for k,v in files.items()]})
        self.assertEqual(read_sources(self.root / 'candidate'), files)
        self.assertFalse((self.root / 'candidate' / 'board.py').exists())

    def test_nested_frontend_is_allowed_and_failed_replace_preserves_old_source(self):
        files = {'app.py': 'import domain', 'domain.py': 'x=1', 'static/index.html': '<html></html>',
                 'README.md': 'run with Docker', 'requirements.lock': '# stdlib'}
        bundle = {'summary': 'controlled nested frontend', 'files': [{'path': k, 'content': v} for k,v in files.items()]}
        validate_bundle(bundle)
        original = read_sources(self.root / 'candidate')
        rename = Path.rename
        def fail_stage(path, target):
            if path.name == 'candidate' and path.parent.name.startswith('source-stage-'):
                raise OSError('simulated replace error')
            return rename(path, target)
        with patch.object(Path, 'rename', fail_stage), self.assertRaises(OSError):
            write_bundle(self.root, bundle)
        self.assertEqual(read_sources(self.root / 'candidate'), original)

    def test_concurrent_process_lock_and_release(self):
        with run_lock(self.root):
            with self.assertRaises(ValueError):
                with run_lock(self.root):
                    self.fail('second writer acquired lock')
        with run_lock(self.root):
            pass


class DockerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = resolve_image()  # This suite requires Docker, never silently falls back.

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        prepare_workspace(self.root, 'clean')

    def test_import_stdout_forgery_executes_zero_acceptance_and_fails(self):
        (self.root / 'candidate' / 'board.py').write_text('print("Ran 5 tests\\nOK")\nraise SystemExit(0)\n', encoding='utf-8')
        result = run_tests(self.root)
        self.assertFalse(result['passed'])
        self.assertEqual(result['executed'], 0)

    def test_update_status_null_return_fails_business_contract(self):
        path = self.root / 'candidate' / 'board.py'
        source = path.read_text(encoding='utf-8')
        position = source.index('    def update_status(')
        tail = source[position:]
        lines = tail.splitlines()
        line = next(line for line in lines if line.strip().startswith('return '))
        path.write_text(source[:position] + tail.replace(line, '        return None', 1), encoding='utf-8')
        result = run_tests(self.root)
        self.assertFalse(result['passed'])
        self.assertTrue(any(c['id'] == 'test_valid_status_survives_reopen' and not c['passed'] for c in result['cases']))

    def test_container_cannot_read_host_env_write_readonly_or_connect_out(self):
        source = '''import os,json,socket
from http.server import BaseHTTPRequestHandler,HTTPServer
checks={'host_env_absent': 'PRODUCT_AUDIT_SENTINEL' not in os.environ}
for path in ['/app/escape.txt','/runtime/escape.txt','/escape.txt']:
    try:
        open(path,'w').write('probe')
        checks[path]=False
    except OSError:
        checks[path]=True
try:
    socket.create_connection(('1.1.1.1',80),timeout=1).close()
    checks['network_blocked']=False
except OSError:
    checks['network_blocked']=True
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200);self.end_headers();self.wfile.write(json.dumps(checks).encode())
HTTPServer(('127.0.0.1',8080),Handler).serve_forever()
'''
        (self.root / 'candidate' / 'app.py').write_text(source, encoding='utf-8')
        with patch.dict(os.environ, {'PRODUCT_AUDIT_SENTINEL': 'harmless-test-only'}):
            with Sandbox(self.root / 'candidate', self.image) as box:
                result = json.loads(box.request('/')['raw'])
                self.assertTrue(all(result.values()), result)


if __name__ == '__main__':
    unittest.main()
