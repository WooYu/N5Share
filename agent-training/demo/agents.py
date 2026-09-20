"""Real LangGraph orchestration; rule-simulated decisions and synthetic read-only tools.

max_steps counts executed graph nodes, including both branches of a fan-out.
verified means the report evidence contract passed, never diagnostic truth.
No inference service, vehicle connection, or vehicle action is available.
workflow is a fixed program baseline, not an Agent or supervisor delegation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import operator
from pathlib import Path
import sys
import threading
import time
from typing import Annotated, TypedDict
import uuid

from langgraph.graph import END, START, StateGraph

PATTERNS = ('workflow', 'supervisor', 'parallel', 'review', 'integrated')
SCENARIOS = ('normal', 'missing', 'conflict', 'tool_failure', 'budget')
TOOLS = ('read_telemetry', 'read_knowledge', 'read_supplemental')
REQUIRED_FIELDS = ('voltage', 'dtc', 'gateway')
FIELD_LABELS = {'voltage': '电压', 'dtc': '故障码', 'gateway': '网关连通'}
FIXTURES = Path(__file__).with_name('fixtures.json')
RECONCILIATION_REASON = '按补充事件索引匹配事件时刻；较早缓存值保留为历史记录，不用于当前事件判断。'


def validate_options(pattern, scenario, max_steps=30, mode='simulation', model=None):
    if not isinstance(pattern, str) or pattern not in PATTERNS:
        raise ValueError('pattern must be one of: ' + ', '.join(PATTERNS))
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        raise ValueError('scenario must be one of: ' + ', '.join(SCENARIOS))
    if type(max_steps) is not int or not 1 <= max_steps <= 30:
        raise ValueError('max_steps must be an integer from 1 to 30')
    if mode != 'simulation' or model is not None:
        raise ValueError('Only explicit rule simulation is supported; Ollama/model options are unavailable')


class ToolError(ValueError):
    pass


class ToolBox:
    """A fixed fixture is the only data source; calls return independent snapshots."""

    def __init__(self, scenario='normal'):
        validate_options('integrated', scenario)
        self.fixtures = json.loads(FIXTURES.read_text(encoding='utf-8'))
        if self.fixtures.get('synthetic') is not True:
            raise ValueError('Only synthetic fixtures are allowed')
        self.scenario = self.fixtures['scenarios'][scenario]

    def call(self, name, arguments):
        if not isinstance(name, str) or name not in TOOLS or type(arguments) is not dict or arguments:
            raise ToolError('Tool or arguments outside the read-only allowlist')
        if name in self.scenario['failing_tools']:
            raise ToolError('Synthetic telemetry service persistently unavailable')
        if name == 'read_knowledge':
            references = self.fixtures['knowledge']
        else:
            references = self.scenario['telemetry' if name == 'read_telemetry' else 'supplemental']
        return deepcopy([self.fixtures['records'][reference] for reference in references])


class DiagnosisState(TypedDict, total=False):
    observations: Annotated[list[dict], operator.add]
    plan: list[str]
    plan_version: int
    revision_rounds: int
    issues: list[str]
    draft: dict
    review: dict
    status: str
    report: str
    verified: bool


def observed_records(state):
    records = {}
    for observation in state.get('observations', []):
        if observation.get('ok') and observation.get('tool') in TOOLS:
            for record in observation['records']:
                if record['id'] in records and records[record['id']] != record:
                    raise ValueError('One evidence ID has inconsistent observations')
                records[record['id']] = record
    return records


def evidence_issues(state):
    records = observed_records(state)
    issues = []
    for field in REQUIRED_FIELDS:
        candidates = [record for record in records.values() if record['field'] == field]
        if not candidates:
            issues.append(f'缺少{FIELD_LABELS[field]}证据（{field}）')
        elif len({json.dumps(record['value']) for record in candidates}) > 1:
            context = records.get('E-INCIDENT')
            if not context or sum(record['observed_at'] == context['value'] for record in candidates) != 1:
                issues.append(f'{FIELD_LABELS[field]}证据冲突：缺少唯一匹配事件时刻的记录（{field}）')
    if 'K-LOW-VOLTAGE' not in records:
        issues.append('缺少低电压知识规则（K-LOW-VOLTAGE）')
    return issues


def make_draft(state):
    records = observed_records(state)
    claims, reconciliations = [], []
    context = records.get('E-INCIDENT')
    for field in REQUIRED_FIELDS:
        candidates = [record for record in records.values() if record['field'] == field]
        if not candidates:
            continue
        selected = candidates[0]
        if len(candidates) > 1 and context:
            matching = [record for record in candidates if record['observed_at'] == context['value']]
            if len(matching) == 1:
                selected = matching[0]
                reconciliations.append({'field': field, 'selected_ref': selected['id'],
                    'rejected_refs': sorted(record['id'] for record in candidates if record != selected),
                    'context_ref': context['id'], 'reason': RECONCILIATION_REASON})
        claims.append({'field': field, 'value': selected['value'], 'unit': selected['unit'], 'refs': [selected['id']]})
    voltage = next((claim for claim in claims if claim['field'] == 'voltage'), None)
    dtc = next((claim for claim in claims if claim['field'] == 'dtc'), None)
    rule = records.get('K-LOW-VOLTAGE')
    supported = bool(voltage and dtc and rule and voltage['value'] < rule['value'] and dtc['value'] == 'U0121')
    return {'claims': claims, 'hypothesis': 'possible_low_voltage' if supported else 'insufficient_evidence',
            'hypothesis_refs': [*voltage['refs'], *dtc['refs'], rule['id']] if supported else [],
            'reconciliations': reconciliations, 'diagnosis_confirmed': False,
            'recommended_action': 'human_review_only'}


def validate_report(state, draft):
    """Validate claims against received tool records, not against generated prose."""
    errors = []
    expected_keys = {'claims', 'hypothesis', 'hypothesis_refs', 'reconciliations', 'diagnosis_confirmed', 'recommended_action'}
    try:
        if not isinstance(draft, dict) or set(draft) != expected_keys:
            return ['报告结构无效：必须包含证据、假设及引用、冲突核对和人工审核标记']
        if draft['diagnosis_confirmed'] is not False or draft['recommended_action'] != 'human_review_only':
            errors.append('报告只能提交待人工审核的假设，不得确认故障或授权车辆操作')
        records = observed_records(state)
        claims = draft['claims']
        if not isinstance(claims, list):
            return errors + ['证据列表格式无效：claims 必须是列表']
        if any(not isinstance(claim, dict) or not isinstance(claim.get('field'), str) for claim in claims):
            return errors + ['证据条目格式无效：每条证据必须包含字符串字段名 field']
        fields = [claim['field'] for claim in claims]
        field_errors = []
        for field in REQUIRED_FIELDS:
            count = fields.count(field)
            if count == 0:
                field_errors.append(f'缺少{FIELD_LABELS[field]}证据：报告未提供 {field} 字段')
            elif count > 1:
                field_errors.append(f'{FIELD_LABELS[field]}证据重复：{field} 字段应有且仅有一条，实际 {count} 条')
        for field in sorted(set(fields) - set(REQUIRED_FIELDS)):
            field_errors.append('未知证据字段：' + field)
        if field_errors:
            return errors + field_errors
        by_field = {}
        for claim in claims:
            label = FIELD_LABELS[claim['field']]
            if (set(claim) != {'field', 'value', 'unit', 'refs'} or not isinstance(claim['refs'], list)
                    or len(claim['refs']) != 1 or not isinstance(claim['refs'][0], str)):
                return errors + [f'{label}证据条目格式无效：需要 field、value、unit 和唯一字符串引用 refs']
            record = records.get(claim['refs'][0])
            if not record:
                errors.append(f'{label}证据引用不存在：{claim["refs"][0]} 未出现在已接收的工具记录中')
            else:
                mismatches = [key for key in ('field', 'value', 'unit')
                              if claim[key] != record[key] or type(claim[key]) is not type(record[key])]
                if mismatches:
                    errors.append(f'{label}证据与引用 {record["id"]} 不一致：' + '、'.join(mismatches))
            by_field[claim['field']] = claim
        expected_conflicts = []
        for field, claim in by_field.items():
            candidates = [record for record in records.values() if record['field'] == field]
            if len(candidates) > 1:
                context = records.get('E-INCIDENT')
                matching = [record for record in candidates if context and record['observed_at'] == context['value']]
                if len(matching) != 1 or claim['refs'] != [matching[0]['id']]:
                    errors.append(f'{FIELD_LABELS[field]}证据冲突：必须引用唯一匹配事件时刻的记录（{field}）')
                    continue
                expected_conflicts.append({'field': field, 'selected_ref': matching[0]['id'],
                    'rejected_refs': sorted(record['id'] for record in candidates if record['id'] != matching[0]['id']),
                    'context_ref': context['id'], 'reason': RECONCILIATION_REASON})
        if draft['reconciliations'] != expected_conflicts:
            errors.append('冲突核对不完整：须保留全部来源，并说明选用记录、历史记录及事件时刻依据')
        voltage, dtc = by_field['voltage'], by_field['dtc']
        rule = records.get('K-LOW-VOLTAGE')
        if not rule or rule['field'] != 'voltage_threshold' or voltage['unit'] != rule['unit']:
            errors.append('缺少适用的低电压知识规则，或规则单位与电压证据不一致（K-LOW-VOLTAGE）')
        elif not (voltage['value'] < rule['value'] and dtc['value'] == 'U0121'):
            errors.append('低电压假设缺少支持：电压须低于规则阈值，且故障码须为 U0121')
        if draft['hypothesis'] != 'possible_low_voltage':
            errors.append('假设不受支持：当前证据仅支持低电压可能参与故障，不能确认原因')
        if draft['hypothesis_refs'] != voltage['refs'] + dtc['refs'] + ['K-LOW-VOLTAGE']:
            errors.append('假设引用不完整或不一致：须引用电压、故障码及低电压知识规则')
    except (KeyError, TypeError, ValueError, IndexError):
        errors.append('证据契约格式无效：请检查字段、数值类型和引用结构')
    return errors


def verify(shared_state, draft):
    return not validate_report(shared_state, draft)


def render_report(state):
    draft = state['draft']
    records = observed_records(state)
    lines = ['合成数据远程诊断报告（待人工审核）', '以下仅通过报告证据契约校验，不代表真实诊断结论。']
    for claim in draft['claims']:
        lines.append(f"{claim['field']}: {claim['value']} {claim['unit']} [{', '.join(claim['refs'])}]")
    for resolution in draft['reconciliations']:
        historical = '；'.join(f"{reference}={records[reference]['value']} {records[reference]['unit']} @ {records[reference]['observed_at']}" for reference in resolution['rejected_refs'])
        selected = records[resolution['selected_ref']]
        lines.append(f"冲突核对：{historical}；选用 {selected['id']}={selected['value']} @ {selected['observed_at']}。{resolution['reason']} [{resolution['context_ref']}]")
    lines.append('假设：低电压可能与通信故障记录有关，因果关系尚未确认。[' + ', '.join(draft['hypothesis_refs']) + ']')
    lines.append('仍需人工结合现场测量确认；本演示不执行清码、刷写、复位或任何车辆操作。')
    return '\n'.join(lines)


class GraphRun:
    """Per-run event journal and atomic node budget, shared by actual graph branches."""

    def __init__(self, toolbox, max_steps):
        self.toolbox = toolbox
        self.max_steps = max_steps
        self.steps_used = 0
        self.tool_calls = 0
        self.stopped = False
        self.events = []
        self.lock = threading.RLock()

    def emit(self, actor, kind, payload, version):
        with self.lock:
            self.events.append({'id': f'E{len(self.events) + 1:03}', 'actor': actor, 'kind': kind,
                                'payload': deepcopy(payload), 'plan_version': version})

    def node(self, name, actor, function):
        def execute(state):
            with self.lock:
                if self.stopped or self.steps_used >= self.max_steps:
                    self.stopped = True
                    return {}
                self.steps_used += 1
                self.emit(actor, 'Decision', {'node': name, 'decision_source': 'fixed_program' if actor == 'workflow' else 'rule_simulation',
                          'step': self.steps_used}, state['plan_version'])
            return function(state)
        return execute

    def read(self, actor, name, state):
        with self.lock:
            self.tool_calls += 1
            self.emit(actor, 'Action', {'tool': name, 'args': {}, 'read_only': True}, state['plan_version'])
        started = time.perf_counter()
        try:
            records = self.toolbox.call(name, {})
            observation = {'tool': name, 'ok': True, 'records': records}
        except ToolError as error:
            observation = {'tool': name, 'ok': False, 'records': [], 'error': str(error)}
        observation['elapsed_ms'] = round((time.perf_counter() - started) * 1000, 3)
        self.emit(actor, 'Observation', observation, state['plan_version'])
        return {'observations': [observation]}

    def coordinator(self, state):
        plan = ['read_telemetry', 'read_knowledge', 'draft', 'review']
        self.emit('coordinator', 'Plan', {'steps': plan, 'decision_source': 'rule_simulation'}, 1)
        return {'plan': plan, 'plan_version': 1}

    def dispatch(self, state):
        self.emit('coordinator', 'Dispatch', {'next_actor': 'knowledge', 'received_observations': len(state['observations'])}, state['plan_version'])
        return {}

    def assess(self, state):
        issues = evidence_issues(state)
        self.emit('coordinator', 'Assessment', {'issues': issues, 'next': 'supplemental_read' if issues else 'draft'}, state['plan_version'])
        return {'issues': issues}

    def revise(self, state):
        version = state['plan_version'] + 1
        plan = ['read_supplemental', 'draft', 'review']
        self.emit('coordinator', 'Revision', {'reason': state['issues'], 'strategy': '一次补充读取；仍不可用则提交人工'}, version)
        self.emit('coordinator', 'Plan', {'steps': plan, 'decision_source': 'rule_simulation'}, version)
        return {'plan': plan, 'plan_version': version, 'revision_rounds': state['revision_rounds'] + 1}

    def draft(self, state):
        draft = make_draft(state)
        self.emit('coordinator', 'Draft', draft, state['plan_version'])
        return {'draft': draft}

    def reviewer(self, state):
        return self.validate(state, 'reviewer', allow_revision=True)

    def validate(self, state, actor, allow_revision=False):
        errors = validate_report(state, state['draft'])
        review = {'accepted': not errors, 'errors': errors, 'scope': 'report_evidence_contract_only'}
        self.emit(actor, 'Review', review, state['plan_version'])
        if not errors:
            self.emit(actor, 'Finish', {'verified': True, 'human_review': 'pending', 'vehicle_actions_allowed': False}, state['plan_version'])
            return {'review': review, 'status': 'completed', 'verified': True, 'report': render_report(state), 'issues': []}
        if not allow_revision or state['revision_rounds']:
            reason = '固定工作流校验未通过，提交人工复核' if not allow_revision else '补充读取后证据仍不满足契约'
            self.emit(actor, 'Stop', {'reason': reason, 'errors': errors}, state['plan_version'])
            return {'review': review, 'status': 'needs_human', 'issues': errors}
        return {'review': review, 'issues': errors}

    def compile_workflow(self):
        """Fixed sequence with one conditional read and one terminal validation."""
        graph = StateGraph(DiagnosisState)

        def fixed_plan(state):
            plan = ['read_telemetry', 'read_knowledge', 'check_evidence', 'read_supplemental', 'draft', 'validate']
            self.emit('workflow', 'Plan', {'steps': plan, 'conditional_steps': ['read_supplemental'],
                      'decision_source': 'fixed_program'}, 1)
            return {'plan': plan, 'plan_version': 1}

        def check_evidence(state):
            issues = evidence_issues(state)
            self.emit('workflow', 'Assessment', {'issues': issues, 'next': 'read_supplemental' if issues else 'draft',
                      'decision_source': 'fixed_program'}, state['plan_version'])
            return {'issues': issues}

        def draft_report(state):
            draft = make_draft(state)
            self.emit('workflow', 'Draft', draft, state['plan_version'])
            return {'draft': draft}

        nodes = {
            'workflow': fixed_plan,
            'read_telemetry': lambda state: self.read('workflow', 'read_telemetry', state),
            'read_knowledge': lambda state: self.read('workflow', 'read_knowledge', state),
            'check_evidence': check_evidence,
            'read_supplemental': lambda state: self.read('workflow', 'read_supplemental', state),
            'draft': draft_report,
            'validate': lambda state: self.validate(state, 'workflow'),
        }
        for name, function in nodes.items():
            graph.add_node(name, self.node(name, 'workflow', function))

        def route(source, destination):
            graph.add_conditional_edges(source, lambda state: END if self.stopped else destination)

        graph.add_edge(START, 'workflow')
        route('workflow', 'read_telemetry')
        route('read_telemetry', 'read_knowledge')
        route('read_knowledge', 'check_evidence')
        graph.add_conditional_edges('check_evidence', lambda state: END if self.stopped else ('read_supplemental' if state['issues'] else 'draft'))
        route('read_supplemental', 'draft')
        route('draft', 'validate')
        graph.add_edge('validate', END)
        return graph.compile()

    def compile(self, pattern):
        if pattern == 'workflow':
            return self.compile_workflow()
        graph = StateGraph(DiagnosisState)
        nodes = {
            'coordinator': ('coordinator', self.coordinator),
            'evidence': ('evidence', lambda state: self.read('evidence', 'read_telemetry', state)),
            'knowledge': ('knowledge', lambda state: self.read('knowledge', 'read_knowledge', state)),
            'dispatch': ('coordinator', self.dispatch),
            'assess': ('coordinator', self.assess),
            'revise': ('coordinator', self.revise),
            'supplement': ('evidence', lambda state: self.read('evidence', 'read_supplemental', state)),
            'draft': ('coordinator', self.draft),
            'reviewer': ('reviewer', self.reviewer),
        }
        for name, (actor, function) in nodes.items():
            graph.add_node(name, self.node(name, actor, function))

        def route(source, destination):
            graph.add_conditional_edges(source, lambda state: END if self.stopped else destination)

        graph.add_edge(START, 'coordinator')
        if pattern in ('parallel', 'integrated'):
            graph.add_edge('coordinator', 'evidence')
            graph.add_edge('coordinator', 'knowledge')
            graph.add_edge(['evidence', 'knowledge'], 'assess' if pattern == 'integrated' else 'draft')
        else:
            route('coordinator', 'evidence')
            if pattern == 'supervisor':
                route('evidence', 'dispatch')
                route('dispatch', 'knowledge')
            else:
                route('evidence', 'knowledge')
            route('knowledge', 'draft' if pattern == 'review' else 'assess')
        graph.add_conditional_edges('assess', lambda state: END if self.stopped else ('revise' if state['issues'] else 'draft'))
        route('revise', 'supplement')
        route('supplement', 'draft')
        route('draft', 'reviewer')
        graph.add_conditional_edges('reviewer', lambda state: END if self.stopped or state['status'] != 'running' else 'revise')
        return graph.compile()


def run(pattern='integrated', scenario='normal', max_steps=30, mode='simulation', model=None):
    validate_options(pattern, scenario, max_steps, mode, model)
    started = time.perf_counter()
    effective_budget = min(max_steps, 2) if scenario == 'budget' else max_steps
    state = {'observations': [], 'plan': [], 'plan_version': 0, 'revision_rounds': 0,
             'issues': [], 'draft': {}, 'review': {}, 'status': 'running', 'report': '', 'verified': False}
    runtime = GraphRun(None, effective_budget)
    actor = 'workflow' if pattern == 'workflow' else 'coordinator'
    decision_source = 'fixed_program' if pattern == 'workflow' else 'rule_simulation'
    runtime.emit(actor, 'Start', {'mode': mode, 'engine': 'langgraph', 'pattern': pattern,
                 'scenario': scenario, 'decision_source': decision_source, 'synthetic': True,
                 'max_steps': max_steps, 'effective_max_steps': effective_budget}, 0)
    case_id = 'SYNTH-REMOTE-001'
    try:
        runtime.toolbox = ToolBox(scenario)
        case_id = runtime.toolbox.fixtures['case_id']
        graph = runtime.compile(pattern)
        for snapshot in graph.stream(state, config={'recursion_limit': 64}, stream_mode='values'):
            state = deepcopy(snapshot)
        if runtime.stopped:
            state.update(status='stopped', verified=False, report='')
            runtime.emit(actor, 'Stop', {'reason': 'Graph node budget exhausted', 'steps_used': runtime.steps_used}, state['plan_version'])
        elif state['status'] == 'running':
            raise RuntimeError('Graph ended without a reviewed outcome')
    except Exception as error:
        state.update(status='failed', verified=False, report='')
        runtime.emit(actor, 'Stop', {'reason': f'{type(error).__name__}: {error}'}, state['plan_version'])
    records = observed_records(state)
    coverage = sum(any(record['field'] == field for record in records.values()) for field in REQUIRED_FIELDS) / len(REQUIRED_FIELDS)
    shared = deepcopy(state)
    shared.update(case_id=case_id, synthetic=True, decision_source=decision_source,
                  required_evidence=list(REQUIRED_FIELDS), vehicle_actions_allowed=False,
                  steps_used=runtime.steps_used, max_steps=max_steps, effective_max_steps=effective_budget,
                  verification_scope='report_evidence_contract_only')
    return {'schema_version': 2, 'run_id': uuid.uuid4().hex, 'mode': mode, 'engine': 'langgraph',
            'pattern': pattern, 'scenario': scenario, 'status': state['status'], 'verified': state['verified'],
            'report': state['report'], 'events': deepcopy(runtime.events),
            'metrics': {'tool_calls': runtime.tool_calls, 'revision_rounds': state['revision_rounds'],
                        'elapsed_ms': round((time.perf_counter() - started) * 1000, 3), 'evidence_coverage': coverage},
            'shared_state': shared, 'human_review': {'status': 'pending', 'required': True,
                'report_ready': state['status'] == 'completed', 'vehicle_actions_allowed': False,
                'reason': '报告仅供人工复核，不确认故障原因，也不授权任何车辆操作。'}}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pattern', choices=PATTERNS, default='integrated')
    parser.add_argument('--scenario', choices=SCENARIOS, default='normal')
    parser.add_argument('--max-steps', type=int, default=30)
    parser.add_argument('--mode', choices=['simulation'], default='simulation')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    arguments = parser.parse_args()
    try:
        trace = run(arguments.pattern, arguments.scenario, arguments.max_steps, arguments.mode)
    except ValueError as error:
        parser.error(str(error))
    arguments.output.mkdir(parents=True, exist_ok=True)
    trace_path = arguments.output / f"{trace['run_id']}-trace.json"
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
    if trace['status'] == 'completed' and trace['verified']:
        (arguments.output / f"{trace['run_id']}-report.md").write_text(trace['report'], encoding='utf-8')
    print(json.dumps({'status': trace['status'], 'verified': trace['verified'], 'trace': str(trace_path)}, ensure_ascii=False))
    return 0 if trace['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
