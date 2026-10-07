"""Real host execution with controlled model responses, without provider requests."""
import _bootstrap
import copy
import unittest

from outing_live import PLACES, run_outing, validate_payload


class EvidenceModel:
    metadata = {'model': 'evidence-double', 'transport': 'test'}

    def __init__(self, weather='rain', budget=300):
        self.weather, self.budget = weather, budget
        self.contexts = []

    def generate(self, instruction, context, cancel):
        self.contexts.append(copy.deepcopy(context))
        answer = dict(summary='根据实际证据交付', calls=[], plan=[], reflection='', next_actor='', result=None)
        if 'required_calls' in context:
            answer['calls'] = context['required_calls']
        elif context.get('intent') == 'unclear':
            answer['summary'] = '请说明要安排出游还是只核算费用。'
        elif context.get('skill') == 'budget_check':
            answer['summary'] = '费用核算完成；未查天气，不能作出游建议。'
        else:
            suitable = [key for key, p in PLACES.items() if self.weather == 'sun' or p['indoor']]
            affordable = [key for key in suitable if sum(PLACES[key][x] for x in ['ticket', 'transport', 'meal']) <= self.budget]
            chosen = affordable[0] if affordable else ''
            answer['result'] = dict(status='recommended' if chosen else 'no_solution', place_id=chosen,
                total=sum(PLACES[chosen][x] for x in ['ticket', 'transport', 'meal']) if chosen else 0,
                citations=['WX01', 'D01', 'D02'] + ([chosen] if chosen else suitable), text='模型基于证据的最终回答')
        return answer, {}


class ArchitectureLiveTests(unittest.TestCase):
    def test_new_architectures_use_evidence_for_all_scenarios(self):
        for stage in [8, 9, 10]:
            for weather in ['rain', 'sun']:
                for budget in [100, 200, 300]:
                    with self.subTest(stage=stage, weather=weather, budget=budget):
                        model = EvidenceModel(weather, budget)
                        trace = run_outing(dict(stage=stage, weather=weather, budget=budget), model)
                        self.assertEqual(trace['status'], 'completed', trace['events'][-1])
                        self.assertTrue(trace['verified'])
                        suitable = [k for k, p in PLACES.items() if weather == 'sun' or p['indoor']]
                        chosen = next((k for k in suitable if sum(PLACES[k][x] for x in ['ticket', 'transport', 'meal']) <= budget), '')
                        self.assertEqual(trace['result']['place_id'], chosen)
                        self.assertTrue(model.contexts[-1]['observations'])

    def test_budget_skill_loads_only_cost_reference_and_never_reads_weather(self):
        model = EvidenceModel()
        trace = run_outing(dict(stage=8, intent='budget'), model)
        self.assertEqual(trace['status'], 'completed', trace['events'][-1])
        self.assertTrue(trace['verified'])
        self.assertEqual(trace['result']['status'], 'cost_checked')
        self.assertNotIn('WX01', trace['shared_state']['observations'])
        self.assertEqual({d['id'] for c in model.contexts for d in c['rules']}, {'D02'})
        self.assertEqual(trace['shared_state']['costs'], {'P01': 180, 'P02': 310, 'P03': 210})
        self.assertTrue(all(c.get('skill') == 'budget_check' for c in model.contexts))

    def test_unclear_intent_stops_before_skill_loading_or_tools(self):
        model = EvidenceModel()
        trace = run_outing(dict(stage=8, intent='unclear'), model)
        self.assertEqual(trace['status'], 'completed', trace['events'][-1])
        self.assertEqual(trace['result']['status'], 'needs_clarification')
        self.assertEqual(trace['metrics']['tool_calls'], 0)
        self.assertFalse(trace['verified'])
        self.assertNotIn('skill', trace['shared_state'])

    def test_skill_cannot_request_weather_outside_its_boundary(self):
        class EscapingModel(EvidenceModel):
            def generate(self, instruction, context, cancel):
                answer, usage = super().generate(instruction, context, cancel)
                answer['calls'] = [{'name': 'read_weather', 'place_id': ''}]
                return answer, usage
        trace = run_outing(dict(stage=8, intent='budget'), EscapingModel())
        self.assertEqual(trace['status'], 'failed')
        self.assertEqual(trace['metrics']['tool_calls'], 0)

    def test_blackboard_versions_and_readiness_match_simulation(self):
        model = EvidenceModel()
        trace = run_outing(dict(stage=9), model)
        self.assertEqual(trace['status'], 'completed', trace['events'][-1])
        writes = [e for e in trace['events'] if e['phase'] == '发布 Publish']
        self.assertEqual([e['actor'] for e in writes], ['weather', 'catalog', 'cost', 'summary'])
        self.assertEqual([e['data']['version'] for e in writes], [1, 2, 3, 4])
        triggers = [e for e in trace['events'] if e['phase'] == '触发 Trigger']
        self.assertEqual([e['actor'] for e in triggers], ['weather', 'catalog', 'cost', 'summary'])
        cost_context = next(c for c in model.contexts if c.get('role') == 'cost')
        self.assertTrue(cost_context['board']['catalog'])
        self.assertNotIn('WX01', cost_context['observations'])
        self.assertEqual(trace['shared_state']['board']['version'], 4)

    def test_graph_has_same_explicit_branches_and_exits(self):
        for weather, budget, branch, exit_node in [('rain', 300, 'indoor_filter', 'recommend'), ('sun', 100, 'all_places', 'no_solution')]:
            trace = run_outing(dict(stage=10, weather=weather, budget=budget), EvidenceModel(weather, budget))
            self.assertEqual(trace['status'], 'completed', trace['events'][-1])
            nodes = [e['data']['node'] for e in trace['events'] if e['phase'] == '节点 Node']
            self.assertEqual(nodes, ['weather', 'catalog', branch, 'cost', 'validate', exit_node])
            self.assertEqual(trace['metrics']['model_calls'], 1)
            observed_costs = {k for k in trace['shared_state']['observations'] if k.startswith('COST:')}
            self.assertEqual(observed_costs, {'COST:P02', 'COST:P03'} if weather == 'rain' else {'COST:P01', 'COST:P02', 'COST:P03'})

    def test_model_failure_preserves_new_architecture_evidence_without_success(self):
        class BrokenModel(EvidenceModel):
            def generate(self, instruction, context, cancel):
                raise RuntimeError('provider unavailable')
        for stage in [8, 9, 10]:
            trace = run_outing(dict(stage=stage), BrokenModel())
            self.assertEqual(trace['status'], 'failed')
            self.assertFalse(trace['verified'])
            self.assertIsNone(trace['result'])

    def test_intent_is_validated_and_cannot_leak_into_other_architectures(self):
        with self.assertRaises(ValueError):
            validate_payload(dict(stage=8, intent='filesystem'))
        with self.assertRaises(ValueError):
            validate_payload(dict(stage=9, intent='budget'))
