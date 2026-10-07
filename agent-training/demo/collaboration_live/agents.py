"""Independent role prompts, structured model actions and actual tool execution."""
from copy import deepcopy
import json
from model_gateway import ModelError
from .tools import read_sources, calculate_costs, missing_fields, validate_proposal

ROLES = ('Researcher', 'Analyst', 'Writer', 'Critic')
TOOLS = {'Researcher': ['read_sources'], 'Analyst': ['calculate_costs'], 'Writer': [], 'Critic': []}
PROMPTS = {
    'Researcher': '你负责搜集资料。每次进入必须调用read_sources一次；收到观察后结束本角色，不得在同一次进入重复读取。缺项交给允许的检查角色，等待反馈后重新进入补充。',
    'Analyst': '你负责费用核算。每次进入先调用calculate_costs一次；读取实际工具结果，不得自己填补缺失费用。缺资料时选择允许的补充路径。',
    'Writer': '你负责写出游建议。仅在资料完整且analyzed=true时提交venue、total、text；否则不编造建议。雨天排除室外，从预算内选择最便宜的场馆。无可行候选时venue为空、total=0，text说明无解。',
    'Critic': '你独立审查资料和建议。资料齐全、已经核算且建议正确时才approved=true。缺资料补资料，缺核算找Analyst，缺建议找Writer。审查通过可选择END。',
    'Supervisor': '你是主管，只选择下一位成员或END。无资料或收到缺项反馈选Researcher；缺核算选Analyst；缺建议选Writer；有建议未通过选Critic；approved=true才结束。每个Worker返回后重新判断。',
    'CEO': '你是总负责人，只调度research_team、delivery_team，不直接调度成员。无资料或needs_research=true选research_team；有资料且needs_research=false选delivery_team，由交付团队检查缺项并向你升级，不连续派资料团队；approved=true才结束。团队有自己的工具与成员，不能因为你自身无工具而认为团队不能执行。',
    'ResearchLead': '你是资料团队负责人。以当前state.research_done字段判断本次团队任务：false时选择Researcher，true时选择END返回上级。重新进入团队会重置为false，之前research_rounds或last_summary不能替代本次任务。你的成员Researcher可实际调用read_sources，工具不在你自己身上。完成一次查询后返回上级，不在团队内部重复读取。',
    'DeliveryLead': '你是交付团队负责人。缺资料时选择ESCALATE逐级返回总负责人；缺核算选Analyst；缺建议选Writer；有建议未通过选Critic；approved=true时END返回上级。',
}


def action_schema(allowed_next, tools):
    properties = {
        'summary': {'type': 'string'}, 'tool': {'type': 'string', 'enum': ['', *tools]},
        'next': {'type': 'string', 'enum': ['', *allowed_next]}, 'venue': {'type': 'string'},
        'total': {'type': 'integer'}, 'text': {'type': 'string'}, 'approved': {'type': 'boolean'},
    }
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


def validate_action(answer, choices, tools):
    if not isinstance(answer, dict) or set(answer) != {'summary', 'tool', 'next', 'venue', 'total', 'text', 'approved'}:
        raise ModelError('模型行动字段不完整')
    if any(not isinstance(answer[key], str) or len(answer[key]) > 3000 for key in ('summary', 'tool', 'next', 'venue', 'text')):
        raise ModelError('模型行动文本格式无效')
    if type(answer['total']) is not int or answer['total'] < 0 or type(answer['approved']) is not bool:
        raise ModelError('模型费用或审查标记格式无效')
    if answer['tool'] not in ['', *tools] or answer['next'] not in ['', *choices]:
        raise ModelError('模型请求不允许的工具或下一角色')
    return answer


def decide(session, role, state, choices):
    """Manager decision really comes from the model; only its allowed set is code."""
    def check(answer):
        if answer['next'] not in choices:
            raise ModelError(role + '没有选择下一角色')
        if answer['next'] == 'END' and role in ('Supervisor', 'CEO', 'DeliveryLead') and not state['approved']:
            raise ModelError('模型尚未完成审查便请求结束')
        if answer['next'] == 'END' and role == 'ResearchLead' and not state['research_done']:
            raise ModelError('本次团队任务 research_done=false，尚未查询；成员 Researcher 有资料工具，需先完成本次查询')
    answer = session.ask(PROMPTS[role], role, state, choices, [], [], validator=check)
    return answer['next'], answer['summary']


def work(session, role, state, choices=()):
    """One role turn: ask → execute requested tool → observe → model return."""
    current, observations = deepcopy(state), []
    for turn in range(3):
        tools = TOOLS[role] if not observations else []
        def check(answer):
            if role in ('Researcher', 'Analyst') and not observations and not answer['tool']:
                raise ModelError(role + '本次进入必须先调用' + TOOLS[role][0] + '，即使先前已经执行过')
            if not answer['tool']:
                if choices and answer['next'] not in choices:
                    raise ModelError(role + '没有选择允许的下一角色')
                if answer['next'] == 'END' and not (role == 'Critic' and answer['approved'] and not validate_proposal(current)):
                    raise ModelError('未经有效建议审查不得结束；请根据缺资料、缺核算或缺建议选择允许的下一角色')
        instruction = PROMPTS[role] + ('本次进入尚未调用工具，必须先请求：' + ','.join(tools) if tools else '本轮工具已完成或无工具；请完成职责并选择允许的下一角色。')
        answer = session.ask(instruction, role, current, list(choices), tools, observations, validator=check)
        if answer['tool']:
            updates = read_sources(current, session.scenario) if answer['tool'] == 'read_sources' else calculate_costs(current)
            current.update(updates)
            observations.append({'tool': answer['tool'], 'result': deepcopy(updates)})
            session.emit('tool_result', role, role, json.dumps(updates, ensure_ascii=False), state=current)
            continue
        if role in ('Researcher', 'Analyst') and not observations:
            raise ModelError(role + '未执行职责所需的资料工具')
        if role == 'Writer':
            current.update(proposal=dict(venue=answer['venue'], total=answer['total'], text=answer['text'])
                           if current['analyzed'] and not missing_fields(current) else None, approved=False)
        if role == 'Critic':
            issues = validate_proposal(current)
            current.update(approved=answer['approved'] and not issues, issues=issues)
        if choices and answer['next'] not in choices:
            raise ModelError(role + '没有选择允许的下一角色')
        if answer['next'] == 'END' and not current['approved']:
            raise ModelError('未经审查不得结束协作')
        current.update(last_actor=role, last_summary=answer['summary'], next_role=answer['next'])
        patch = {key: value for key, value in current.items() if value != state.get(key)}
        session.emit('work', role, role, answer['summary'], state=current)
        return patch
    raise ModelError('本角色的工具调用轮次已耗尽')
