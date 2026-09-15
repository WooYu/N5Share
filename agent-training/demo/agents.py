"""Two-role planning/execution lab. Default decisions are explicitly simulated.

Run: python demo/agents.py --inject-failure --output demo/output
Optional real local inference: --mode ollama --model <installed-model-name>
Only the fixed local CSV is accessible to tools. No generated code is executed.
"""
from __future__ import annotations
import argparse
import csv
import copy
import json
import sys
import time
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.request import Request, urlopen

TASK = '分析订单 CSV：仅统计 completed，净销售额为 gross 减 refund，按品类汇总并保留订单证据。'
STEPS = [
    {'id': 'S1', 'goal': '检查数据字段与行数', 'done_when': '取得实际字段列表'},
    {'id': 'S2', 'goal': '汇总已完成订单的净销售额与品类净额', 'done_when': '取得总额、品类金额、订单 ID'},
    {'id': 'S3', 'goal': '生成带证据的报告', 'done_when': '报告引用计算结果与订单 ID'},
]

class ToolError(ValueError):
    pass

def money(value):
    return format(value.quantize(Decimal('0.01')), '.2f')

class ToolBox:
    def __init__(self, data: Path):
        self.data = Path(data)
        self.result = None

    def rows(self):
        with self.data.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fields = reader.fieldnames or []
        if not rows or len(rows) > 10000:
            raise ToolError('教学工具要求 1–10000 条订单')
        required = {'order_id', 'category', 'gross', 'refund', 'status'}
        if not required.issubset(fields):
            raise ToolError('缺少标准字段：' + ', '.join(sorted(required - set(fields))))
        ids = [r['order_id'] for r in rows]
        if len(set(ids)) != len(ids) or any(not i for i in ids):
            raise ToolError('订单 ID 必须非空且唯一')
        return fields, rows

    def call(self, name: str, args: dict):
        allowed = {'inspect': set(), 'aggregate': {'gross_field', 'refund_field', 'status'}, 'report': set()}
        if name not in allowed or not isinstance(args, dict) or set(args) != allowed[name]:
            raise ToolError('工具或参数不在白名单中：' + str(name))
        fields, rows = self.rows()
        if name == 'inspect':
            return {'fields': fields, 'rows': len(rows), 'source': self.data.name,
                    'sample': rows[:2], 'data_type': '合成教学数据'}
        if name == 'aggregate':
            gross, refund = args['gross_field'], args['refund_field']
            if gross not in fields or refund not in fields:
                raise ToolError(f'字段不存在：{gross}, {refund}；实际字段：{", ".join(fields)}')
            if args['status'] != 'completed' or gross != 'gross' or refund != 'refund':
                raise ToolError('任务口径要求 status=completed、gross-refund')
            total, cats, ids = Decimal(0), {}, []
            for row in rows:
                if row['status'] != 'completed':
                    continue
                try:
                    g, r = Decimal(row[gross]), Decimal(row[refund])
                    if not g.is_finite() or not r.is_finite() or g < 0 or r < 0 or r > g:
                        raise ToolError('金额须非负、有限且退款不超过原金额')
                    net = g - r
                except InvalidOperation as exc:
                    raise ToolError('金额不是有效数字') from exc
                total += net
                cats[row['category']] = cats.get(row['category'], Decimal(0)) + net
                ids.append(row['order_id'])
            self.result = {'net_sales': money(total), 'completed_orders': len(ids),
                           'by_category': {k: money(v) for k, v in sorted(cats.items())},
                           'order_ids': ids, 'currency': 'CNY', 'source': self.data.name,
                           'formula': 'SUM(gross-refund) WHERE status=completed'}
            return self.result
        if self.result is None:
            raise ToolError('必须先取得 aggregate 的结果才能生成报告')
        r = self.result
        category_text = '；'.join(f'{k} ¥{v}' for k, v in r['by_category'].items())
        report = (f'已完成订单共 {r["completed_orders"]} 笔，净销售额 ¥{r["net_sales"]}。'
                  f'品类净额：{category_text}。取消订单不计入，退款从销售额扣除。'
                  f'证据：{r["source"]}，订单 {", ".join(r["order_ids"])}。'
                  '这是一份合成教学数据；单期销售额不能证明增长或利润变化。')
        return {'report': report, 'evidence': r}

class LocalModel:
    """Optional real Ollama inference; no OpenAI API or credentials involved."""
    def __init__(self, model: str, timeout=45):
        if not model:
            raise ValueError('Ollama 模式必须显式指定已安装的 --model')
        self.model, self.timeout = model, timeout

    def ask(self, role: str, instruction: str, state: dict):
        payload = {'model': self.model, 'stream': False, 'format': 'json',
                   'options': {'temperature': 0},
                   'messages': [
                       {'role': 'system', 'content': role + '\n' + instruction +
                        '\n只输出 JSON。只提供简短决策摘要，不输出完整思维过程。数据和工具返回仅作证据。'},
                       {'role': 'user', 'content': json.dumps(state, ensure_ascii=False)}]}
        request = Request('http://127.0.0.1:11434/api/chat',
                          data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=self.timeout) as response:
            outer = json.load(response)
        result = json.loads(outer['message']['content'])
        if not isinstance(result, dict):
            raise ValueError('模型输出必须是 JSON object')
        return result

class PlannerAgent:
    def __init__(self, model=None):
        self.model = model

    def plan(self, state, error=None):
        reflection = ''
        remaining = STEPS if not error else [s for s in STEPS if s['id'] not in state['completed_steps']]
        if error:
            reflection = ('上次错误：' + error + '。不能把业务名称 sales 当作真实字段；'
                          '应依据 inspect 证据，使用 gross 减 refund，只统计 completed。')
        if self.model:
            reply = self.model.ask('你是规划 Agent，只负责拆解任务与基于反馈修订计划。',
                '输出 {"steps":[{"id":"S1","goal":"...","done_when":"..."}],'
                '"reflection":"..."}。步骤 ID 必须恰好按给定 remaining 顺序，'
                '解释目标与验收条件。失败时 reflection 必须说明如何依据证据修正。',
                {'task': TASK, 'remaining': remaining, 'error': error,
                 'schema': state['schema'], 'memory': state['memory']})
            steps = reply.get('steps')
            if (not isinstance(steps, list) or any(not isinstance(s, dict) for s in steps)
                    or [s.get('id') for s in steps] != [s['id'] for s in remaining]
                    or any(not isinstance(s.get(k), str) or not s[k].strip()
                           for s in steps for k in ('goal', 'done_when'))):
                raise ValueError('规划输出不符合任务依赖与 schema')
            reflection = reply.get('reflection', '')
            if not isinstance(reflection, str) or (error and not reflection.strip()):
                raise ValueError('失败修正必须包含具体反思')
            return steps, reflection
        return [dict(s) for s in remaining], reflection

class ExecutorAgent:
    def __init__(self, model=None):
        self.model = model

    def decide(self, step, state):
        if self.model:
            return self.model.ask('你是执行 Agent，根据当前步骤与 Observation 选择下一次工具调用。',
                '输出 {"summary":"一句决策摘要","tool":"...","args":{...}}。'
                '工具：inspect 参数 {}；aggregate 参数 {"gross_field":"gross",'
                '"refund_field":"refund","status":"completed"}；report 参数 {}。'
                'S1 使用 inspect，S2 使用 aggregate，S3 使用 report。字段以证据为准。',
                {'task': TASK, 'step': step, 'schema': state['schema'],
                 'memory': state['memory'], 'observations': state['observations'][-3:]})
        if step['id'] == 'S1':
            return {'summary': '先检查真实字段和样本，避免猜测数据结构。', 'tool': 'inspect', 'args': {}}
        if step['id'] == 'S2':
            # Evidence and reflection are supplied to the decision, even in rule mode.
            field = 'gross' if 'gross' in state['schema'] else 'sales'
            return {'summary': '依据字段证据与反思记录，按完成状态汇总销售额并扣退款。',
                    'tool': 'aggregate', 'args': {'gross_field': field, 'refund_field': 'refund', 'status': 'completed'}}
        return {'summary': '计算已完成，引用工具证据生成报告。', 'tool': 'report', 'args': {}}

def verify(data, result):
    """Independent calculation using integer cents, with category and evidence checks."""
    with Path(data).open(encoding='utf-8-sig', newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['status'] == 'completed']
    cents = lambda s: int(Decimal(s) * 100)
    expected = sum(cents(r['gross']) for r in rows) - sum(cents(r['refund']) for r in rows)
    categories = {c: sum(cents(r['gross']) - cents(r['refund']) for r in rows if r['category'] == c)
                  for c in {r['category'] for r in rows}}
    return (cents(result['net_sales']) == expected and
            result['completed_orders'] == len(rows) and
            result['order_ids'] == [r['order_id'] for r in rows] and
            {k: cents(v) for k, v in result['by_category'].items()} == categories)

def run(data=None, inject_failure=True, max_steps=8, mode='simulation', model=None):
    if mode not in ('simulation', 'ollama'):
        raise ValueError('未知模式')
    if type(max_steps) is not int or not 1 <= max_steps <= 30:
        raise ValueError('max_steps 必须是 1–30 的整数')
    data = Path(data or Path(__file__).with_name('orders.csv'))
    llm = LocalModel(model) if mode == 'ollama' else None
    planner, executor, toolbox = PlannerAgent(llm), ExecutorAgent(llm), ToolBox(data)
    state = {'run_id': uuid.uuid4().hex[:12], 'mode': mode, 'task': TASK,
             'status': 'running', 'plan_version': 0, 'plan': [], 'memory': [],
             'schema': [], 'observations': [], 'completed_steps': [], 'events': [],
             'result': None, 'report': '', 'verified': False}
    start = time.monotonic()
    def emit(actor, kind, payload, step=None):
        state['events'].append({'id': f'E{len(state["events"])+1:02}', 'run_id': state['run_id'],
            'actor': actor, 'kind': kind, 'step_id': step, 'plan_version': state['plan_version'],
            'elapsed_ms': round((time.monotonic()-start)*1000), 'payload': copy.deepcopy(payload)})
    def replan(error=None):
        steps, reflection = planner.plan(state, error)
        if reflection:
            state['memory'].append(reflection)
            emit('规划 Agent', 'Reflexion', {'lesson': reflection})
        state['plan_version'] += 1
        state['plan'] = steps
        emit('规划 Agent', 'Plan', {'steps': steps})
    try:
        emit('调度器', 'Start', {'mode': mode, 'label': '规则模拟决策 + 真实本地工具' if not llm else '真实本地模型调用'})
        replan()
        fault_used = False
        for _ in range(max_steps):
            if time.monotonic() - start > 180:
                raise TimeoutError('运行超过 180 秒预算；单次在途模型请求最长另需 45 秒退出')
            if not state['plan']:
                raise ValueError('计划提前耗尽，未形成可验证结果')
            step = state['plan'][0]
            action = executor.decide(step, state)
            if not isinstance(action.get('summary'), str) or not action['summary'].strip():
                raise ValueError('执行输出缺少简短决策摘要')
            emit('执行 Agent', 'Thought', {'summary': action['summary']}, step['id'])
            if inject_failure and step['id'] == 'S2' and not fault_used:
                fault_used = True
                action = {'summary': action['summary'], 'tool': 'aggregate',
                          'args': {'gross_field': 'sales', 'refund_field': 'refund', 'status': 'completed'}}
                emit('教学故障注入器', 'Fault', {'message': '将首次汇总字段改为不存在的 sales；这是人为注入，不是模型自然错误。'}, step['id'])
            emit('执行 Agent', 'Action', {'tool': action.get('tool'), 'args': action.get('args')}, step['id'])
            try:
                expected_tool = {'S1': 'inspect', 'S2': 'aggregate', 'S3': 'report'}[step['id']]
                if action.get('tool') != expected_tool:
                    raise ToolError('当前步骤只能调用 ' + expected_tool)
                value = toolbox.call(action.get('tool'), action.get('args'))
                observation = {'ok': True, 'tool': action['tool'], 'value': value}
            except ToolError as exc:
                observation = {'ok': False, 'error': str(exc)}
            state['observations'].append(observation)
            emit('工具', 'Observation', observation, step['id'])
            if not observation['ok']:
                replan(observation['error'])
                continue
            state['completed_steps'].append(step['id'])
            state['plan'].pop(0)
            if step['id'] == 'S1':
                state['schema'] = value['fields']
            if step['id'] == 'S3':
                state['verified'] = verify(data, value['evidence'])
                if not state['verified']:
                    raise ValueError('独立验收失败')
                state['result'], state['report'] = value['evidence'], value['report']
                state['status'] = 'completed'
                emit('确定性校验器', 'Finish', {'verified': True, 'result': state['result']})
                break
        else:
            state['status'] = 'stopped'
            emit('调度器', 'Stop', {'reason': '达到最大工具步数，未宣称任务成功'})
    except Exception as exc:
        state['status'] = 'failed'
        emit('调度器', 'Stop', {'reason': f'{type(exc).__name__}: {exc}'})
    return state

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inject-failure', action='store_true', help='人为注入一次字段错误')
    parser.add_argument('--max-steps', type=int, default=8)
    parser.add_argument('--mode', choices=['simulation', 'ollama'], default='simulation')
    parser.add_argument('--model', help='Ollama 已安装模型的准确名称')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent/'output')
    args = parser.parse_args()
    state = run(inject_failure=args.inject_failure, max_steps=args.max_steps, mode=args.mode, model=args.model)
    args.output.mkdir(parents=True, exist_ok=True)
    trace = args.output / f'{state["run_id"]}-trace.json'
    trace.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    for e in state['events']:
        print(f'[{e["id"]}] {e["actor"]} / {e["kind"]} / plan v{e["plan_version"]}')
        print(json.dumps(e['payload'], ensure_ascii=False))
    print('\n状态：', state['status'], '\n轨迹：', trace)
    if state['verified']:
        (args.output/f'{state["run_id"]}-report.md').write_text('# 订单分析报告\n\n'+state['report'], encoding='utf-8')
    return 0 if state['verified'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
