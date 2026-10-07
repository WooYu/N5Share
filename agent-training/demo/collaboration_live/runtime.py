"""Run compiled graphs, stream actual events, and save reproducible evidence."""
import argparse
from copy import deepcopy
from datetime import datetime
import importlib
import json
from pathlib import Path
import sys
import threading
import time
from uuid import uuid4
from langgraph.errors import GraphRecursionError
from model_gateway import create_model, ModelError, ModelCancelled, ModelUnavailable
from .agents import action_schema, validate_action
from .state import initial_state
from .tools import calculate_costs
from .console import ConsolePresenter, name, STATUS

PATTERNS = ('sequential', 'supervisor', 'hierarchical', 'swarm', 'network')


class RunLimit(Exception):
    pass


class Session:
    def __init__(self, model, scenario, max_model_calls, max_seconds, on_event):
        self.model, self.scenario = model, scenario
        self.max_model_calls, self.calls = max_model_calls, 0
        self.deadline = time.monotonic() + max_seconds
        self.events, self.on_event, self.cancel = [], on_event, threading.Event()
        self.latest_state = None
        self.usage = {'input_tokens': 0, 'output_tokens': 0}

    def emit(self, kind, actor, target, message, state=None, **extra):
        event = dict(index=len(self.events) + 1, kind=kind, actor=actor, target=target,
                     message=message, **extra)
        if state is not None:
            event['state'] = deepcopy(state)
            self.latest_state = deepcopy(state)
        self.events.append(event)
        if self.on_event:
            self.on_event(deepcopy(event))

    def ask(self, instruction, role, state, choices, tools, observations, validator=None):
        context = dict(role=role, state=deepcopy(state), allowed_next=choices,
                       available_tools=tools, observations=observations,
                       task='两大一小出游，预算包括两张成人票、一张儿童票、交通与三人餐费。')
        context['control'] = ('你是当前决策者；allowed_next 是你可调度的对象，available_tools 只是你自己的工具。'
                              'state.last_actor/last_summary 属于上一角色，不是你的身份、工具或本轮完成标志。')
        instruction += ('只返回schema中的字段。tool非空时先请求工具，不得伪造观察；'
                        '本角色完成时tool为空，next从allowed_next选择；没有下一角色时next为空。'
                        'summary是简短决策摘要，不输出内部思维过程。已知缺项不能按0元。')
        schema = action_schema(choices, tools)
        retries = 0
        while True:
            remaining = self.deadline - time.monotonic()
            if self.calls >= self.max_model_calls or remaining <= 0:
                raise RunLimit('达到模型调用或运行时长上限')
            self.calls += 1
            self.model.timeout = min(45, remaining)
            self.emit('model_request', role, role, '调用真实模型', provider=self.model.metadata)
            try:
                answer, usage = self.model.generate_json(instruction, context, self.cancel, schema)
                if time.monotonic() >= self.deadline:
                    raise RunLimit('运行时长已耗尽')
            except ModelUnavailable as error:
                if not hasattr(self.model, 'activate_fallback') or not self.model.activate_fallback():
                    raise
                self.emit('model_switch', role, role, str(error) + '；后续使用备用模型', provider=self.model.metadata)
                continue
            for key in self.usage:
                self.usage[key] += usage.get(key, 0)
            try:
                answer = validate_action(answer, choices, tools)
                if validator:
                    validator(answer)
                break
            except ModelError as error:
                self.emit('model_rejected', role, role, str(error))
                if retries >= 2:
                    raise
                retries += 1
                context['correction'] = str(error) + '。请根据当前允许对象和实际状态重新返回；未执行被拒绝的行动。'
        self.emit('model_response', role, role, answer['summary'], action=answer, provider=self.model.metadata)
        return answer


def run_demo(pattern='supervisor', scenario='normal', model=None, weather='rain', budget=300,
             max_model_calls=32, max_steps=40, max_seconds=360, on_event=None):
    if pattern not in PATTERNS or scenario not in ('normal', 'missing'):
        raise ValueError('未知模式或情景')
    if weather not in ('rain', 'sun') or type(budget) is not int or budget < 0:
        raise ValueError('天气或预算无效')
    if any(type(value) is not int or value < 1 for value in (max_model_calls, max_steps, max_seconds)):
        raise ValueError('运行上限必须为正整数')
    state = initial_state(weather, budget)
    session = Session(model or create_model(), scenario, max_model_calls, max_seconds, on_event)
    status, error = 'running', None
    graph = importlib.import_module('.' + pattern, __package__).build_graph(session)
    try:
        if getattr(session.model, 'startup_fallback_reason', None):
            session.emit('model_switch', 'Runtime', 'Runtime', session.model.startup_fallback_reason, provider=session.model.metadata)
        # subgraphs=True exposes real nested team namespaces in hierarchical mode.
        for namespace, updates in graph.stream(state, stream_mode='updates', subgraphs=True,
                                                config={'recursion_limit': max_steps}):
            for node, patch in updates.items():
                if not isinstance(patch, dict):
                    continue
                state.update(deepcopy(patch))
                session.emit('graph_update', node, node, 'LangGraph 节点返回状态更新',
                             state=state, namespace=list(namespace), changed=list(patch))
        status = 'completed' if state['approved'] and state['proposal']['venue'] else 'no_solution' if state['approved'] else 'needs_input'
    except (RunLimit, GraphRecursionError) as problem:
        status, error = 'stopped', str(problem) if isinstance(problem, RunLimit) else '达到图步骤上限'
    except ModelCancelled:
        status, error = 'cancelled', '运行已取消'
    except ModelError as problem:
        status, error = 'failed', str(problem)
    except KeyboardInterrupt:
        session.cancel.set()
        status, error = 'cancelled', '讲师中断了运行'
    if session.latest_state is not None:
        state = deepcopy(session.latest_state)
    session.emit('finish', 'Runtime', 'END', error or status, state=state)
    return dict(pattern=pattern, scenario=scenario, execution='langgraph_live_model',
                status=status, error=error, state=deepcopy(state), events=session.events,
                model_calls=session.calls, tokens=session.usage, model=session.model.metadata)


def render_report(trace):
    """Deliver checked fields; preserve unverified model prose in the trace."""
    report = '# ' + name(trace['pattern']) + '\n\n状态：' + STATUS.get(trace['status'], trace['status']) + '\n\n'
    state = trace['state']
    if not state['approved']:
        return report + (trace['error'] or '没有通过验收，需补充资料或修订方案。') + '\n'
    proposal = state['proposal']
    if proposal['venue']:
        row = next(row for row in calculate_costs(state)['analysis'] if row['venue'] == proposal['venue'])
        report += (f"已验收建议：{row['venue']}；合计 {row['total']} 元，预算 {state['budget']} 元。\n\n"
                   f"两大一小门票 {row['tickets']} 元 + 交通 {row['transport']} 元 + 三人餐费 {row['meal']} 元。\n\n"
                   f"天气：{state['weather']}；场馆：{'室内' if row['indoor'] else '室外'}。"
                   f"资料引用：{row['ref']}、{state['evidence']['meal_ref']}。\n")
    else:
        report += '已验收结论：当前资料中没有满足天气和完整预算要求的候选。\n'
    return report + '\n模型原始建议保存在 trace.json；此报告根据已验收结构化字段与工具证据生成。\n'


def main(default_pattern=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pattern', choices=[*PATTERNS, 'all'], default=default_pattern or 'supervisor')
    parser.add_argument('--scenario', choices=['normal', 'missing'], default='normal')
    parser.add_argument('--weather', choices=['rain', 'sun'], default='rain')
    parser.add_argument('--budget', type=int, default=300)
    parser.add_argument('--max-model-calls', type=int, default=32)
    parser.add_argument('--max-steps', type=int, default=40)
    parser.add_argument('--max-seconds', type=int, default=360)
    parser.add_argument('--step', action='store_true', help='每个图节点完成后按 Enter 继续')
    parser.add_argument('--show-state', action='store_true')
    parser.add_argument('--check-model', action='store_true', help='只检查配置，不调用模型')
    parser.add_argument('--output', type=Path, default=Path('demo/output/collaboration-live'))
    args = parser.parse_args()
    if args.step and not sys.stdin.isatty():
        parser.error('--step 需要 VS Code 集成终端')
    if min(args.budget, args.max_model_calls, args.max_steps, args.max_seconds) < 0 or min(args.max_model_calls, args.max_steps, args.max_seconds) == 0:
        parser.error('预算须非负，运行上限须为正整数')
    try:
        model = create_model()
    except ModelError as error:
        print('配置不可用：' + str(error))
        return 1
    if args.check_model:
        print('实际模型配置：' + json.dumps(model.metadata, ensure_ascii=False))
        return 0
    output = args.output / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:6])
    output.mkdir(parents=True, exist_ok=False)
    exit_code = 0
    for pattern in PATTERNS if args.pattern == 'all' else [args.pattern]:
        scenario_label = '完整资料' if args.scenario == 'normal' else '首次缺少餐费资料'
        print(f'\n=== {name(pattern)} · {scenario_label} ===', flush=True)
        show = ConsolePresenter(show_state=args.show_state, step=args.step)
        run_model = model if pattern == (PATTERNS[0] if args.pattern == 'all' else args.pattern) else create_model()
        show.show_model(run_model.metadata)
        # Each comparison run independently starts with DeepSeek as its primary.
        trace = run_demo(pattern, args.scenario, model=run_model, weather=args.weather,
                         budget=args.budget, max_model_calls=args.max_model_calls,
                         max_steps=args.max_steps, max_seconds=args.max_seconds, on_event=show)
        (output / f'{pattern}-trace.json').write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
        report = render_report(trace)
        (output / f'{pattern}-report.md').write_text(report, encoding='utf-8')
        print(report, flush=True)
        print(f"\n结果：{STATUS.get(trace['status'], trace['status'])}；实际模型请求 {trace['model_calls']} 次\n输出目录：{output.resolve()}", flush=True)
        if trace['status'] in ('failed', 'stopped', 'cancelled'):
            exit_code = 2
    return exit_code
