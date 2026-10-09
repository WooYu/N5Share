"""Actual MetaGPT roles, subscriptions and Team environment; explicit host gates."""
import json
from pydantic import Field
from metagpt.actions.add_requirement import UserRequirement
from metagpt.config2 import Config
from metagpt.context import Context
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.team import Team
from .actions import ClarifyRequirement, DesignBoard, PrepareChange, ReviewCode, VerifyBoard, RepairCode
from .contracts import ContractError
from .tools import fingerprint, write_json


class FixRequested(UserRequirement):
    """Message cause used only after host tests and revision checks."""


class ArtifactRole(Role):
    """Use only freshly observed messages; previous revision history stays out of prompts."""
    session: object = Field(default=None, exclude=True)

    async def _act(self):
        todo = self.rc.todo
        current = self.rc.news
        await self.session.before_action(self.name, todo.name, [message.cause_by for message in current])
        result = await todo.run(current)
        self.session.remaining_time()
        message = Message(content=result, role=self.profile, cause_by=type(todo), sent_from=self.name)
        self.rc.memory.add(message)
        return message


def role(session, context, name, profile, action, watches):
    member = ArtifactRole(name=name, profile=profile, context=context, session=session)
    member.set_actions([action(session=session, context=context)])
    member._watch(watches)
    return member


def build_team(session):
    # All model requests happen inside custom Actions through our existing gateway.
    # MetaGPT's internal client is initialized but is never used by these single-Action roles.
    config = Config(llm={'api_type': 'openai', 'model': 'action-gateway',
                         'api_key': 'unused-by-custom-actions', 'base_url': 'http://127.0.0.1:1/v1'})
    context = Context(config=config)
    team = Team(context=context)
    members = [
        role(session, context, 'PM', '产品经理', ClarifyRequirement, [UserRequirement]),
        role(session, context, 'Architect', '架构师', DesignBoard, [ClarifyRequirement]),
        role(session, context, 'Developer', '开发者', PrepareChange, [DesignBoard]),
        role(session, context, 'Reviewer', '独立代码评审', ReviewCode, [PrepareChange, RepairCode]),
        role(session, context, 'Tester', '固定验收', VerifyBoard, [ReviewCode]),
        role(session, context, 'RepairDeveloper', '开发者修复行动', RepairCode, [FixRequested]),
    ]
    team.hire(members)
    return team


async def run_team(session):
    team = build_team(session)
    team.run_project(json.dumps(session.product, ensure_ascii=False) if session.product else '交付一个任务看板，演示代码评审与修复闭环')
    # Run the real MetaGPT environment round by round; budget/gates belong to the host.
    for _ in range(30):
        session.remaining_time()
        await team.env.run(k=1)
        status = session.state['status']
        if status == 'needs_fix':
            if session.state['repair_round'] >= session.state['max_repairs']:
                session.state['status'] = 'needs_human'
                session.emit('Host', 'stop', '修复轮次耗尽，转人工；保留所有评审与测试材料')
                return session.state
            feedback = {'revision': fingerprint(session.root), 'review': session.state['review'],
                        'tests': session.state['tests']}
            session.state['status'] = 'running'
            team.env.publish_message(Message(content=json.dumps(feedback, ensure_ascii=False),
                                              cause_by=FixRequested, sent_from='Host', send_to={'RepairDeveloper'}))
            session.emit('Host', 'fix_requested', '评审或验收退回，发送当前版本的结构化修复请求')
        elif status in ('waiting_approval', 'needs_context', 'stale'):
            session.emit('Host', 'gate', status + '：未自动批准或发布')
            return session.state
        write_json(session.root / 'state.json', session.state)
    raise ContractError('MetaGPT 环境轮次耗尽，未完成交付')
