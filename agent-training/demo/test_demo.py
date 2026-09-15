"""Behavioral tests: independently calculated sample totals and recovery contracts."""
import unittest
from unittest.mock import patch
from copy import deepcopy
from pathlib import Path
from agents import run, ToolBox, ToolError, verify

DATA = Path(__file__).with_name('orders.csv')

class DemoTests(unittest.TestCase):
    def test_normal_result(self):
        state = run(DATA, inject_failure=False)
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(state['result']['net_sales'], '2650.00')
        self.assertEqual(state['result']['completed_orders'], 6)
        self.assertEqual(state['result']['by_category'], {'办公': '1450.00', '数码': '1200.00'})
        self.assertEqual(state['result']['order_ids'], ['O001','O002','O004','O005','O006','O008'])

    def test_field_error_causes_revision_and_memory(self):
        state = run(DATA, inject_failure=True)
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(state['plan_version'], 2)
        self.assertTrue(state['memory'])
        self.assertTrue(any(e['kind'] == 'Observation' and not e['payload']['ok'] for e in state['events']))
        self.assertEqual(state['result']['net_sales'], '2650.00')

    def test_budget_stops_with_no_success_report(self):
        state = run(DATA, max_steps=1)
        self.assertEqual(state['status'], 'stopped')
        self.assertIsNone(state['result'])
        self.assertFalse(state['verified'])

    def test_tool_allowlist(self):
        with self.assertRaises(ToolError):
            ToolBox(DATA).call('shell', {'command': 'anything'})

    def test_wrong_field_is_an_observation_not_silent_default(self):
        with self.assertRaisesRegex(ToolError, 'sales'):
            ToolBox(DATA).call('aggregate', {'gross_field':'sales','refund_field':'refund','status':'completed'})

    def test_cannot_choose_another_file(self):
        with self.assertRaises(ToolError):
            ToolBox(DATA).call('inspect', {'path':'../../private.csv'})

    def test_plan_events_keep_original_snapshot_after_execution(self):
        state = run(DATA, inject_failure=True)
        plans = [e['payload']['steps'] for e in state['events'] if e['kind']=='Plan']
        self.assertEqual([s['id'] for s in plans[0]], ['S1','S2','S3'])
        self.assertEqual([s['id'] for s in plans[1]], ['S2','S3'])

    def test_validator_rejects_tampered_category(self):
        result = deepcopy(run(DATA)['result'])
        result['by_category']['办公'] = '1451.00'
        self.assertFalse(verify(DATA, result))

    def test_unavailable_model_fails_without_simulated_success(self):
        with patch('agents.LocalModel.ask', side_effect=TimeoutError('transport unavailable')):
            state = run(DATA, mode='ollama', model='test-transport')
        self.assertEqual(state['mode'], 'ollama')
        self.assertEqual(state['status'], 'failed')
        self.assertFalse(state['verified'])
        self.assertIsNone(state['result'])

    def test_invalid_model_plan_is_not_executed(self):
        with patch('agents.LocalModel.ask', return_value={'steps':[{'id':'S3'}]}):
            state = run(DATA, mode='ollama', model='test-transport')
        self.assertEqual(state['status'], 'failed')
        self.assertFalse(any(e['kind']=='Action' for e in state['events']))

if __name__ == '__main__':
    unittest.main()
