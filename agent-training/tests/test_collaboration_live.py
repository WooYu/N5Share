"""Actual graph boundaries and dataflow with only the external model stubbed."""
import _bootstrap
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))


class ScriptedModel:
    """External response fixture; never imported by the delivered examples."""
    metadata = {'provider': 'test response fixture', 'model': 'test'}
    timeout = 30

    def generate_json(self, instruction, context, cancel, schema):
        state, role = context['state'], context['role']
        choices = context['allowed_next']
        answer = dict(summary='测试返回', tool='', next='', venue='', total=0,
                      text='', approved=False)
        evidence = state.get('evidence', {})
        if role in ('Supervisor', 'CEO', 'ResearchLead', 'DeliveryLead'):
            if role == 'ResearchLead':
                target = 'END' if state.get('research_done') else 'Researcher'
            elif role == 'CEO':
                target = 'END' if state.get('approved') else 'research_team' if not evidence or state.get('needs_research') else 'delivery_team'
            else:
                target = 'END' if state.get('approved') else 'Researcher' if 'meal' not in evidence else 'Analyst' if not state.get('analyzed') else 'Writer' if not state.get('proposal') else 'Critic'
                if role == 'DeliveryLead' and target == 'Researcher':
                    target = 'ESCALATE'
            answer['next'] = target
        elif role == 'Researcher':
            if not context['observations']:
                answer['tool'] = 'read_sources'
            elif choices:
                answer['next'] = 'Critic' if 'Analyst' not in choices else 'Analyst'
        elif role == 'Analyst':
            if not context['observations']:
                answer['tool'] = 'calculate_costs'
            elif choices:
                answer['next'] = 'Researcher' if 'meal' not in evidence else 'Writer'
        elif role == 'Writer':
            if state.get('analyzed'):
                answer.update(venue='城市博物馆', total=240, text='城市博物馆，三人合计240元。')
                if choices:
                    answer['next'] = 'Critic'
            elif choices:
                answer['next'] = 'Researcher' if 'Researcher' in choices else 'Critic'
        elif role == 'Critic':
            answer['approved'] = bool(state.get('proposal') and state.get('analyzed') and 'meal' in evidence)
            if choices:
                answer['next'] = 'END' if answer['approved'] else 'Researcher' if 'meal' not in evidence else 'Analyst' if not state.get('analyzed') else 'Writer'
        return answer, {'input_tokens': 1, 'output_tokens': 1}


class LiveCollaborationTests(unittest.TestCase):
    def run_pattern(self, pattern, scenario='normal', **kwargs):
        from collaboration_live.runtime import run_demo
        return run_demo(pattern, scenario=scenario, model=ScriptedModel(), **kwargs)

    def test_same_complete_evidence_produces_reviewed_result_in_all_five_graphs(self):
        for pattern in ('sequential', 'supervisor', 'hierarchical', 'swarm', 'network'):
            with self.subTest(pattern=pattern):
                trace = self.run_pattern(pattern)
                self.assertEqual(trace['status'], 'completed')
                self.assertTrue(trace['state']['approved'])
                self.assertEqual(trace['state']['proposal']['total'], 240)
                self.assertGreater(trace['model_calls'], 0)
                self.assertTrue(any(event['kind'] == 'tool_result' for event in trace['events']))

    def test_missing_sources_stop_fixed_chain_but_return_through_actual_feedback_paths(self):
        sequential = self.run_pattern('sequential', 'missing')
        self.assertEqual(sequential['status'], 'needs_input')
        self.assertNotIn('meal', sequential['state']['evidence'])
        for pattern in ('supervisor', 'hierarchical', 'swarm', 'network'):
            with self.subTest(pattern=pattern):
                trace = self.run_pattern(pattern, 'missing')
                self.assertEqual(trace['status'], 'completed')
                self.assertEqual(trace['state']['research_rounds'], 2)
                if pattern == 'hierarchical':
                    self.assertTrue(any(event['kind'] == 'escalate' for event in trace['events']))
                    self.assertTrue(any(len(event.get('namespace', [])) > 0 for event in trace['events'] if event['kind'] == 'graph_update'))

    def test_bad_model_route_and_fabricated_approval_cannot_deliver_success(self):
        from collaboration_live.runtime import run_demo
        class InvalidRoute(ScriptedModel):
            def generate_json(self, instruction, context, cancel, schema):
                answer, usage = super().generate_json(instruction, context, cancel, schema)
                answer['next'] = 'UnknownAgent'
                return answer, usage
        self.assertEqual(run_demo('network', model=InvalidRoute())['status'], 'failed')
        class BadDraft(ScriptedModel):
            def generate_json(self, instruction, context, cancel, schema):
                answer, usage = super().generate_json(instruction, context, cancel, schema)
                if context['role'] == 'Writer':
                    answer['total'] = 0
                return answer, usage
        trace = run_demo('sequential', model=BadDraft())
        self.assertEqual(trace['status'], 'needs_input')
        self.assertFalse(trace['state']['approved'])

    def test_call_limit_preserves_events_and_never_calls_an_extra_model(self):
        trace = self.run_pattern('supervisor', max_model_calls=1)
        self.assertEqual(trace['status'], 'stopped')
        self.assertEqual(trace['model_calls'], 1)
        self.assertFalse(trace['state']['approved'])

    def test_report_cannot_replace_verified_facts_with_contradictory_model_prose(self):
        from collaboration_live.runtime import run_demo, render_report
        class WrongProse(ScriptedModel):
            def generate_json(self, instruction, context, cancel, schema):
                answer, usage = super().generate_json(instruction, context, cancel, schema)
                if context['role'] == 'Writer':
                    answer['text'] = 'Recommend the outdoor park for 0 CNY.'
                return answer, usage
        trace = run_demo('sequential', model=WrongProse())
        report = render_report(trace)
        self.assertEqual(trace['status'], 'completed')
        self.assertIn('城市博物馆；合计 240 元', report)
        self.assertNotIn('outdoor park', report)
        self.assertIn('outdoor park', trace['state']['proposal']['text'])

    def test_invalid_action_is_returned_to_model_before_any_tool_execution(self):
        class RecoveringModel(ScriptedModel):
            rejected = False
            def generate_json(self, instruction, context, cancel, schema):
                answer, usage = super().generate_json(instruction, context, cancel, schema)
                if not self.rejected:
                    self.rejected = True
                    answer['next'] = 'UnknownAgent'
                elif context.get('correction'):
                    self.feedback = context['correction']
                return answer, usage
        from collaboration_live.runtime import run_demo
        model = RecoveringModel()
        trace = run_demo('network', model=model)
        self.assertEqual(trace['status'], 'completed')
        self.assertIn('未执行被拒绝', model.feedback)
        self.assertEqual(sum(event['kind'] == 'model_rejected' for event in trace['events']), 1)

    def test_transport_failure_switches_supplier_and_preserves_current_evidence(self):
        from collaboration_live.runtime import run_demo
        from model_backup import ModelRouter
        from model_gateway import ModelUnavailable
        class FailingPrimary(ScriptedModel):
            metadata = {'provider': 'DeepSeek', 'model': 'primary'}
            def generate_json(self, instruction, context, cancel, schema):
                if context['state'].get('evidence'):
                    raise ModelUnavailable('连接失败')
                return super().generate_json(instruction, context, cancel, schema)
        backup = ScriptedModel()
        backup.metadata = {'provider': 'OpenAI/Codex', 'model': 'backup'}
        trace = run_demo('sequential', model=ModelRouter(FailingPrimary(), backup))
        self.assertEqual(trace['status'], 'completed')
        self.assertEqual(trace['model']['provider'], 'OpenAI/Codex')
        self.assertEqual(trace['state']['research_rounds'], 1)
        self.assertEqual(sum(event['kind'] == 'model_switch' for event in trace['events']), 1)

    def test_deepseek_is_primary_and_configuration_failure_uses_existing_codex(self):
        import model_backup
        from model_gateway import ModelUnavailable
        deepseek, codex = ScriptedModel(), ScriptedModel()
        deepseek.metadata = {'provider': 'DeepSeek', 'model': 'primary'}
        codex.metadata = {'provider': 'OpenAI/Codex', 'model': 'backup'}
        with patch.object(model_backup, 'DeepSeekModel', return_value=deepseek), patch.object(model_backup, 'CodexModel', return_value=codex):
            model = model_backup.create_model()
            self.assertEqual(model.metadata['provider'], 'DeepSeek')
            self.assertTrue(model.activate_fallback())
            self.assertEqual(model.metadata['provider'], 'OpenAI/Codex')
        with patch.object(model_backup, 'DeepSeekModel', side_effect=ModelUnavailable('未配置')), patch.object(model_backup, 'CodexModel', return_value=codex):
            self.assertTrue(model_backup.create_model().metadata['using_backup'])

    def test_generic_schema_reaches_deepseek_without_the_old_outing_role_restrictions(self):
        import httpx
        from model_backup import DeepSeekModel
        response = {'next': 'Researcher'}
        def reply(request):
            payload = json.loads(request.content)
            self.assertIn('Researcher', payload['messages'][0]['content'])
            return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(response)}}], 'usage': {'prompt_tokens': 2, 'completion_tokens': 3}})
        model = DeepSeekModel('unit-test-credential', transport=httpx.MockTransport(reply))
        schema = {'type': 'object', 'properties': {'next': {'type': 'string', 'enum': ['Researcher']}}, 'required': ['next'], 'additionalProperties': False}
        answer, usage = model.generate_json('Choose next', {}, threading.Event(), schema)
        self.assertEqual(answer, response)
        self.assertEqual(usage['output_tokens'], 3)


if __name__ == '__main__':
    unittest.main()
