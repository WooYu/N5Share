"""Behavior checks: incomplete evidence, limits, pricing and trace isolation."""
import _bootstrap
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from collaboration_patterns import PATTERNS, run_demo


class CollaborationPatternsTests(unittest.TestCase):
    def test_all_patterns_account_for_food_transport_and_three_tickets(self):
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern):
                trace = run_demo(pattern)
                self.assertEqual(trace['status'], 'completed')
                self.assertEqual(trace['state']['proposal']['venue'], '城市博物馆')
                self.assertEqual(trace['state']['proposal']['total'], 240)
                self.assertTrue(trace['state']['approved'])

    def test_missing_food_is_recovered_except_in_fixed_chain(self):
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern):
                trace = run_demo(pattern, scenario='missing')
                research = [e for e in trace['events']
                            if e['actor'] == 'Researcher' and e['kind'] == 'work']
                self.assertNotIn('meal', research[0]['state']['evidence'])
                if pattern == 'sequential':
                    self.assertEqual(trace['status'], 'needs_input')
                    self.assertFalse(trace['state']['approved'])
                    self.assertEqual(len(research), 1)
                else:
                    self.assertEqual(trace['status'], 'completed')
                    self.assertEqual(len(research), 2)
                    self.assertEqual(trace['state']['proposal']['total'], 240)
                    self.assertEqual(research[1]['state']['evidence']['meal'], 90)

    def test_no_feasible_plan_is_an_explicit_result(self):
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern):
                trace = run_demo(pattern, budget=200)
                self.assertEqual(trace['status'], 'no_solution')
                self.assertIsNone(trace['state']['proposal']['venue'])
                self.assertTrue(trace['state']['approved'])
                self.assertEqual(trace['state']['proposal']['total'], None)

    def test_sun_allows_cheaper_outdoor_candidate(self):
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern):
                trace = run_demo(pattern, weather='sun', budget=200)
                self.assertEqual(trace['status'], 'completed')
                self.assertEqual(trace['state']['proposal']['venue'], '滨河公园')
                self.assertEqual(trace['state']['proposal']['total'], 150)

    def test_budget_stops_before_excess_work_and_keeps_partial_evidence(self):
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern):
                trace = run_demo(pattern, max_steps=1)
                self.assertEqual(trace['status'], 'step_limit')
                self.assertEqual(trace['steps'], 1)
                self.assertFalse(trace['state']['approved'])
                self.assertTrue(trace['events'])
                self.assertEqual(trace['events'][-1]['kind'], 'stop')

    def test_snapshots_and_runs_do_not_share_mutable_state(self):
        first = run_demo('swarm', scenario='missing')
        early = next(e for e in first['events'] if e['kind'] == 'work')
        self.assertNotIn('meal', early['state']['evidence'])
        first['state']['evidence']['meal'] = -1
        self.assertEqual(run_demo('swarm')['state']['evidence']['meal'], 90)

    def test_invalid_inputs_are_rejected(self):
        for args in ({'pattern': 'other'}, {'pattern': 'swarm', 'max_steps': 0},
                     {'pattern': 'network', 'scenario': 'other'},
                     {'pattern': 'network', 'budget': -1},
                     {'pattern': 'network', 'weather': 'snow'}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                run_demo(**args)

    def test_cli_writes_five_real_traces_and_offline_report(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str((Path(__file__).resolve().parents[1] / 'demo/reference/collaboration_patterns.py')),
                 '--pattern', 'all', '--scenario', 'missing', '--output', directory],
                capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Researcher', result.stdout)
            self.assertIn('needs_input', result.stdout)
            paths = list(Path(directory).rglob('*-trace.json'))
            self.assertEqual(len(paths), 5)
            statuses = [json.loads(p.read_text(encoding='utf-8'))['status'] for p in paths]
            self.assertEqual(statuses.count('completed'), 4)
            self.assertEqual(statuses.count('needs_input'), 1)
            self.assertTrue(list(Path(directory).rglob('comparison.html')))


if __name__ == '__main__':
    unittest.main()
