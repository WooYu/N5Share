"""Native LangGraph node boundaries for comparing the course in Studio.

Only JSON teaching state enters checkpoints. Provider objects and credentials
are reconstructed privately inside worker threads, never saved in graph state.
"""
import asyncio
import copy
from pathlib import Path
import sys
import threading
import time
from typing import Literal
from typing_extensions import TypedDict

from pydantic import BaseModel, ConfigDict, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

DEMO_DIR = str(Path(__file__).resolve().parent)
if DEMO_DIR not in sys.path:
    sys.path.insert(0, DEMO_DIR)

from model_gateway import create_model, ModelError, ModelCancelled
from model_backup import DeepSeekModel, ModelRouter
from outing_live import OutingRun, StopRun, validate_result


class StudioInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    weather: Literal['rain', 'sun'] = Field(default='rain', description='合成天气：rain 下雨，sun 晴天')
    budget: Literal[100, 200, 300] = Field(default=300, description='两大一小的总预算，元')
    model_source: Literal['configured', 'deepseek'] = Field(default='configured', description='configured 与课件一致，CCSwitch 主模型加备用；deepseek 直接比较备用模型')
    max_model_calls: int = Field(default=12, ge=1, le=12, description='包含失败尝试的模型调用总上限')
    pause_before_summary: bool = Field(default=False, description='Supervisor 在汇总前暂停，检查状态后用 true 继续或 false 结束')


class StudioState(TypedDict, total=False):
    weather: str
    budget: int
    model_source: str
    max_model_calls: int
    pause_before_summary: bool
    trace: dict
    pending: dict
    feedback: list[str]
    next_role: str
    approval: bool


def build_graph(kind, model_factory=None, checkpointer=None):
    if kind not in ('react', 'supervisor'):
        raise ValueError('Unknown Studio graph')

    def runner_for(state, cancel, fresh=False):
        source = state.get('model_source', 'configured')
        old_trace = state.get('trace') if not fresh else None
        if model_factory:
            model = model_factory()
        elif source == 'deepseek':
            model = DeepSeekModel()
        elif old_trace and old_trace['model'].get('using_backup'):
            model = ModelRouter(DeepSeekModel(), startup_reason='继续本次已启用的 DeepSeek 备用。')
        else:
            model = create_model()
        runner = OutingRun({'stage': 4 if kind == 'react' else 7, 'weather': state.get('weather', 'rain'),
                            'budget': state.get('budget', 300), 'pattern': 'supervisor'},
                           model, None, cancel, min(12, max(1, state.get('max_model_calls', 12))), 480)
        if old_trace:
            runner.trace = copy.deepcopy(old_trace)
            runner.tools.observations = copy.deepcopy(old_trace['shared_state']['observations'])
            spent = old_trace['metrics']['elapsed_ms'] / 1000
            runner.started = time.monotonic() - spent
            runner.deadline = time.monotonic() + max(0, 480 - spent)
        return runner

    def node(action, fresh=False):
        async def execute(state: StudioState):
            cancelled = threading.Event()

            def work():
                runner = runner_for(state, cancelled, fresh=fresh)
                updates = {}
                try:
                    runner.check()
                    updates = action(runner, state) or {}
                except ModelCancelled as error:
                    runner.trace['status'] = 'cancelled'
                    runner.event('Stop', '运行已停止', str(error), 'host')
                except StopRun as error:
                    runner.trace['status'] = 'stopped'
                    runner.event('Stop', '达到运行上限', str(error), 'host')
                except ModelError as error:
                    runner.trace['status'] = 'failed'
                    runner.event('Error', '真实调用未完成', str(error), 'host')
                return {**updates, 'trace': runner.trace}

            task = asyncio.create_task(asyncio.to_thread(work))
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                cancelled.set()
                try:
                    await asyncio.shield(task)
                except Exception:
                    pass
                raise

        return execute

    def prepare(runner, state):
        runner.event('Goal', 'Studio 与课件使用同一个出游任务', runner.task, 'host')
        if getattr(runner.model, 'startup_fallback_reason', None):
            runner.event('模型切换', '使用已配置的备用模型', runner.model.startup_fallback_reason, 'host', runner.model.metadata)
        return {'pending': {}, 'feedback': [], 'next_role': '', 'approval': False}

    def decide(runner, state):
        context = runner.context()
        context['validation_feedback'] = state.get('feedback', [])
        answer = runner.ask('只根据实际observations决定下一步。缺证据时在calls中提出工具请求，result=null。'
                            '有足够证据后返回result，status为recommended或no_solution，calls=[]。'
                            '必须实际调用天气、目录及calculate_cost；总价包括门票、交通、餐费。'
                            '引用WX01、D01、D02及场馆Pxx；无解需要核算并引用所有天气适配候选。'
                            '不要重复读取已有证据。', context, 'react_agent')
        return {'pending': answer}

    def call_tools(runner, state):
        runner.execute(state['pending']['calls'], 'react_agent')

    def verify(runner, state):
        answer = state.get('pending', {})
        if kind == 'supervisor' and answer.get('calls'):
            raise ModelError('汇总节点不允许发起新的工具请求。')
        if not runner.accept(answer):
            if kind == 'supervisor':
                runner.trace['status'] = 'failed'
            return {'feedback': validate_result(answer.get('result'), runner.tools)}

    def supervisor(runner, state):
        answer = runner.ask('你是主管。输出至少2步的分工plan，将天气和费用交给两个专业角色，最后汇总。'
                            'next_actor选择weather或cost作为先启动角色；calls=[]，result=null。',
                            {'task': runner.task, 'pattern': 'supervisor'}, 'supervisor')
        if answer['next_actor'] not in ('weather', 'cost') or answer['calls']:
            raise ModelError('主管未返回有效分派。')
        runner.trace['shared_state']['plan'] = answer['plan']
        runner.event('Delegation', '主管分工计划', '\n'.join(answer['plan']), 'supervisor')
        return {'next_role': answer['next_actor']}

    def weather_agent(runner, state):
        runner.worker('weather', 'supervisor')

    def cost_agent(runner, state):
        runner.worker('cost', 'supervisor')

    def review_gate(state: StudioState):
        if not state.get('pause_before_summary', False):
            return {'approval': True}
        decision = interrupt({'提示': '天气与费用角色已经完成。检查 trace.shared_state，然后用 true 继续汇总，或 false 结束。',
                              'model_calls': state['trace']['metrics']['model_calls'],
                              'role_messages': state['trace']['shared_state']['messages']})
        approved = decision is True
        if not approved:
            trace = copy.deepcopy(state['trace'])
            trace['status'] = 'cancelled'
            return {'approval': False, 'trace': trace}
        return {'approval': True}

    def summarize(runner, state):
        context = runner.context()
        context['messages'] = runner.trace['shared_state']['messages']
        answer = runner.ask('你是汇总角色，根据两份角色消息与实际工具证据生成最终result。calls=[]。'
                            '核对天气、预算和完整费用。引用WX01、D01、D02与相关Pxx。'
                            '无解时必须引用所有天气适配候选。不得发明新资料。', context, 'summary')
        return {'pending': answer}

    def active(state):
        return state['trace']['status'] == 'running'

    graph = StateGraph(StudioState, input_schema=StudioInput)
    graph.add_node('prepare', node(prepare, fresh=True))
    graph.add_node('verify', node(verify))
    graph.add_edge(START, 'prepare')
    if kind == 'react':
        graph.add_node('decide', node(decide))
        graph.add_node('call_tools', node(call_tools))
        graph.add_conditional_edges('prepare', lambda s: 'decide' if active(s) else END, ['decide', END])
        graph.add_conditional_edges('decide', lambda s: END if not active(s) else 'call_tools' if s['pending']['calls'] else 'verify', ['call_tools', 'verify', END])
        graph.add_conditional_edges('call_tools', lambda s: 'decide' if active(s) else END, ['decide', END])
        graph.add_conditional_edges('verify', lambda s: 'decide' if active(s) else END, ['decide', END])
    else:
        graph.add_node('supervisor', node(supervisor))
        graph.add_node('weather_agent', node(weather_agent))
        graph.add_node('cost_agent', node(cost_agent))
        graph.add_node('review_gate', review_gate)
        graph.add_node('summarize', node(summarize))
        graph.add_conditional_edges('prepare', lambda s: 'supervisor' if active(s) else END, ['supervisor', END])
        graph.add_conditional_edges('supervisor', lambda s: s['next_role'] + '_agent' if active(s) else END, ['weather_agent', 'cost_agent', END])

        def after_role(state):
            if not active(state):
                return END
            roles = state['trace']['shared_state'].get('role_results', {})
            if 'weather' not in roles:
                return 'weather_agent'
            if 'cost' not in roles:
                return 'cost_agent'
            return 'review_gate'

        for role in ('weather_agent', 'cost_agent'):
            graph.add_conditional_edges(role, after_role, ['weather_agent', 'cost_agent', 'review_gate', END])
        graph.add_conditional_edges('review_gate', lambda s: 'summarize' if s.get('approval') else END, ['summarize', END])
        graph.add_conditional_edges('summarize', lambda s: 'verify' if active(s) else END, ['verify', END])
        graph.add_edge('verify', END)
    return graph.compile(checkpointer=checkpointer, name='出游 ReAct' if kind == 'react' else '出游 Supervisor')


react = build_graph('react')
supervisor = build_graph('supervisor')
