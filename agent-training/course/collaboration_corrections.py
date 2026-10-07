"""Reviewed teaching corrections; keep the imported source snapshot intact."""
from html import escape
import re

from collaboration_visuals import graph


def listing(source):
    return ('<div class="code-block"><div class="code-header">'
            '<span class="code-lang">python</span>'
            '<button class="copy-btn" onclick="copyCode(this)">复制</button></div>'
            f'<pre><code>{escape(source)}</code></pre></div>')


AUTOGEN_SWARM = '''from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import Swarm
researcher = AssistantAgent("Researcher", model_client=model_client,
    tools=[search_tool], handoffs=["Critic"],
    system_message="研究任务，按需交给 Critic 检查。")
critic = AssistantAgent("Critic", model_client=model_client,
    handoffs=["Researcher", "Writer"],
    system_message="检查资料；缺项交回 Researcher，完整则交给 Writer。")
writer = AssistantAgent("Writer", model_client=model_client,
    handoffs=["Researcher"],
    system_message="写报告；缺资料交回 Researcher，完成时输出 TERMINATE。")
team = Swarm([researcher, critic, writer],
    termination_condition=TextMentionTermination("TERMINATE"), max_turns=6)'''


NETWORK_NODES = '''from typing import Literal
from pydantic import BaseModel
from langchain.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

class NextHop(BaseModel):
    next_agent: Literal["planner", "executor", "reviewer", "END"]

# agents 为已定义的三个 Agent；NetworkState 包含 messages
def peer_node(role, state):
    result = agents[role].invoke({"messages": state["messages"]})
    messages = result["messages"][len(state["messages"]):]
    decision = model.with_structured_output(NextHop).invoke([
        SystemMessage(content=f"你是 {role}，根据任务结果选择下一角色或 END。"),
        *state["messages"], *messages,
    ])
    target = END if decision.next_agent == "END" else decision.next_agent
    return Command(update={"messages": messages}, goto=target)

# 决策在各角色节点内部；没有独立的中央 Router 节点
graph = StateGraph(NetworkState)
for role in ("planner", "executor", "reviewer"):
    graph.add_node(role, lambda state, role=role: peer_node(role, state))
graph.add_edge(START, "planner")
network = graph.compile()
result = network.invoke(inputs, config={"recursion_limit": 12})'''


def correct_sections(sections):
    hierarchical = sections['sec04']['blocks']
    hierarchical[0] = hierarchical[0].replace('Supervisor的升级版——多层嵌套', 'Supervisor 的多层扩展，通过子团队分工')
    swarm = sections['sec05']['blocks']
    swarm[0] = ('<div class="voice-line">Swarm 的核心是当前活跃 Agent 按需交接控制权（Handoff），'
                '不要求经过中央主管。当前角色决定是否交接、交给谁，也可直接完成任务；'
                '允许的交接关系由工具或 handoffs 配置，不是固定轮询。</div>')
    swarm[6] = listing(AUTOGEN_SWARM)
    swarm[7] = ('<div class="highlight-box warn"><div class="hl-title">注意：三种机制不同</div>'
                '<code>Swarm</code>：当前 Agent 通过 handoffs 交接；'
                '<code>RoundRobinGroupChat</code>：固定顺序轮流发言；'
                '<code>SelectorGroupChat</code>：选择器决定下一位发言者，属于集中选择。</div>')
    sequential = sections['sec06']['blocks']
    sequential[-1] = ('<div class="highlight-box key"><div class="hl-title">关键</div>'
                      '用 <code>add_edge</code> 定义外层固定顺序；阶段内部仍可推理、调用工具和重试。'
                      '本例省略条件分支与回退。只有各阶段具有独立 Agent 职责时，才称为多 Agent 链；'
                      '普通函数或模型调用的串联属于顺序工作流。</div>')
    network = sections['sec07']['blocks']
    network[0] = ('<div class="voice-line">Network 用网络连接多个专业角色，各节点在任务结果基础上'
                  '按允许连接选择下一跳或结束，不要求由固定中央主管决策。'
                  '本例使用全连接；也可限制连接。Swarm 强调交接机制，Network 强调连接与路由结构，两者可重叠。</div>')
    svg, _ = graph('network', 'Network 三角色对等路由', network_roles=3)
    network[2] = ('<div class="network-routing-diagram">' + svg +
                  '<div><p><strong>A · Planner　B · Executor　C · Reviewer</strong></p>'
                  '<p>每个节点：执行任务 → 决定下一跳 / 结束</p>'
                  '<p>灰色：允许连接　青色：一次示例路径</p></div></div>')
    network[3] = '<p class="comparison-note">路由代码可以复用，决策权仍在当前角色；统一中央 LLM Router 属于集中式路由。</p>'
    network[5] = listing(NETWORK_NODES)
    network[6] = ('<div class="highlight-box tip"><div class="hl-title">生产建议</div>'
                  '结构化输出约束目标名称；限制允许连接、总步数和超时，并定义终止条件。'
                  '本例允许三个角色互相路由，硬性步数上限用于防止无限循环。</div>')
    # Edit the teaching copy here; the supplied HTML remains a source snapshot.
    prose = {
        'sec02': {
            '中央调度Agent分配任务，Sub-Agent执行后汇报。适合动态任务分发、客服分流。':
                '主管分配任务，成员执行后汇报。适合任务分发、客服分流。',
            '多层嵌套的Supervisor结构（Supervisor-of-Supervisors）。适合大规模复杂系统。':
                '主管管理团队负责人，负责人再调度成员。适合有多个子团队的任务。',
            'Agent之间自主交接控制权（Handoff），无中央调度。适合灵活协作、多角度讨论。':
                '当前角色按需交出控制权（Handoff）。适合在专业角色间转交任务。',
            '全连接对等网络，Agent可自由路由。适合高自由度探索型任务。':
                '节点按允许的连接选择下一角色。适合路径随结果变化的任务。',
        },
        'sec09': {
            'A2A管Agent之间怎么对话，MCP管Agent怎么用工具。一个是横向协作层，一个是纵向工具层，两者互补，不是竞争关系。':
                'A2A 用于不同系统中的 Agent 交换任务与结果；MCP 用于连接工具和数据源。同一个系统可以同时使用两种协议。',
            'Google发布的开放协议，解决不同框架/厂商Agent之间的互操作问题。已有150+组织参与，发布v1.0稳定版。':
                '由 Google 发起的开放协议，用于不同框架和厂商的 Agent 协作。版本与参与组织见官方资料。',
            '&#128161; 一句话总结': '两种连接方式',
            '（横向协作层）': '（角色之间的任务协作）',
            '（纵向工具层），两者互补，不是竞争关系。': '（工具与资料接入），可在同一系统中配合使用。',
        },
        'sec10': {
            '多Agent的安全问题是首要障碍，不是普通挑战。Agent链的传播效应会放大单点安全问题——一个Agent被注入恶意指令，可能通过Handoff传播到整个系统。':
                '一个 Agent 读到恶意指令后，可能通过消息或交接把它传给其他角色。接收方需要区分外部资料与执行指令，并校验工具权限。',
            '五大威胁': '常见风险与防护',
            '安全防护三原则': '消息、工具与调用限制',
            '拒绝纯文本，强制Agent间传递结构化数据，防止注入攻击。':
                '校验消息字段，分开资料与指令；结构化格式本身不能阻止注入。',
            '每个Agent只能使用授权的工具，遵循最小权限原则。':
                '宿主按角色限制工具和参数，拒绝超出授权的请求。',
            '设置Token预算和调用深度限制，防止Agent循环调用耗尽资源。':
                '设置 token、调用次数和超时上限，达到上限后停止。',
        },
        'sec11': {
            '不要为了多Agent而多Agent。多Agent的Token开销通常是单Agent的2到5倍，必须通过决策矩阵来判断到底值不值得。':
                '拆分角色会增加通信和模型调用。用同一组任务比较完成率、延迟与 token，再判断是否值得拆分。',
            '三大工程挑战': '通信、等待与结果冲突',
            '挑战1：通信开销': '通信开销',
            '挑战2：死锁和循环依赖': '死锁和循环依赖',
            '挑战3：结果冲突': '结果冲突',
            '多个Agent之间需要频繁通信，每次通信都可能触发LLM调用。通信开销应控制在总Token的30%以内。':
                '角色间传递的长消息可能被反复送入模型。记录输入、输出和通信 token；30% 可作为课堂讨论目标，实际阈值需按任务确定。',
            '使用结构化消息，减少不必要的LLM调用。LangGraph的做法是Sub-Agent的输出直接作为消息传递，Supervisor只在需要决策时调用LLM。':
                '传递必要字段和产物引用，省去重复总结。在 LangGraph 中可直接把成员结果写入状态，在需要决策的节点调用模型。',
            '设置超时和递归深度限制。调用链深度不应超过10层。':
                '定义超时、总步数和等待条件，超限后停止或转人工。10 层是课堂示例上限，需要按实际路径调整。',
            '投票或仲裁机制。加权投票按置信度汇总，专家仲裁由指定Agent做最终裁决。':
                '先核对来源和采集条件，再由指定角色或人工审查。投票与加权汇总需要可靠的评分依据。',
            '&#9989; 推荐': '优先考虑',
            '&#10060; 过度设计': '通常无须拆分',
            '&#10060; 上下文混乱': '先检查上下文是否需要隔离',
            '&#10060; 无法覆盖所有分支': '可用单 Agent 探索路径',
            '&#10060; 通信开销不划算': '评估额外通信成本',
            '&#10060; 串行效率低': '也可由普通程序并行',
            '&#10060; Token开销高2-5x': '先测额外调用与 token',
            '性能基准': '性能目标示例',
            '任务完成率': '完成率目标',
            '通信开销占比': '通信占比目标',
        },
    }
    for section_id, edits in prose.items():
        sections[section_id]['blocks'] = [
            _rewrite(block, edits) for block in sections[section_id]['blocks']]
    # Decorative icons add no information to these protocol and safety cards.
    for section_id in ('sec09', 'sec10'):
        sections[section_id]['blocks'] = [
            re.sub(r'<div class="card-icon">.*?</div>', '', block)
            for block in sections[section_id]['blocks']]
    sections['sec11']['blocks'][-1] += (
        '<p class="comparison-note">以上数值用于练习制定验收目标，未经本课实测，'
        '也不是行业基准。上线前按任务难度、预算与服务要求调整。</p>')
    return sections


def _rewrite(text, edits):
    for old, new in edits.items():
        text = text.replace(old, new)
    return text
