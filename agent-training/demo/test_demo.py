"""Behavioral contracts for the synthetic remote-diagnosis classroom lab."""
import copy
import http.client
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import agents
import server

PATTERNS = ('workflow', 'supervisor', 'parallel', 'review', 'integrated')
SCENARIOS = ('normal', 'missing', 'conflict', 'tool_failure', 'budget')


class DemoTests(unittest.TestCase):
    def test_schema_v2_backend_exists(self):
        self.assertTrue(hasattr(agents, 'PATTERNS'), 'Remote diagnosis graph API is missing')

    def test_every_pattern_and_scenario(self):
        for pattern in PATTERNS:
            for scenario in SCENARIOS:
                with self.subTest(pattern=pattern, scenario=scenario):
                    trace = agents.run(pattern=pattern, scenario=scenario)
                    self.assertEqual(trace['schema_version'], 2)
                    self.assertEqual(trace['engine'], 'langgraph')
                    self.assertEqual(trace['mode'], 'simulation')
                    self.assertEqual((trace['pattern'], trace['scenario']), (pattern, scenario))
                    self.assertEqual(trace['human_review']['status'], 'pending')
                    self.assertFalse(trace['shared_state']['vehicle_actions_allowed'])
                    self.assertGreaterEqual(trace['metrics']['elapsed_ms'], 0)
                    actions = [event for event in trace['events'] if event['kind'] == 'Action']
                    self.assertEqual(trace['metrics']['tool_calls'], len(actions))
                    self.assertEqual(len({event['id'] for event in trace['events']}), len(trace['events']))
                    for event in trace['events']:
                        self.assertIn(event['actor'], ('workflow', 'coordinator', 'evidence', 'knowledge', 'reviewer'))
                        self.assertTrue({'id', 'actor', 'kind', 'payload', 'plan_version'} <= event.keys())
                    expected = {'tool_failure': 'needs_human', 'budget': 'stopped'}.get(scenario, 'completed')
                    self.assertEqual(trace['status'], expected)
                    self.assertEqual(trace['verified'], expected == 'completed')
                    if expected == 'completed':
                        self.assertEqual(trace['metrics']['evidence_coverage'], 1.0)
                        self.assertIn('11.7', trace['report'])
                        self.assertIn('U0121', trace['report'])
                        self.assertIn('人工', trace['report'])
                        self.assertTrue(agents.verify(trace['shared_state'], trace['shared_state']['draft']))
                    else:
                        self.assertEqual(trace['report'], '')
                    json.dumps(trace, allow_nan=False)

    def test_supplemental_read_recovers_missing_information(self):
        trace = agents.run(scenario='missing')
        tools = [event['payload']['tool'] for event in trace['events'] if event['kind'] == 'Action']
        self.assertEqual(tools.count('read_supplemental'), 1)
        self.assertEqual(trace['metrics']['tool_calls'], 3)
        self.assertEqual(trace['metrics']['revision_rounds'], 1)
        self.assertIn('E-VOLTAGE', trace['report'])

    def test_conflicting_values_are_reconciled_and_reviewed(self):
        trace = agents.run(scenario='conflict')
        resolution = trace['shared_state']['draft']['reconciliations'][0]
        self.assertEqual(resolution['selected_ref'], 'E-VOLTAGE')
        self.assertEqual(resolution['rejected_refs'], ['E-VOLTAGE-OLD'])
        self.assertEqual(resolution['context_ref'], 'E-INCIDENT')
        self.assertIn('12.6', trace['report'])
        self.assertTrue(any(event['actor'] == 'reviewer' and event['kind'] == 'Review' for event in trace['events']))

    def test_persistent_tool_failure_never_publishes_success(self):
        trace = agents.run(scenario='tool_failure')
        failures = [event for event in trace['events'] if event['kind'] == 'Observation' and not event['payload']['ok']]
        self.assertEqual(len(failures), 2)
        self.assertEqual(trace['metrics']['tool_calls'], 3)
        self.assertFalse(trace['verified'])
        self.assertFalse(any(event['kind'] == 'Finish' for event in trace['events']))

    def test_review_pattern_routes_rejection_through_revision(self):
        trace = agents.run(pattern='review', scenario='missing')
        reviews = [event['payload']['accepted'] for event in trace['events'] if event['kind'] == 'Review']
        self.assertEqual(reviews, [False, True])
        self.assertEqual(trace['metrics']['revision_rounds'], 1)

    def test_missing_review_names_the_missing_voltage_evidence(self):
        trace = agents.run(pattern='review', scenario='missing')
        reviews = [event['payload'] for event in trace['events'] if event['kind'] == 'Review']
        self.assertFalse(reviews[0]['accepted'])
        self.assertIn('缺少电压证据', '\n'.join(reviews[0]['errors']))
        self.assertTrue(reviews[1]['accepted'])
        self.assertEqual(reviews[1]['errors'], [])

    def test_validator_identifies_each_missing_or_duplicate_field(self):
        state = agents.run()['shared_state']
        for field, label in (('voltage', '电压'), ('dtc', '故障码'), ('gateway', '网关连通')):
            with self.subTest(field=field):
                draft = copy.deepcopy(state['draft'])
                draft['claims'] = [claim for claim in draft['claims'] if claim['field'] != field]
                errors = agents.validate_report(state, draft)
                self.assertEqual(len(errors), 1)
                self.assertIn('缺少' + label + '证据', errors[0])
                draft = copy.deepcopy(state['draft'])
                draft['claims'].append(copy.deepcopy(next(claim for claim in draft['claims'] if claim['field'] == field)))
                self.assertIn(label + '证据重复', '\n'.join(agents.validate_report(state, draft)))

    def test_validator_distinguishes_unknown_and_malformed_claims(self):
        state = agents.run()['shared_state']
        cases = (
            ([{'field': 'temperature', 'value': 20, 'unit': 'C', 'refs': []}], '未知证据字段：temperature'),
            ([None], '证据条目格式无效'),
            ({}, '证据列表格式无效'),
        )
        for claims, expected in cases:
            with self.subTest(claims=claims):
                draft = copy.deepcopy(state['draft'])
                draft['claims'] = claims
                self.assertIn(expected, '\n'.join(agents.validate_report(state, draft)))

    def test_workflow_uses_fixed_steps_and_conditional_supplement_without_delegation(self):
        with patch.multiple(agents.GraphRun,
                            coordinator=unittest.mock.DEFAULT, dispatch=unittest.mock.DEFAULT,
                            assess=unittest.mock.DEFAULT, revise=unittest.mock.DEFAULT,
                            draft=unittest.mock.DEFAULT, reviewer=unittest.mock.DEFAULT) as agent_methods:
            for method in agent_methods.values():
                method.side_effect = AssertionError('Fixed workflow delegated to an Agent role')
            for scenario in ('normal', 'missing', 'conflict', 'tool_failure'):
                with self.subTest(scenario=scenario):
                    trace = agents.run(pattern='workflow', scenario=scenario)
                    self.assertEqual(trace['status'], 'needs_human' if scenario == 'tool_failure' else 'completed')
                    self.assertEqual({event['actor'] for event in trace['events']}, {'workflow'})
                    self.assertFalse(any(event['kind'] in ('Dispatch', 'Revision') for event in trace['events']))
                    self.assertEqual(trace['metrics']['revision_rounds'], 0)
                    self.assertEqual(trace['shared_state']['plan_version'], 1)
                    self.assertEqual(trace['shared_state']['decision_source'], 'fixed_program')
                    plans = [event for event in trace['events'] if event['kind'] == 'Plan']
                    self.assertEqual(len(plans), 1)
                    actions = [event['payload']['tool'] for event in trace['events'] if event['kind'] == 'Action']
                    self.assertEqual(actions, ['read_telemetry', 'read_knowledge'] + ([] if scenario == 'normal' else ['read_supplemental']))
                    reviews = [event for event in trace['events'] if event['kind'] == 'Review']
                    self.assertEqual(len(reviews), 1)
                    decisions = [event for event in trace['events'] if event['kind'] == 'Decision']
                    self.assertTrue(all(event['payload']['decision_source'] == 'fixed_program' for event in decisions))
                    self.assertEqual(len(decisions), trace['shared_state']['steps_used'])

    def test_workflow_shares_evidence_verifier_and_report_with_agent_patterns(self):
        for scenario in ('normal', 'missing', 'conflict'):
            with self.subTest(scenario=scenario):
                baseline = agents.run(pattern='workflow', scenario=scenario)
                integrated = agents.run(pattern='integrated', scenario=scenario)
                self.assertEqual(baseline['report'], integrated['report'])
                self.assertEqual(baseline['shared_state']['draft'], integrated['shared_state']['draft'])
        with patch.object(agents, 'validate_report', return_value=['测试校验拒绝']):
            rejected = agents.run(pattern='workflow')
        self.assertEqual(rejected['status'], 'needs_human')
        self.assertFalse(rejected['verified'])
        self.assertEqual(rejected['report'], '')
        self.assertEqual(rejected['shared_state']['review']['errors'], ['测试校验拒绝'])

    def test_workflow_is_deterministic_apart_from_run_id_and_timings(self):
        def without_timings(value):
            if isinstance(value, dict):
                return {key: without_timings(item) for key, item in value.items() if key not in ('run_id', 'elapsed_ms')}
            if isinstance(value, list):
                return [without_timings(item) for item in value]
            return value

        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                self.assertEqual(without_timings(agents.run(pattern='workflow', scenario=scenario)),
                                 without_timings(agents.run(pattern='workflow', scenario=scenario)))

    def test_workflow_budget_stops_before_any_unadmitted_step(self):
        for scenario, required_steps in (('normal', 6), ('missing', 7), ('conflict', 7), ('tool_failure', 7)):
            full = agents.run(pattern='workflow', scenario=scenario)
            for limit in range(1, required_steps + 1):
                with self.subTest(scenario=scenario, limit=limit):
                    trace = agents.run(pattern='workflow', scenario=scenario, max_steps=limit)
                    self.assertEqual(trace['shared_state']['steps_used'], limit)
                    actions = [event['payload']['tool'] for event in trace['events'] if event['kind'] == 'Action']
                    expected_tools = ['read_telemetry'] if limit == 2 else []
                    if limit >= 3:
                        expected_tools = ['read_telemetry', 'read_knowledge']
                    if scenario != 'normal' and limit >= 5:
                        expected_tools.append('read_supplemental')
                    self.assertEqual(actions, expected_tools)
                    self.assertEqual(trace['status'], full['status'] if limit == required_steps else 'stopped')
                    if limit < required_steps:
                        self.assertFalse(trace['verified'])
                        self.assertEqual(trace['report'], '')
                        self.assertFalse(any(event['kind'] in ('Review', 'Finish') for event in trace['events']))

    def test_parallel_and_integrated_really_fan_out(self):
        original = agents.ToolBox.call
        for pattern in ('parallel', 'integrated'):
            rendezvous = threading.Barrier(2)

            def simultaneous_reads(toolbox, name, arguments):
                if name in ('read_telemetry', 'read_knowledge'):
                    rendezvous.wait(timeout=3)
                return original(toolbox, name, arguments)

            with self.subTest(pattern=pattern), patch.object(agents.ToolBox, 'call', simultaneous_reads):
                self.assertEqual(agents.run(pattern=pattern)['status'], 'completed')

    def test_integrated_coordinates_recovery_before_draft_while_parallel_reviews_after_join(self):
        parallel = agents.run(pattern='parallel', scenario='missing')
        integrated = agents.run(pattern='integrated', scenario='missing')
        self.assertEqual([event['payload']['accepted'] for event in parallel['events'] if event['kind'] == 'Review'], [False, True])
        self.assertEqual([event['payload']['accepted'] for event in integrated['events'] if event['kind'] == 'Review'], [True])
        self.assertEqual(parallel['report'], integrated['report'])

    def test_real_graph_nodes_are_executed(self):
        trace = agents.run()
        nodes = [event['payload']['node'] for event in trace['events'] if event['kind'] == 'Decision']
        self.assertIn('evidence', nodes)
        self.assertIn('knowledge', nodes)
        self.assertIn('reviewer', nodes)
        self.assertEqual(trace['shared_state']['steps_used'], len(nodes))

    def test_budget_never_exceeds_node_limit(self):
        for pattern in PATTERNS:
            for limit in (1, 2, 3):
                with self.subTest(pattern=pattern, limit=limit):
                    trace = agents.run(pattern=pattern, max_steps=limit)
                    self.assertEqual(trace['status'], 'stopped')
                    self.assertLessEqual(trace['shared_state']['steps_used'], limit)
                    self.assertFalse(trace['verified'])
                    self.assertEqual(trace['report'], '')
                    self.assertFalse(any(event['kind'] == 'Finish' for event in trace['events']))

    def test_tools_are_read_only_and_allowlisted(self):
        toolbox = agents.ToolBox('normal')
        for name, arguments in [('shell', {}), ('clear_dtc', {}), ('read_telemetry', {'path': '../../private'}), ('read_supplemental', {'vehicle': 'real'})]:
            with self.subTest(name=name), self.assertRaises(agents.ToolError):
                toolbox.call(name, arguments)
        records = toolbox.call('read_telemetry', {})
        records[0]['value'] = 'changed'
        self.assertEqual(toolbox.call('read_telemetry', {})[0]['value'], 11.7)

    def test_validator_rejects_fabrication_and_inconsistent_claims(self):
        trace = agents.run(scenario='conflict')
        original = trace['shared_state']['draft']
        mutations = (
            lambda draft: draft['claims'][0].update(refs=['E-MADE-UP']),
            lambda draft: draft['claims'][0].update(value=14.8),
            lambda draft: draft['claims'][0].update(unit='kV'),
            lambda draft: draft.update(hypothesis='confirmed_abs_failure'),
            lambda draft: draft.update(diagnosis_confirmed=True),
            lambda draft: draft.update(recommended_action='clear_dtc'),
            lambda draft: draft.update(reconciliations=[]),
            lambda draft: draft['reconciliations'][0].update(selected_ref='E-VOLTAGE-OLD'),
            lambda draft: draft['reconciliations'][0].update(context_ref='E-MADE-UP'),
            lambda draft: draft['claims'].pop(),
            lambda draft: draft.update(report='车辆已修复'),
        )
        for mutate in mutations:
            draft = copy.deepcopy(original)
            mutate(draft)
            with self.subTest(draft=draft):
                self.assertFalse(agents.verify(trace['shared_state'], draft))

    def test_events_keep_original_snapshots(self):
        trace = agents.run(scenario='missing')
        plans = [event for event in trace['events'] if event['kind'] == 'Plan']
        self.assertEqual([event['plan_version'] for event in plans], [1, 2])
        self.assertIn('read_telemetry', plans[0]['payload']['steps'])
        self.assertEqual(plans[1]['payload']['steps'], ['read_supplemental', 'draft', 'review'])
        observation = next(event for event in trace['events'] if event['kind'] == 'Observation' and event['payload']['ok'])
        snapshot = copy.deepcopy(observation)
        trace['shared_state']['observations'][0]['records'].clear()
        trace['shared_state']['plan'].clear()
        self.assertEqual(observation, snapshot)
        self.assertIn('read_telemetry', plans[0]['payload']['steps'])

    def test_invalid_run_options_fail_before_execution(self):
        for arguments in ({'pattern': 'bad'}, {'scenario': 'bad'}, {'max_steps': True}, {'max_steps': 0}, {'max_steps': 31}, {'max_steps': 1.5}, {'mode': 'ollama', 'model': 'missing'}, {'model': 'ignored'}, {'pattern': []}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                agents.run(**arguments)

    def test_cli_exports_failure_trace_without_report(self):
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run([sys.executable, str(Path(agents.__file__)), '--pattern', 'integrated', '--scenario', 'tool_failure', '--max-steps', '30', '--output', output], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 1, result.stderr)
            traces = list(Path(output).glob('*-trace.json'))
            self.assertEqual(len(traces), 1)
            self.assertEqual(json.loads(traces[0].read_text(encoding='utf-8'))['report'], '')
            self.assertEqual(list(Path(output).glob('*-report.md')), [])

    def test_workflow_cli_exports_verified_report(self):
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run([sys.executable, str(Path(agents.__file__)), '--pattern', 'workflow', '--scenario', 'missing', '--output', output], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            trace = json.loads(next(Path(output).glob('*-trace.json')).read_text(encoding='utf-8'))
            self.assertEqual(trace['pattern'], 'workflow')
            self.assertTrue(trace['verified'])
            self.assertEqual(next(Path(output).glob('*-report.md')).read_text(encoding='utf-8'), trace['report'])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.worker = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.worker.join()
        cls.httpd.server_close()

    def request(self, method, path, payload=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.httpd.server_port, timeout=5)
        body = json.dumps(payload) if payload is not None else None
        options = {'Content-Type': 'application/json'}
        options.update(headers or {})
        try:
            connection.request(method, path, body, options)
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_health_readiness(self):
        status, body = self.request('GET', '/api/health')
        self.assertEqual(status, 200)
        health = json.loads(body)
        self.assertTrue(health['ready'])
        self.assertEqual(health['engine'], 'langgraph')
        self.assertEqual(health['patterns'], list(PATTERNS))
        self.assertEqual(health['modes'], ['simulation'])

    def test_run_contract(self):
        status, body = self.request('POST', '/api/run', {'pattern': 'parallel', 'scenario': 'normal'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['status'], 'completed')

    def test_workflow_run_contract(self):
        for scenario, expected in (('normal', 'completed'), ('missing', 'completed'), ('conflict', 'completed'), ('tool_failure', 'needs_human'), ('budget', 'stopped')):
            with self.subTest(scenario=scenario):
                status, body = self.request('POST', '/api/run', {'pattern': 'workflow', 'scenario': scenario})
                self.assertEqual(status, 200)
                trace = json.loads(body)
                self.assertEqual(trace['status'], expected)
                self.assertEqual({event['actor'] for event in trace['events']}, {'workflow'})

    def test_rejects_invalid_requests_before_graph_execution(self):
        invalid = [{}, [], {'pattern': 'other', 'scenario': 'normal'}, {'pattern': 'parallel', 'scenario': 'other'}, {'pattern': 'parallel', 'scenario': 'normal', 'max_steps': True}, {'pattern': 'parallel', 'scenario': 'normal', 'max_steps': 0}, {'pattern': 'parallel', 'scenario': 'normal', 'max_steps': 31}, {'pattern': 'parallel', 'scenario': 'normal', 'path': '/private'}, {'pattern': None, 'scenario': 'normal'}]
        with patch('server.run', side_effect=AssertionError('Invalid payload reached execution')):
            for payload in invalid:
                with self.subTest(payload=payload):
                    self.assertEqual(self.request('POST', '/api/run', payload)[0], 400)

    def test_origin_and_host_restrictions(self):
        payload = {'pattern': 'integrated', 'scenario': 'normal'}
        for headers in ({'Origin': 'https://evil.example'}, {'Origin': 'null'}, {'Host': 'evil.example'}, {'Origin': 'http://localhost:1'}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request('POST', '/api/run', payload, headers)[0], 403)
        self.assertEqual(self.request('POST', '/api/run', payload, {'Origin': f'http://localhost:{self.httpd.server_port}'})[0], 200)

    def test_no_generic_static_file_access(self):
        for path in ('/demo/agents.py', '/demo/fixtures.json', '/../README.md', '/.env'):
            with self.subTest(path=path):
                self.assertEqual(self.request('GET', path)[0], 404)


if __name__ == '__main__':
    unittest.main()
