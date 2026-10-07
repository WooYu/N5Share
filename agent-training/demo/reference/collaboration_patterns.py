"""Slides 12–26: executable collaboration topologies, with rule-based workers.

No LLM, network or framework dependency. Each pattern executes its own control
flow against identical synthetic tools. Run this file directly in VS Code.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys
from uuid import uuid4

PATTERNS = ('supervisor', 'hierarchical', 'swarm', 'sequential', 'network')
LABELS = {
    'supervisor': 'Supervisor · 中心调度（16–17 页）',
    'hierarchical': 'Hierarchical · 多层团队（18–19 页）',
    'swarm': 'Swarm · 控制权交接（20–21 页）',
    'sequential': 'Sequential Chain · 固定流水线（14–15 页）',
    'network': 'Network · 对等路由（22–23 页）',
}
VENUES = [
    {'venue': '城市博物馆', 'indoor': True, 'adult': 50, 'child': 20,
     'transport': 30, 'ref': 'VENUE-001'},
    {'venue': '互动科学馆', 'indoor': True, 'adult': 80, 'child': 40,
     'transport': 30, 'ref': 'VENUE-002'},
    {'venue': '滨河公园', 'indoor': False, 'adult': 0, 'child': 0,
     'transport': 60, 'ref': 'VENUE-003'},
]
ROLES = ('Researcher', 'Analyst', 'Writer', 'Critic')
SWARM_LINKS = {
    'Researcher': {'Critic'},
    'Critic': {'Researcher', 'Analyst', 'Writer', 'END'},
    'Analyst': {'Writer'},
    'Writer': {'Critic'},
}


def missing_fields(state):
    return [key for key in ('candidates', 'meal', 'meal_ref')
            if key not in state['evidence']]


def cost_rows(state):
    """Actual synthetic tool values; do not interpret absent meal cost as zero."""
    if missing_fields(state):
        return []
    return [dict(venue=v['venue'], indoor=v['indoor'], ref=v['ref'],
                 tickets=2 * v['adult'] + v['child'], transport=v['transport'],
                 meal=state['evidence']['meal'],
                 total=2 * v['adult'] + v['child'] + v['transport']
                       + state['evidence']['meal'])
            for v in state['evidence']['candidates']]


def feasible_rows(state):
    return [row for row in cost_rows(state)
            if (state['weather'] == 'sun' or row['indoor'])
            and row['total'] <= state['budget']]


def worker(role, state, scenario):
    """Replace this function with model+tool calls for a live Agent experiment.

    The current policies are deterministic teaching rules, not model reasoning.
    Return a state patch plus the human-readable result of this turn.
    """
    if role == 'Researcher':
        rounds = state['research_rounds'] + 1
        evidence = {'candidates': deepcopy(VENUES)}
        if scenario == 'normal' or rounds > 1:
            evidence.update(meal=90, meal_ref='FOOD-001')
        return {'evidence': evidence, 'research_rounds': rounds,
                'analysis': [], 'analyzed': False, 'proposal': None,
                'approved': False, 'issues': []}, (
            '读取合成场馆及餐费资料；餐费为三人合计 90 元。' if 'meal' in evidence
            else '首次读取只有场馆资料，餐费字段缺失；不能将缺失视为免费。')
    if role == 'Analyst':
        missing = missing_fields(state)
        if missing:
            return {'analysis': [], 'analyzed': False,
                    'issues': missing, 'approved': False}, '无法核算：缺少 ' + ', '.join(missing)
        rows = cost_rows(state)
        return {'analysis': rows, 'analyzed': True, 'issues': [],
                'approved': False}, '核算两张成人票、一张儿童票、交通及餐费：' + '；'.join(
                    f"{r['venue']} {r['total']} 元" for r in rows)
    if role == 'Writer':
        if missing_fields(state) or not state['analyzed']:
            return {'proposal': None, 'approved': False}, '资料或核算尚未齐备，暂不生成可执行方案。'
        options = [row for row in state['analysis']
                   if (state['weather'] == 'sun' or row['indoor'])
                   and row['total'] <= state['budget']]
        selected = min(options, key=lambda row: row['total']) if options else None
        proposal = {
            'venue': selected['venue'] if selected else None,
            'total': selected['total'] if selected else None,
            'refs': [selected['ref'], state['evidence']['meal_ref']] if selected else [],
            'text': (f"建议去{selected['venue']}，三人总计 {selected['total']} 元，"
                     f"不超过 {state['budget']} 元预算。" if selected
                     else f"当前天气与 {state['budget']} 元预算下无可行方案；建议调整预算或需求。"),
        }
        return {'proposal': proposal, 'approved': False}, proposal['text']
    if role == 'Critic':
        missing = missing_fields(state)
        if missing:
            return {'issues': missing, 'approved': False}, '资料审查未通过：缺少 ' + ', '.join(missing)
        proposal = state['proposal']
        if proposal is None:
            return {'issues': [], 'approved': False}, '资料齐备；下一步需要核算并撰写方案。'
        # Independently recompute from evidence, rather than trusting the draft.
        options = feasible_rows(state)
        expected = min(options, key=lambda row: row['total']) if options else None
        valid = (proposal['venue'] == (expected['venue'] if expected else None)
                 and proposal['total'] == (expected['total'] if expected else None)
                 and proposal['refs'] == ([expected['ref'], state['evidence']['meal_ref']]
                                          if expected else []))
        return {'approved': valid, 'issues': [] if valid else ['proposal']}, (
            '审查通过：天气、票数、全部费用、预算与资料引用一致。' if valid
            else '审查退回：方案与原始费用、天气或引用不一致。')
    raise ValueError('Unknown worker: ' + role)


class StepLimit(Exception):
    pass


class Run:
    def __init__(self, pattern, scenario, weather, budget, max_steps, on_event):
        self.pattern, self.scenario = pattern, scenario
        self.max_steps, self.steps = max_steps, 0
        self.on_event = on_event
        self.state = dict(weather=weather, budget=budget, evidence={},
                          research_rounds=0, analysis=[], analyzed=False,
                          proposal=None, approved=False, issues=[])
        self.events = []

    def tick(self):
        # Limits apply before executing workers AND control decisions.
        if self.steps >= self.max_steps:
            raise StepLimit
        self.steps += 1

    def emit(self, actor, target, kind, reason, message='', changed=None):
        event = dict(index=len(self.events) + 1, step=self.steps, actor=actor,
                     target=target, kind=kind, reason=reason, message=message,
                     changed=changed or [], state=deepcopy(self.state))
        self.events.append(event)
        if self.on_event:
            self.on_event(deepcopy(event))

    def control(self, actor, target, kind, reason):
        self.tick()
        self.emit(actor, target, kind, reason)

    def work(self, role):
        self.tick()
        updates, message = worker(role, deepcopy(self.state), self.scenario)
        changed = [key for key, value in updates.items() if self.state.get(key) != value]
        self.state.update(updates)
        self.emit(role, role, 'work', '执行本角色职责', message, changed)

    def result_status(self):
        if not self.state['approved']:
            return 'needs_input'
        return 'completed' if self.state['proposal']['venue'] else 'no_solution'


def supervisor_choice(state):
    """The manager decides after every worker report, based on actual state."""
    if not state['evidence']:
        return 'Researcher', '没有候选资料，先分派搜集任务'
    if state['issues'] and missing_fields(state):
        return 'Researcher', '收到缺项反馈，重新分派补充资料'
    if not state['analyzed']:
        return 'Analyst', '已收到资料，分派费用核算'
    if state['proposal'] is None or 'proposal' in state['issues']:
        return 'Writer', '费用已核算，分派撰写或修订'
    return 'Critic', '方案已提交，分派独立审查'


def run_supervisor(run):
    while not run.state['approved']:
        role, reason = supervisor_choice(run.state)
        run.control('Supervisor', role, 'dispatch', reason)
        run.work(role)
        run.emit(role, 'Supervisor', 'report', 'Worker 返回主管，主管决定下一步')


def research_team(run):
    """A callable sub-team: its leader selects workers and reports upward."""
    run.control('ResearchLead', 'Researcher', 'dispatch', '资料团队负责人分派查询或补充')
    run.work('Researcher')
    run.emit('Researcher', 'ResearchLead', 'report', '成员只向本团队负责人汇报')
    run.emit('ResearchLead', 'CEO', 'report', '团队返回资料摘要',
             '字段：' + ', '.join(run.state['evidence']))


def delivery_team(run):
    while not run.state['approved']:
        if run.state['issues'] and missing_fields(run.state):
            run.emit('DeliveryLead', 'CEO', 'escalate', '本团队无法补数据，逐级请求资料团队协助',
                     '缺少：' + ', '.join(run.state['issues']))
            return
        role, reason = supervisor_choice(run.state)
        # Data gathering belongs to the sibling team, never a direct leaf call.
        if role == 'Researcher':
            raise ValueError('Delivery team cannot dispatch research workers')
        run.control('DeliveryLead', role, 'dispatch', reason)
        run.work(role)
        run.emit(role, 'DeliveryLead', 'report', '交付成员向本团队负责人汇报')
    run.emit('DeliveryLead', 'CEO', 'report', '交付团队完成核算、撰写与审查')


def run_hierarchical(run):
    while not run.state['approved']:
        run.control('CEO', 'ResearchLead', 'dispatch', '高层委派资料团队，不直接调度叶子成员')
        research_team(run)
        run.control('CEO', 'DeliveryLead', 'dispatch', '高层将资料摘要交给交付团队')
        delivery_team(run)


def swarm_choice(role, state):
    """Local handoff policy; each active peer has a restricted tool set."""
    if role == 'Researcher':
        return 'Critic', '搜集者交出控制权，请审查者检查资料'
    if role == 'Critic':
        if missing_fields(state):
            return 'Researcher', '审查者发现缺项，交回搜集者补充'
        if state['approved']:
            return 'END', '方案已通过审查，结束交接'
        if not state['analyzed']:
            return 'Analyst', '资料齐备，将控制权交给费用专家'
        return 'Writer', '需要方案或修订，将控制权交给撰写者'
    if role == 'Analyst':
        return 'Writer', '核算完成，将控制权交给撰写者'
    return 'Critic', '方案完成，将控制权交给审查者'


def network_choice(role, state):
    """Shared technical router, no manager role; any peer can reach any other.

    The decision uses current peer output and shared task state. It does not
    round-robin through roles. Here rules stand in for the slides' model router.
    """
    if state['approved']:
        return 'END', '有经过审查的结果，满足结束条件'
    if role == 'Researcher':
        return 'Analyst', '搜集者将本次资料交给费用专家检查与核算'
    if missing_fields(state):
        return 'Researcher', '当前角色直接路由到搜集者补齐资料'
    if not state['analyzed']:
        return 'Analyst', '需要核算，直接路由到费用专家'
    if state['proposal'] is None or state['issues']:
        return 'Writer', '需要方案或修订，直接路由到撰写者'
    return 'Critic', '当前方案需要审查，直接路由到审查者'


def run_peers(run, kind):
    active = 'Researcher' if kind == 'swarm' else 'Writer'
    policy = swarm_choice if kind == 'swarm' else network_choice
    run.emit('User', active, 'start', '指定初始活跃角色；同一时刻只有一个角色持有控制权')
    while True:
        run.work(active)
        target, reason = policy(active, run.state)
        allowed = SWARM_LINKS[active] if kind == 'swarm' else (set(ROLES) - {active}) | {'END'}
        if target not in allowed:
            raise ValueError(f'Invalid peer route: {active} -> {target}')
        run.control(active, target, 'handoff' if kind == 'swarm' else 'route', reason)
        if target == 'END':
            if not run.state['approved']:
                raise ValueError('Cannot finish without a reviewed result')
            return
        active = target


def run_sequential(run):
    # No back edges or dynamically selected next role, even on missing evidence.
    for index, role in enumerate(ROLES):
        previous = ROLES[index - 1] if index else 'START'
        run.emit(previous, role, 'fixed_edge', '预先定义的顺序边，传递上一步状态')
        run.work(role)


def run_demo(pattern='supervisor', scenario='normal', weather='rain', budget=300,
             max_steps=40, on_event=None):
    if pattern not in PATTERNS or scenario not in ('normal', 'missing'):
        raise ValueError('Invalid pattern or scenario')
    if weather not in ('rain', 'sun') or type(budget) is not int or budget < 0:
        raise ValueError('Invalid weather or budget')
    if type(max_steps) is not int or not 1 <= max_steps <= 100:
        raise ValueError('max_steps must be an integer from 1 to 100')
    run = Run(pattern, scenario, weather, budget, max_steps, on_event)
    try:
        if pattern == 'supervisor':
            run_supervisor(run)
        elif pattern == 'hierarchical':
            run_hierarchical(run)
        elif pattern == 'sequential':
            run_sequential(run)
        else:
            run_peers(run, pattern)
        status = run.result_status()
        reason = {'completed': '交付经过审查的出游建议',
                  'no_solution': '审查确认当前约束下无可行方案',
                  'needs_input': '流水线结束但资料不齐；保留缺项，等待补充后重新运行'}[status]
        run.emit(pattern, 'END', 'finish', reason)
    except StepLimit:
        status = 'step_limit'
        run.emit('Runtime', 'END', 'stop', '达到步骤上限，保留已有状态，不宣称成功')
    return dict(pattern=pattern, label=LABELS[pattern], scenario=scenario,
                execution='rule_simulation', status=status, steps=run.steps,
                max_steps=max_steps, state=deepcopy(run.state), events=run.events)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='第 12–26 页五种协作模式的离线可运行演示')
    parser.add_argument('--pattern', choices=(*PATTERNS, 'all'), default='all')
    parser.add_argument('--scenario', choices=('normal', 'missing'), default='normal')
    parser.add_argument('--weather', choices=('rain', 'sun'), default='rain')
    parser.add_argument('--budget', type=int, default=300)
    parser.add_argument('--max-steps', type=int, default=40)
    parser.add_argument('--step', action='store_true', help='每个角色执行后按 Enter 继续')
    parser.add_argument('--show-state', action='store_true', help='每次执行后打印完整共享状态')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output' / 'collaboration')
    args = parser.parse_args()
    if args.budget < 0 or not 1 <= args.max_steps <= 100:
        parser.error('budget 必须非负；max-steps 必须为 1–100')
    if args.step and not sys.stdin.isatty():
        parser.error('--step 需要交互式终端；请在 VS Code 集成终端运行')

    def display(event):
        print(f"  [{event['index']:02d} / 步骤 {event['step']:02d}] "
              f"{event['actor']} -> {event['target']} | {event['kind']}", flush=True)
        print('       原因：' + event['reason'], flush=True)
        if event['message']:
            print('       输出：' + event['message'], flush=True)
        if event['kind'] == 'work':
            state = event['state']
            print(f"       状态：资料轮次={state['research_rounds']}；"
                  f"缺项={','.join(missing_fields(state)) or '无'}；"
                  f"方案={(state['proposal'] or {}).get('venue') or '未选定'}；"
                  f"审查通过={state['approved']}；变更={','.join(event['changed']) or '无'}", flush=True)
            if args.show_state:
                print(json.dumps(state, ensure_ascii=False, indent=2), flush=True)
            if args.step:
                input('       按 Enter 继续…')

    traces = []
    patterns = PATTERNS if args.pattern == 'all' else (args.pattern,)
    print('规则模拟 · 合成资料 · 无模型调用\n任务：为两大一小安排出游，核对天气、票价、交通及餐费。', flush=True)
    for pattern in patterns:
        print(f"\n{'=' * 64}\n{LABELS[pattern]} | {args.scenario} | {args.weather} | {args.budget} 元", flush=True)
        trace = run_demo(pattern, args.scenario, args.weather, args.budget, args.max_steps, display)
        traces.append(trace)
        print(f"  结果：{trace['status']} | 控制决策及角色执行共 {trace['steps']} 步", flush=True)
        if trace['state']['approved'] and trace['status'] != 'step_limit':
            print('  ' + trace['state']['proposal']['text'], flush=True)

    # Unique run directories preserve prior classroom results.
    output = args.output.resolve() / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:6])
    output.mkdir(parents=True, exist_ok=False)
    for trace in traces:
        (output / f"{trace['pattern']}-trace.json").write_text(
            json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
    from collaboration_report import write_report
    write_report(traces, output)
    print('\n模式对比：', flush=True)
    for trace in traces:
        print(f"  {trace['pattern']:13s} {trace['status']:12s} "
              f"步骤={trace['steps']:2d}  资料查询={trace['state']['research_rounds']}", flush=True)
    print(f"\nHTML 对比报告：{output / 'comparison.html'}\nMarkdown 讲解：{output / 'comparison.md'}\nJSON 轨迹目录：{output}", flush=True)
    return 2 if any(t['status'] == 'step_limit' for t in traces) else 0


if __name__ == '__main__':
    raise SystemExit(main())
