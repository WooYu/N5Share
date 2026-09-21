"""Seven real-model teaching stages with read-only tools and inspectable state."""
import copy
import json
import threading
import time
import uuid

from model_gateway import create_model, ModelCancelled, ModelError, ModelUnavailable, check_step


PLACES = {
    'P01': {'name': '湖畔公园', 'indoor': False, 'ticket': 60, 'transport': 40, 'meal': 80},
    'P02': {'name': '自然馆', 'indoor': True, 'ticket': 150, 'transport': 60, 'meal': 100},
    'P03': {'name': '城市博物馆', 'indoor': True, 'ticket': 90, 'transport': 40, 'meal': 80},
}
DOCUMENTS = [
    {'id': 'D01', 'text': '雨天排除户外场馆。', 'keywords': ['出游', '天气', '雨天']},
    {'id': 'D02', 'text': '两大一小的预算必须包含门票、交通和餐费。', 'keywords': ['出游', '费用', '预算']},
    {'id': 'D03', 'text': '长途住宿行程需另核对酒店入住时间。', 'keywords': ['住宿', '酒店']},
]


def validate_payload(payload):
    if not isinstance(payload, dict) or 'stage' not in payload or set(payload) - {'stage', 'weather', 'budget', 'pattern'}:
        raise ValueError('仅接受 stage、weather、budget、pattern。')
    result = {'weather': 'rain', 'budget': 300, 'pattern': 'supervisor', **payload}
    if type(result['stage']) is not int or result['stage'] not in range(1, 8):
        raise ValueError('stage 必须为 1–7 的整数。')
    if result['weather'] not in ['rain', 'sun'] or type(result['budget']) is not int or result['budget'] not in [100, 200, 300]:
        raise ValueError('请选择晴天或雨天，以及 100、200、300 元预算。')
    if result['pattern'] not in ['supervisor', 'hierarchical', 'swarm']:
        raise ValueError('不支持的协作模式。')
    return result


class OutingTools:
    def __init__(self, weather, budget):
        self.weather, self.budget = weather, budget
        self.observations = {}

    def execute(self, name, place_id):
        if name == 'read_weather' and place_id == '':
            value = {'id': 'WX01', 'weather': self.weather, 'synthetic': True}
            self.observations['WX01'] = value
        elif name == 'read_catalog' and place_id == '':
            value = {'id': 'CAT01', 'places': [{'id': key, **data} for key, data in PLACES.items()], 'synthetic': True}
            self.observations['CAT01'] = value
        elif name == 'calculate_cost' and place_id in PLACES:
            place = PLACES[place_id]
            value = {'id': 'COST:' + place_id, 'place_id': place_id,
                     'ticket': place['ticket'], 'transport': place['transport'], 'meal': place['meal'],
                     'total': place['ticket'] + place['transport'] + place['meal'], 'synthetic': True}
            self.observations[value['id']] = value
        else:
            raise ValueError('工具或参数不在允许范围内。')
        return copy.deepcopy(value)


def validate_result(result, tools):
    if not result or result.get('status') not in ['recommended', 'no_solution']:
        return ['尚未提交明确结果。']
    issues = []
    observed = tools.observations
    if 'WX01' not in observed or 'CAT01' not in observed:
        issues.append('缺少实际读取的天气或场馆证据。')
    citations = result.get('citations', [])
    known = {'WX01', 'CAT01', 'D01', 'D02'} | set(PLACES) | {'COST:' + key for key in PLACES}
    if not isinstance(citations, list) or any(x not in known for x in citations):
        issues.append('引用了未知证据。')
        citations = []
    if not {'WX01', 'D01', 'D02'} <= set(citations):
        issues.append('缺少天气与完整费用规则引用。')
    suitable = [key for key, place in PLACES.items() if tools.weather == 'sun' or place['indoor']]
    if result['status'] == 'recommended':
        key = result.get('place_id')
        if key not in PLACES:
            return issues + ['场馆不存在。']
        actual = sum(PLACES[key][x] for x in ['ticket', 'transport', 'meal'])
        if key not in suitable:
            issues.append('天气不适配。')
        if type(result.get('total')) is not int or result['total'] != actual:
            issues.append('完整费用不正确。')
        if actual > tools.budget:
            issues.append('超过预算。')
        if 'COST:' + key not in observed:
            issues.append('没有实际执行所选场馆的成本工具。')
        if key not in citations:
            issues.append('缺少所选场馆引用。')
    else:
        if any('COST:' + key not in observed for key in suitable):
            issues.append('尚未核算所有天气适配候选，不能断言无解。')
        if any(sum(PLACES[key][x] for x in ['ticket', 'transport', 'meal']) <= tools.budget for key in suitable):
            issues.append('仍有可行候选，不能宣称无解。')
        if not set(suitable) <= set(citations):
            issues.append('无解结论缺少候选来源。')
    return issues


class StopRun(Exception):
    pass


class OutingRun:
    def __init__(self, payload, model, emit, cancel, max_calls, max_seconds):
        self.payload = validate_payload(payload)
        self.model, self.publish, self.cancel = model, emit, cancel
        self.limit, self.deadline = max_calls, time.monotonic() + max_seconds
        self.started = time.monotonic()
        self.tools = OutingTools(self.payload['weather'], self.payload['budget'])
        self.trace = {'id': str(uuid.uuid4()), 'mode': 'live', 'status': 'running', 'verified': False,
                      'config': self.payload, 'model': model.metadata, 'events': [], 'result': None,
                      'metrics': {'model_calls': 0, 'tool_calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'elapsed_ms': 0},
                      'shared_state': {'plan_version': 1, 'plan': [], 'observations': {}, 'messages': [], 'reflection': '', 'draft': None}}
        self.task = f'两名成人一名儿童，周六半日出游，预算{self.payload["budget"]}元，不订票不付款。'

    def event(self, phase, title, detail, actor='agent', data=None):
        self.trace['events'].append({'phase': phase, 'title': title, 'detail': detail,
                                     'actor': actor, 'data': data, 'index': len(self.trace['events'])})
        self.trace['shared_state']['observations'] = copy.deepcopy(self.tools.observations)
        self.trace['metrics']['elapsed_ms'] = round((time.monotonic() - self.started) * 1000)
        if self.publish:
            self.publish(copy.deepcopy(self.trace))

    def check(self):
        if self.cancel.is_set():
            raise ModelCancelled('讲师停止了本次运行。')
        if time.monotonic() >= self.deadline:
            raise StopRun('已到本次运行时长上限。')

    def ask(self, instruction, context, actor='agent'):
        while True:
            self.check()
            if self.trace['metrics']['model_calls'] >= self.limit:
                raise StopRun('已到模型调用次数上限，保留已有证据。')
            self.trace['metrics']['model_calls'] += 1
            self.trace['model'] = self.model.metadata
            self.event('模型请求', f'{actor} 正在调用真实模型', '等待结构化返回；此步骤会使用模型额度。', actor, self.model.metadata)
            if hasattr(self.model, 'timeout'):
                self.model.timeout = min(90, max(1, self.deadline - time.monotonic()))
            try:
                answer, usage = self.model.generate(instruction, copy.deepcopy(context), self.cancel)
                break
            except ModelUnavailable as error:
                self.check()
                if not hasattr(self.model, 'activate_fallback') or not self.model.activate_fallback():
                    raise
                self.trace['model'] = self.model.metadata
                self.event('模型切换', '已切换 DeepSeek 备用模型', str(error) + ' 已保留当前计划和工具证据，后续使用备用模型。', 'host', self.model.metadata)
        self.check()
        answer = check_step(answer)
        for key in ['input_tokens', 'output_tokens']:
            self.trace['metrics'][key] += usage.get(key, 0)
        self.event('Thought / 决策摘要', f'{actor} 的模型返回', answer['summary'], actor, answer)
        return answer

    def context(self):
        return {'task': self.task, 'rules': DOCUMENTS[:2],
                'plan_version': self.trace['shared_state']['plan_version'],
                'plan': self.trace['shared_state']['plan'],
                'reflection': self.trace['shared_state']['reflection'],
                'observations': self.tools.observations,
                'allowed_tools': ['read_weather()', 'read_catalog()', 'calculate_cost(place_id=P01/P02/P03)']}

    def execute(self, calls, actor='agent', allowed=None):
        outputs = []
        for call in calls:
            self.check()
            if self.trace['metrics']['tool_calls'] >= 20:
                raise StopRun('已到工具调用上限。')
            if allowed is not None and call['name'] not in allowed:
                raise ModelError(f'{actor} 请求了不属于该角色的工具。')
            self.event('Action / 工具请求', call['name'], json.dumps(call, ensure_ascii=False), actor, call)
            try:
                value = self.tools.execute(call['name'], call['place_id'])
            except ValueError as error:
                raise ModelError(str(error)) from None
            self.trace['metrics']['tool_calls'] += 1
            outputs.append(value)
            self.event('Observation / 实际工具结果', value['id'], json.dumps(value, ensure_ascii=False), actor, value)
        return outputs

    def accept(self, answer):
        result = answer.get('result')
        issues = validate_result(result, self.tools)
        self.trace['shared_state']['draft'] = result
        self.event('程序验收', '通过' if not issues else '需要修正', '天气、完整费用、预算和证据引用均通过。' if not issues else '；'.join(issues), 'validator', issues)
        if not issues:
            self.trace.update(result=result, verified=True, status='completed')
            self.event('Result / 最终结果', '建议待用户确认' if result['status'] == 'recommended' else '现有候选无可行方案', result['text'], 'host', result)
            return True
        return False

    def loop(self, single_batch=False):
        feedback = []
        while True:
            context = self.context()
            context['validation_feedback'] = feedback
            instruction = ('只根据实际 observations 决定下一步。缺证据时在 calls 中提出工具请求，result=null。'
                           '有足够证据后返回 result：recommended 或 no_solution。费用必须三项齐全，必须实际调用 calculate_cost。'
                           '最终 citations 必须包含 WX01、D01、D02 和相关场馆 Pxx；无解必须核算并引用所有天气适配候选。'
                           '已经读到的相同资料不要重复读。最多一次请求5个工具。')
            if single_batch and not self.tools.observations:
                instruction += '本页是一次批量工具调用：本轮一次提出天气、目录、P01/P02/P03成本共5个请求，然后依据返回回答。'
            answer = self.ask(instruction, context)
            if answer['calls']:
                if single_batch and self.tools.observations:
                    raise StopRun('工具调用页只展示一批调用；继续根据观察行动请使用 ReAct 页。')
                self.execute(answer['calls'])
            elif self.accept(answer):
                return
            else:
                feedback = validate_result(answer.get('result'), self.tools)

    def plan(self, reflection=False):
        context = self.context()
        if reflection:
            draft = {'status': 'recommended', 'place_id': 'P01', 'total': 100, 'citations': [], 'text': '公园费用100元'}
            self.event('教学注入', '故意提供错误执行草稿', '漏算餐费且未核对天气；此错误由讲师样本注入，并非宣称模型刚刚犯错。', 'teacher', draft)
            context.update(failed_draft=draft, feedback=validate_result(draft, self.tools))
            instruction = '根据失败草稿和验收反馈，输出可执行的 reflection 与修订后的 plan。不要调用工具，不要给最终结果。计划至少2步，保留有效证据。'
        else:
            instruction = '先规划再执行：输出至少2步的 plan，写明依赖与验收条件。现在不要调用工具或给结论，calls=[]，result=null。'
        answer = self.ask(instruction, context, 'planner')
        if len(answer['plan']) < 2 or answer['calls']:
            raise ModelError('规划阶段没有返回有效计划，或提前请求了工具。')
        if reflection:
            if not answer['reflection'].strip():
                raise ModelError('未返回针对失败的反思记录。')
            self.trace['shared_state']['reflection'] = answer['reflection']
            self.trace['shared_state']['plan_version'] = 2
            self.event('Reflexion / 反思', '将失败反馈用于下一次尝试', answer['reflection'], 'planner')
        self.trace['shared_state']['plan'] = answer['plan']
        self.event('Plan / 计划', f'计划 v{self.trace["shared_state"]["plan_version"]}', '\n'.join(answer['plan']), 'planner', answer['plan'])

    def worker(self, actor, sender):
        weather = actor == 'weather'
        allowed = ['read_weather', 'read_catalog'] if weather else ['read_catalog', 'calculate_cost']
        # Role-local context intentionally excludes the other specialist's messages.
        context = {'task': self.task, 'role': actor, 'rules': DOCUMENTS[:1] if weather else DOCUMENTS[1:2],
                   'allowed_tools': allowed, 'observations': []}
        instruction = ('你是天气角色，仅提出 read_weather 和 read_catalog 两项调用，place_id为空。不要读费用，不要给最终结论。' if weather else
                       '你是费用角色，仅提出 read_catalog 和 calculate_cost(P01)、calculate_cost(P02)、calculate_cost(P03) 共4个调用。不要查天气，不要给最终结论。')
        answer = self.ask(instruction, context, actor)
        outputs = self.execute(answer['calls'], actor, allowed)
        required = {'WX01', 'CAT01'} if weather else {'CAT01', 'COST:P01', 'COST:P02', 'COST:P03'}
        if not required <= {value['id'] for value in outputs}:
            raise ModelError('专业角色没有收集齐职责内所需证据。')
        # Weather role sees indoor/outdoor fields, not the cost specialist's data.
        if weather:
            outputs = [dict(value, places=[{'id': p['id'], 'name': p['name'], 'indoor': p['indoor']} for p in value['places']]) if 'places' in value else value for value in outputs]
        context['observations'] = outputs
        context['completed_roles'] = list(self.trace['shared_state'].get('role_results', {})) + [actor]
        instruction = ('根据本角色实际工具返回输出简洁 summary，附来源编号。calls=[]，result=null。'
                       '若协作模式是swarm，通过 next_actor 选择未完成的另一个专业角色；两角色都完成后选择summary。'
                       '不能交接给已完成角色。其他模式 next_actor=""。')
        context['pattern'] = self.payload['pattern']
        answer = self.ask(instruction, context, actor)
        if answer['calls']:
            raise ModelError('角色汇报阶段不接受新增工具请求。')
        message = {'task_id': self.trace['id'], 'from': actor, 'to': sender, 'type': 'result',
                   'plan_version': 1, 'summary': answer['summary'], 'evidence_refs': [x['id'] for x in outputs]}
        state = self.trace['shared_state']
        state.setdefault('role_results', {})[actor] = message
        state['messages'].append(message)
        self.event('Message / Agent 间通信', f'{actor} → {sender}', answer['summary'], actor, message)
        self.event('Shared State / 共享状态', '按角色合并证据，保留来源', '已完成角色：' + '、'.join(state['role_results']), 'host', copy.deepcopy(state))
        return answer['next_actor']

    def multi(self):
        pattern = self.payload['pattern']
        self.event('协作模式', pattern, '各角色独立调用同一模型，运行时隔离角色上下文并合并消息。', 'host')
        instruction = ('你是主管。输出至少2步的分工 plan，将天气和费用交给两个专业角色，最后汇总。'
                       'next_actor 选择 weather 或 cost 作为首先启动的角色；calls=[]，result=null。')
        answer = self.ask(instruction, {'task': self.task, 'pattern': pattern}, 'supervisor')
        actor = answer['next_actor']
        if actor not in ['weather', 'cost'] or answer['calls']:
            raise ModelError('主管没有返回有效的角色分派。')
        self.trace['shared_state']['plan'] = answer['plan']
        self.event('Delegation / 主管分派', '模型生成分工计划', '\n'.join(answer['plan']), 'supervisor')
        order = [actor, 'cost' if actor == 'weather' else 'weather']
        for position in range(2):
            if pattern != 'swarm':
                actor = order[position]
            sender = ('outing_lead' if actor == 'weather' else 'budget_lead') if pattern == 'hierarchical' else 'supervisor'
            if pattern == 'hierarchical':
                lead = self.ask('你是组长。根据分工选择唯一子角色：outing_lead交给weather，budget_lead交给cost。输出下一角色与简短任务说明，calls=[]，result=null。',
                                {'task': self.task, 'leader': sender, 'assigned_role': actor}, sender)
                if lead['next_actor'] != actor or lead['calls']:
                    raise ModelError('组长返回了不属于本组的分派。')
                self.event('层次化分派', f'supervisor → {sender} → {actor}', lead['summary'], sender)
            next_actor = self.worker(actor, sender if pattern != 'swarm' else 'handoff')
            if pattern == 'swarm':
                expected = order[1] if position == 0 else 'summary'
                if next_actor != expected:
                    raise ModelError('Swarm 交接重复、缺失或越过必要角色，运行已停止。')
                self.event('Handoff / 控制权交接', f'{actor} → {next_actor}', '交接任务、已完成角色和证据引用；下个角色保持独立上下文。', actor)
                actor = next_actor
        context = self.context()
        context['messages'] = self.trace['shared_state']['messages']
        if pattern == 'hierarchical':
            self.event('层次化汇总', '组长将子角色产物交回总主管', '天气组与预算组保留各自来源，统一进入总主管验收。', 'host')
        answer = self.ask('你是汇总角色。根据实际证据与两份角色消息生成最终 result。calls=[]。核对天气和完整费用；引用WX01、D01、D02及相关Pxx。无解时引用所有天气适配候选。不要新增资料。', context, 'summary')
        if answer['calls'] or not self.accept(answer):
            raise ModelError('汇总结果未通过程序验收，请查看已保留的反馈。')

    def run(self):
        try:
            self.check()
            stage = self.payload['stage']
            self.event('Goal / 目标', '真实模型，同一出游任务', self.task, 'host')
            if getattr(self.model, 'startup_fallback_reason', None):
                self.event('模型切换', '主模型不可用，使用 DeepSeek 备用', self.model.startup_fallback_reason, 'host', self.model.metadata)
            if stage in [1, 2]:
                context = {'task': self.task}
                if stage == 2:
                    query = '出游 预算 天气'
                    documents = [d for d in DOCUMENTS if any(term in query for term in d['keywords'])]
                    context['retrieved_documents'] = documents
                    self.event('Retrieval / 检索', '本地关键词检索命中资料', '\n'.join(f'{d["id"]}：{d["text"]}' for d in documents), 'retriever', documents)
                answer = self.ask('根据已提供的内容给出简短建议，放在summary。没有实际天气和报价时明确待核实，不能声称已调用工具。calls=[]，result=null。若有检索资料，引用D01、D02。', context)
                if answer['calls']:
                    raise ModelError('本阶段尚未开放工具。')
                self.trace.update(status='completed', result={'text': answer['summary'], 'status': 'unverified'})
                self.event('模型回答', '尚未做事实验收', answer['summary'], 'agent')
            elif stage == 7:
                self.multi()
            else:
                if stage in [5, 6]:
                    self.plan()
                if stage == 6:
                    self.plan(reflection=True)
                self.loop(single_batch=stage == 3)
        except ModelCancelled as error:
            self.trace['status'] = 'cancelled'
            self.event('Stop / 已停止', '本次运行已取消', str(error), 'host')
        except StopRun as error:
            self.trace['status'] = 'stopped'
            self.event('Stop / 达到上限', '受控停止', str(error), 'host')
        except Exception as error:
            self.trace['status'] = 'failed'
            message = str(error) if isinstance(error, ModelError) else '运行未完成，已保留现有轨迹；没有使用离线答案替代。'
            self.event('Error / 运行失败', '真实调用未完成', message, 'host')
        self.trace['metrics']['elapsed_ms'] = round((time.monotonic() - self.started) * 1000)
        return self.trace


def run_outing(payload, model=None, emit=None, cancel=None, max_calls=12, max_seconds=480):
    validate_payload(payload)
    return OutingRun(payload, model or create_model(), emit, cancel or threading.Event(), max_calls, max_seconds).run()


class RunManager:
    """One live run at a time; bounded in-memory history, no credential storage."""
    def __init__(self, model_factory=create_model):
        self.lock = threading.Lock()
        self.jobs = {}
        self.model_factory = model_factory

    def start(self, payload):
        payload = validate_payload(payload)
        with self.lock:
            if any(job['trace']['status'] in ['queued', 'running'] for job in self.jobs.values()):
                raise ValueError('已有真实模型任务正在运行，请先等待或停止。')
            model = self.model_factory()
            job_id = str(uuid.uuid4())
            cancel = threading.Event()
            trace = {'id': job_id, 'status': 'queued', 'mode': 'live', 'config': payload,
                     'model': model.metadata, 'events': [], 'verified': False, 'metrics': {}}
            while len(self.jobs) >= 8:
                del self.jobs[next(iter(self.jobs))]
            self.jobs[job_id] = {'cancel': cancel, 'trace': trace}

        def publish(value):
            value['id'] = job_id
            with self.lock:
                if job_id in self.jobs:
                    self.jobs[job_id]['trace'] = value

        def work():
            execution = OutingRun(payload, model, publish, cancel, 12, 480)
            execution.trace['id'] = job_id
            publish(execution.run())

        threading.Thread(target=work, daemon=True).start()
        return self.snapshot(job_id)

    def snapshot(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            return copy.deepcopy(job['trace']) if job else None

    def stop(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return False
            job['cancel'].set()
            return True
