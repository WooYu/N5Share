"""Chinese training content: synthetic diagnosis examples and instructor notes."""
from html import escape


SOURCES = {
    'react': ('ReAct · ICLR 2023', 'https://arxiv.org/abs/2210.03629'),
    'reflexion': ('Reflexion · NeurIPS 2023', 'https://arxiv.org/abs/2303.11366'),
    'plan': ('LangChain · Plan-and-Execute', 'https://blog.langchain.com/planning-agents/'),
    'auto': ('AutoGen · 官方仓库', 'https://github.com/microsoft/autogen'),
    'autochat': ('AutoGen · AgentChat 文档', 'https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/agents.html'),
    'meta': ('MetaGPT · 官方仓库', 'https://github.com/FoundationAgents/MetaGPT'),
    'graph': ('LangGraph · 官方概览', 'https://docs.langchain.com/oss/python/langgraph/overview'),
    'state': ('LangGraph · Graph API', 'https://docs.langchain.com/oss/python/langgraph/graph-api'),
    'persistence': ('LangGraph · Persistence', 'https://docs.langchain.com/oss/python/langgraph/persistence'),
    'interrupt': ('LangGraph · Interrupts', 'https://docs.langchain.com/oss/python/langgraph/interrupts'),
    'multi': ('LangChain · Multi-agent', 'https://docs.langchain.com/oss/python/langchain/multi-agent'),
    'ollama': ('Ollama · Chat API', 'https://docs.ollama.com/api/chat'),
    'autel': ('道通 Autel · 远程专家', 'https://www.auteltech.cn/cloud/3942.jhtml'),
    'patterns': ('Anthropic · Building effective agents', 'https://www.anthropic.com/engineering/building-effective-agents'),
    'research': ('Anthropic · Multi-agent research system', 'https://www.anthropic.com/engineering/multi-agent-research-system'),
}

CHAPTERS = [
    ('开场与目标', 5),
    ('Agent 基础', 13),
    ('能力演进', 13),
    ('按复杂度选择方案', 12),
    ('多 Agent 协作设计', 22),
    ('三种框架的工程取舍', 12),
    ('工作流基线与三个短演示', 15),
    ('综合实战与落地', 28),
]


def p(text, cls=''):
    return f'<p class="{cls}">{text}</p>'


def bullets(*items):
    return '<ul class="points">' + ''.join(f'<li>{item}</li>' for item in items) + '</ul>'


def code(text):
    return '<pre><code>' + escape(text.strip()) + '</code></pre>'


def flow(*items):
    return '<div class="flow">' + '<span class="arrow" aria-hidden="true">→</span>'.join(
        '<div class="node">' + item + '</div>' for item in items) + '</div>'


def split(left, right):
    return f'<div class="split"><div>{left}</div><div>{right}</div></div>'


def table(headers, rows, cls=''):
    return f'<table class="{cls}"><thead><tr>' + ''.join(
        f'<th>{item}</th>' for item in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join(f'<td>{item}</td>' for item in row) + '</tr>'
        for row in rows) + '</tbody></table>'


def evolution(stage):
    labels = [('对话', 'LLM'), ('检索', 'RAG'), ('工具', 'Tool Calling'),
              ('交替', 'ReAct'), ('规划', 'Plan-and-Execute'),
              ('反思', 'Reflexion'), ('协作', 'Multi-Agent')]
    nodes = []
    for position, (label, subtitle) in enumerate(labels, 1):
        cls = 'is-active' if position <= stage else 'is-pending'
        current = ' aria-current="step"' if position == stage else ''
        nodes.append(f'<div class="node {cls}"{current}><small>0{position}</small>'
                     f'<br>{label}<br><small>{subtitle}</small></div>')
    return '<div class="evolution flow" aria-label="七种能力的组合，不是历史进程">' + (
        '<span class="arrow" aria-hidden="true">→</span>'.join(nodes)) + '</div>'


def outing_demo(stage):
    label = '脚本示意：固定回答，无模型或工具调用。' if stage == 1 else '预写规则模拟，无真实 LLM 调用。'
    return (f'<div class="outing-demo" data-outing-stage="{stage}">'
            '<p class="foot">两大一小，半日出游，不订票。场馆与费用均为合成样本。</p>'
            '<div class="interactive-line">'
            '<label>仿真天气 <select data-outing-weather><option value="rain" selected>下雨</option>'
            '<option value="sun">晴天</option></select></label>'
            '<label>预算 <select data-outing-budget><option value="300" selected>300元</option>'
            '<option value="200">200元</option><option value="100">100元</option></select></label>'
            '<button type="button" data-outing-next>下一步演示</button>'
            '<button type="button" data-outing-reset>重置</button>'
            '<span data-outing-counter>0 / 0</span></div>'
            f'<p class="foot">{label}下拉项用于对照天气与预算约束。</p>'
            '<div data-outing-output role="status" aria-live="polite"></div></div>')


def quiz(name, choices):
    buttons = ''.join(
        f'<button type="button" data-correct="{str(correct).lower()}" '
        f'data-feedback="{escape(feedback, quote=True)}">{label}</button>'
        for label, correct, feedback in choices)
    return f'<div class="quiz" data-quiz="{name}">{buttons}' + (
        '<p class="quiz-feedback" role="status" aria-live="polite">'
        '选择后说明：哪条约束决定了你的选择？</p></div>')


def demo_button(pattern, scenario):
    return (f'<button class="primary" data-demo-pattern="{pattern}" '
            f'data-demo-scenario="{scenario}">打开运行台：{pattern} / {scenario}</button>')


def references(entries):
    return '<div class="references">' + ''.join(
        f'<a href="{SOURCES[key][1]}" target="_blank" rel="noopener">'
        f'<span>{position:02}</span><div><strong>{SOURCES[key][0]}</strong>'
        f'<small>{description}</small></div><b>↗</b></a>'
        for position, (key, description) in enumerate(entries, 1)) + '</div>'


LANGGRAPH_DEFINITIONS = '''from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class DiagnosisState(TypedDict, total=False):
    evidence: str
    knowledge: str
    approval: str

evidence = lambda state: {"evidence": "E01"}
knowledge = lambda state: {"knowledge": "K01"}
review = lambda state: {"approval": "pending_human"}'''

LANGGRAPH_WIRING = '''builder = StateGraph(DiagnosisState)
builder.add_node("evidence", evidence)
builder.add_node("knowledge", knowledge)
builder.add_node("review", review)
builder.add_edge(START, "evidence")
builder.add_edge(START, "knowledge")
builder.add_edge(["evidence", "knowledge"], "review")
builder.add_edge("review", END)
graph = builder.compile()
for snapshot in graph.stream({}, stream_mode="values"):
    print(snapshot)'''


slides = []


def add(chapter, title, body, notes, sources=(), layout='', minutes=2):
    slides.append(dict(chapter=chapter, title=title, body=body,
                       notes=f'【{minutes} 分钟】' + notes, sources=list(sources),
                       layout=layout, minutes=minutes))


add('开场与目标', '高级推理框架与多 Agent 协作',
    '<div class="cover-title">高级推理框架<br><em>与多 Agent 协作</em></div>'
    '<p class="cover-sub">道通远程专家：接单前资料初审与专家辅助</p>'
    '<div class="cover-line">同一合成工单 · 工作流基线与三种协作模式 · 四角色综合实战</div>',
    '今天不要求 Python 熟练，也不要求做过模型微调。Agent 在难以预先枚举的任务路径中解释信息、选择工具；已知条件分支仍是工作流。后面用函数、状态对象和 HTTP 对照大家已有的开发经验。'
    '只有两个核心目标：面对复杂度能选择合适的推理与编排方案；能设计一个职责清楚、能够停止的简单多 Agent 系统。'
    '所有工单、诊断读数与知识条目均为合成教学样本，不连接真实车辆。最终输出是待人工确认的建议，演示通过也不代表完成维修。',
    layout='cover', minutes=1)

add('开场与目标', '120 分钟：从判断题走到可运行系统',
    split(table(['前半程', '分钟'], [[name, str(minutes)] for name, minutes in CHAPTERS[:4]]),
          table(['后半程', '分钟'], [[name, str(minutes)] for name, minutes in CHAPTERS[4:]])) +
    p('带走两项能力：<b>按复杂度选方案</b>；<b>设计最小协作闭环</b>。', 'takeaway'),
    '八章总计 120 分钟，包含投票、演示、练习与讨论，不额外添加隐藏的实操时长。前半程先解决何时需要 Agent，再介绍推理机制；后半程把机制映射到角色、框架和工程接口。'
    '请 Java 与后端同学关注权限、状态和错误恢复，前端与客户端同学关注事件、可见状态和人工确认入口。三次选择题不考 API 拼写，而是考选择理由。'
    '最后每组设计等待客户端上传的暂停与恢复，提交角色边界、消息契约和重复或过期上传的处理路径。',
    layout='compact', minutes=2)

add('开场与目标', '道通远程专家：接单前资料初审与专家辅助',
    p('SYNTH-REMOTE-001：接单前整理门店上传资料，标出缺失，供远程专家复核。', 'lead') +
    table(['业务步骤', '负责泳道', 'AI 可辅助的位置'], [
        ['填写 VIN → 导入报告 → 发布订单', '门店 / 客户端', '提取字段、标出缺失'],
        ['资料初审 → 专家接单', '业务平台 → 专家', '整理证据与候选资料'],
        ['请求补充 → 再次上传', '专家 → 门店 / 客户端', '列出缺失项；平台等待资料'],
        ['复核 → 报告 → 客户确认', '专家 → 门店 / 客户', '起草有引用的建议'],
    ]) +
    p('U0121：与 ABS 控制模块失去通信的故障码；voltage：供电电压；gateway：通信网关。', 'foot'),
    '道通远程专家官方产品页描述连接客户与专家的平台，服务包括远程诊断、编程、防盗、ADAS 与咨询；流程包含填写 VIN、导入报告和发布订单。官方还列出实时语音、文字、视频、电话沟通，以及服务和连接状态。'
    '官方宣称 AI 智能匹配，但未披露 LLM 或多智能体架构，不能据此推断自主专家实现。本课接单前资料初审、补充证据与专家辅助是教学设计，不声称厂商已实现这些自动化。'
    '沿泳道讲门店发布订单、平台整理资料、专家接单并复核、需要时请求补充，再形成建议供客户确认。AI 辅助整理和检查，专家负责专业判断，业务平台落实权限；后续复核与确认泳道是教学归纳。'
    'U0121 可通俗理解为某模块没有收到 ABS 控制模块应有的通信，不等于 ABS 模块损坏。voltage 是本次采集的供电电压；gateway 是转接通信的网关，reachable 只说明该次记录可达。远程网络链路中断不能证明车辆故障，网络通畅也不能证明车辆正常。'
    '本课固定检查 voltage、dtc、gateway 三类字段；11.7 V、12.0 V 阈值与规则均为合成教学数据，不是维修标准。必须核对事件时间和条件，不能凭 U0121 与低电压确认因果。',
    ['autel'], layout='compact', minutes=2)

add('Agent 基础', '认识 Agent 的组成部分',
    p('智能体 Agent：围绕目标，利用上下文与工具决定下一步。', 'lead') +
    '<div class="agent-anatomy">'
    '<div class="anatomy-input"><strong>用户目标</strong><p>两大一小，半日出游</p><span>↓</span></div>'
    '<div class="anatomy-core">'
    '<div class="anatomy-model"><strong>模型 Model</strong><p>结合目标与证据，判断下一步：下雨，先查室内场馆</p></div>'
    '<div class="anatomy-parts">'
    '<div class="anatomy-part"><strong>指令 Instructions</strong><p>约束模型：预算300元，不订票</p></div>'
    '<div class="anatomy-part"><strong>上下文 Context</strong><p>供模型参考：同行人数、天气、已查候选</p></div>'
    '<div class="anatomy-part"><strong>工具 Tools</strong><p>模型请求 → 程序查天气、算总价 → 结果回传</p></div>'
    '<div class="anatomy-part"><strong>控制循环 Control loop</strong><p>判断 → 调用 → 观察 ↺；合适或无解就停止</p></div>'
    '</div></div>'
    '<div class="anatomy-output"><span>↓</span><strong>可核对的建议</strong><p>雨天选城市博物馆，合计210元，待用户确认</p></div>'
    '</div>',
    '用一个周末出游任务解释五个部件。模型 Model 解释需求并提出选择；指令 Instructions 限制半日、预算300元、不订票；上下文 Context 保存两大一小、天气和已查到的场馆信息；工具 Tools 提供查询和计算；控制循环 Control loop 把结果带回下一次判断。'
    '图中模型位于中心，指令施加约束，上下文提供信息，工具接收请求并回传结果，控制循环组织判断与反馈；四个配套部件不是依次执行的流水线。下雨时放弃户外，超预算时换方案，没有合适候选时说明不足并停止。'
    'LLM 即大语言模型 Large Language Model，是一种决策来源，真正执行工具的是宿主程序。运行时负责参数、权限、预算与终止，不能让模型自行放宽约束。'
    '本课后面的出游动画以预写规则解释组成，不调用真实模型。这个已知小任务用固定工作流也足够；难以预先枚举的自然语言需求与查询路径，才值得评估 Agent。',
    ['patterns'], layout='compact', minutes=4)

add('Agent 基础', '本课学习路线：会判断、懂协作、能搭建',
    table(['步骤', '学会回答', '对应章节'], [
        ['01 会判断', '怎么查、怎么改？<br><small>推理策略 Reasoning Strategy</small>', '能力演进 → 按复杂度选择方案'],
        ['02 懂协作', '谁来做、如何汇合？<br><small>协作架构 Collaboration Architecture</small>', '多 Agent 协作设计'],
        ['03 能搭建', '怎样用代码运行？<br><small>开发框架 Development Framework</small>', '三种框架的工程取舍 → 短演示 → 综合实战'],
    ]) + p('先用出游理解机制，再用接单前资料初审练习工程实现。', 'takeaway'),
    '按学习动作讲路线，而不是先背分类。第一步会判断：能力演进介绍 ReAct、规划与反思，再用复杂度选择题决定普通程序、工作流或 Agent。第二步懂协作：明确角色产物，再学习主管分派、并行与评审修订。第三步能搭建：比较开发框架，运行基线与短演示，完成综合设计。'
    '推理策略 Reasoning Strategy 回答一个任务怎样决策；协作架构 Collaboration Architecture 回答多人怎样分工；开发框架 Development Framework 回答代码怎样管理状态与执行。一个框架能实现多种策略，策略与架构也能组合。'
    'Java 业务服务负责权限，状态与消息可类比 DTO，前端呈现进度和人工确认。最终实战题目是道通远程专家：接单前资料初审与专家辅助。',
    ['patterns', 'graph'], layout='compact', minutes=3)

add('Agent 基础', '普通程序、工作流和智能体有什么不同？',
    table(['实现方式', '怎样完成任务', '生活中的例子'], [
        ['普通程序', '按写好的规则计算与校验', '同一次出游：门票60 + 交通40 + 餐饮80 = 180元'],
        ['工作流 Workflow', '沿预设步骤和条件分支执行', '查天气 → 雨天筛室内 → 算总价 → 请用户确认'],
        ['智能体 Agent', '解释需求，结合结果选择后续行动', '理解“孩子怕淋雨”，选择查询；超预算后再找候选'],
    ]) + p('组合使用：程序检查权限 → AI 查询资料 → 用户确认方案；本例不订票。', 'takeaway'),
    '三种方式围绕同一个任务：两大一小，半日出游，预算300元，不订票。普通程序可靠地算总价；工作流预先写好晴雨和预算分支；Agent 可以解释开放的偏好并在运行中选择查询路径。'
    '有 if/else、有反馈或调用了 LLM，都不自动意味着是 Agent。模型若只执行固定步骤中的文本摘要，整体仍可由工作流控制。下雨改室内和超预算换候选，这个已知例子完全可以写成固定流程。'
    '混合流程用白话说明：程序先检查用户有没有权访问资料；AI 在允许的工具范围内查找信息；最后由用户确认建议。确认不会触发本例中的订票。权限和约束由程序执行，不交给模型自行决定。'
    '六分钟内先比较三行，再请学员分别说出计算、查天气和理解开放偏好属于哪种职责。推理循环的反馈与停止将在 ReAct 演进页观察，固定工作流基线保留在后面的运行台章节。',
    ['patterns'], layout='compact', minutes=6)

add('能力演进', '能力演进 ①：大语言模型 LLM',
    evolution(1) +
    p('先给一个出游建议：能组织语言，还没有当前天气与费用依据。', 'lead') +
    p('机制：根据输入生成回答；局限：固定示意答案，不随下拉项重新推理。', 'foot') +
    outing_demo(1),
    '七页展示可以组合的能力，不是技术发展的历史时间线，也不是每个应用必须逐级升级。全程沿用两大一小、半日出游、预算300元、不订票；下拉预算可对照200或100元。'
    'LLM 是大语言模型 Large Language Model。本页只展示事先写好的回答，例如建议湖畔公园，并提示核对天气与费用；没有实际模型、检索或工具调用。改变天气或预算不会使固定答案获得新的事实依据。'
    '统一合成场馆：湖畔公园为户外，门票60、交通40、餐饮80，总计180元；自然馆为室内，150+60+100=310元；城市博物馆为室内，90+40+80=210元。金额均为本次两大一小的合计。下雨需要室内，但本页并未查证这一约束。'
    '这些场馆与价格不是现实推荐，后六页也是预写模拟。固定流程足够完成这个已知例子，动画用于比较机制，不证明自主能力。',
    layout='compact outing-slide', minutes=1)

add('能力演进', '能力演进 ②：检索增强生成 RAG',
    evolution(2) +
    p('回答前先找资料：雨天选室内，费用必须算全。', 'lead') +
    p('机制：检索 → 引用 → 回答；局限：文档规则不等于实时天气与报价。', 'foot') +
    outing_demo(2),
    'RAG 是检索增强生成 Retrieval-Augmented Generation，可理解为先查资料再回答，不是重新训练模型。预写检索片段 D01：下雨时选择室内场馆；D02：总成本必须包含门票、交通、餐饮。'
    '演示把 D01、D02 带入回答并保留引用。仅有规则，仍不能声称已查到真实天气或实时价格；合成场馆数据与资料规则是不同来源。'
    '两大一小、半日、预算300元、不订票保持一致。预算改成200或100时，成本口径仍不能省略交通和餐饮。本页检索和回答均为脚本模拟，没有真实检索服务或 LLM；固定检索链也是工作流。',
    layout='compact outing-slide', minutes=2)

add('能力演进', '能力演进 ③：工具调用 Tool Calling',
    evolution(3) +
    p('把“查一下、算一下”变成可核对的调用结果。', 'lead') +
    p('机制（伪代码）：weather → catalog → sum；局限：查天气、场馆和总价，不等于自动规划。', 'foot') +
    outing_demo(3),
    '工具调用 Tool Calling 区分提出请求、宿主校验执行、收到结果。这里 weather、catalog、sum 是概念伪代码，界面实际使用 read_weather、localcatalog、outingCost；均为浏览器预写步骤示意，无网络服务、真实模型或订票动作。'
    'weather 使用 rain/sun 选项；catalog 返回合成场馆：湖畔公园户外60+40+80=180，自然馆室内150+60+100=310，城市博物馆室内90+40+80=210。sum 按门票、交通、餐饮核算两大一小合计。'
    '300元下自然馆也超预算，不能只看门票150元就认为可行。下雨排除公园；200元下雨和100元任意天气都没有符合条件的候选。此页重点观察数据来源和计算返回，下一页再观察怎样利用反馈重选。'
    '工具返回事实或错误，不能凭一句已经查过认定调用成功；参数权限与预算由运行时负责。已知调用次序可以直接使用固定工作流。',
    layout='compact outing-slide', minutes=2)

add('能力演进', '能力演进 ④：推理与行动交替 ReAct',
    evolution(4) +
    p('先试自然馆，算出310元超预算，再查城市博物馆210元。', 'lead') +
    p('机制：判断 Thought → 行动 Action → 观察 Observation；满足条件或无候选时停止。', 'foot') +
    outing_demo(4),
    'ReAct 强调推理与行动交替：决定先查什么，执行查询，利用返回决定下一步。展示简短教学决策摘要，不展示模型完整内部思维；这里每一步均预写。'
    '默认下雨、预算300元：先按 D01 排除户外湖畔公园；查询自然馆并按 D02 算出310元，观察超预算后换城市博物馆，总计210元，通过天气和预算检查，再请用户确认，不订票。'
    '预算改为200元且下雨，室内候选都超额，应保留已查价格并说明没有可行方案；100元同样停止。晴天时公园180元可作为候选。不能偷偷增预算、漏餐费或反复查询同一结果。'
    '成功、无可行候选、工具错误和无进展都应有明确出口，运行时还要限制步数与时长。单次工具调用不等于 ReAct；本页这种已知重选也可以由固定分支实现。',
    ['react'], layout='compact outing-slide', minutes=2)

add('能力演进', '能力演进 ⑤：规划执行 Plan-and-Execute',
    evolution(5) +
    p('先列任务依赖：天气与场馆信息齐备后，才能筛选、算价和验收。', 'lead') +
    p('机制：规划 Planning → 执行 → 检查；局限：计划需要真实结果支持，不能提前宣布成功。', 'foot') +
    outing_demo(5),
    '规划 Planning 把目标拆成有依赖和交付标准的任务，Plan-and-Execute 将规划与执行分开。出游计划是读取天气和场馆，再按晴雨筛选，计算门票加交通加餐饮，最后核对两大一小、半日、预算与不订票。'
    '天气查询和场馆目录可从同一需求独立启动；筛选依赖两者，总价依赖选中场馆，最终建议依赖筛选与成本检查。不能先写可行再补证据。'
    '默认300元雨天选城市博物馆210元；200元雨天无合适场馆，反馈回计划并停止或请用户调整条件，系统不能自行放宽条件。已经有效的天气和目录无需全部重查。'
    '执行器可以是普通函数或 ReAct 循环。此处只是预写计划与步骤模拟，无真实 LLM；固定工作流能表达已知依赖，不必为了有计划而增加智能体。',
    ['plan'], layout='compact outing-slide', minutes=2)

add('能力演进', '能力演进 ⑥：反思修订 Reflexion',
    evolution(6) +
    p('复核“去湖畔公园，费用合适”的无依据草稿，再按证据修订。', 'lead') +
    p('机制：尝试 → 反馈 → 反思 Reflection → 再验收；局限：改语气不能补足证据。', 'foot') +
    outing_demo(6),
    '反思 Reflection 将反馈转为下一次可执行的改进；Reflexion 用语言反馈影响后续尝试，更新任务上下文而非模型权重。本页是简化的预写机制演示，不是论文实验复现。'
    '初稿直接推荐湖畔公园但未引用天气或完整费用。评审指出缺天气依据与成本核算；默认雨天还违反 D01。反思应写成先核对 weather，再用 catalog 和 sum，引用 D01、D02 后重写并验收。'
    '默认雨天300元修订为城市博物馆210元；200或100元雨天应修订为无可行候选，不能把措辞改成可能适合就算通过。晴天若预算至少180元，公园可保留，但必须补上天气与费用证据。'
    '反思本身可能出错，仍要外部检查；同一错误反复出现或没有新增证据时有限停止。固定审查规则足够覆盖本例，无真实模型参与。',
    ['reflexion'], layout='compact outing-slide', minutes=2)

add('能力演进', '能力演进 ⑦：多智能体 Multi-Agent',
    evolution(7) +
    p('天气与费用各自形成摘要，由协调者合并成可核对的出游建议。', 'lead') +
    p('机制：独立分工 → 汇合 → 统一检查；局限：多角色有协调成本，固定流程也能完成本例。', 'foot') +
    outing_demo(7),
    '多智能体 Multi-Agent 按职责组织协作。同一出游需求下，天气角色独立读取 weather 与 D01，提交天气和室内外约束；费用角色独立读取全部 catalog 与 D02，提交三个场馆的完整费用及预算判断，不等待天气结论。'
    '协调者拿到两份摘要后取交集：雨天排除湖畔公园，300元预算排除自然馆，留下城市博物馆210元。雨天200或100元无解；晴天200元可选公园180元。合并保留引用与限制，不能覆盖另一角色的证据。'
    '只有各自结果齐备才能交付，部分失败必须说明。界面把两份独立角色摘要放在同一事件展示，不代表后台真实并行；这里角色和摘要均由预写规则模拟，没有真实 LLM 或自主专家。'
    '七页表示可组合的能力：角色内部仍可使用 RAG、工具、ReAct、规划或反思，并非历史先后或能力排名。这个已知小任务仍用固定工作流即可；后续有独立上下文、工具权限或专业责任时，才评估拆分收益。',
    ['multi'], layout='compact outing-slide', minutes=2)

add('按复杂度选择方案', '决策卡：选择能解决问题的最简单方案',
    table(['先问这个问题', '优先选择', '工单中的例子'], [
        ['输入齐全，只需一次生成？', '普通 LLM', '改写症状描述'],
        ['步骤与判断条件稳定？', '固定工作流', '按字段检查工单完整性'],
        ['路径难穷举，需解释非结构化信息并选工具？', '单 Agent', '自由文本日志驱动探索查证'],
        ['新增独立上下文、权限或专业归属？', '评估多 Agent', '隔离证据、资料与专业审查'],
    ]) + p('升级前写明瓶颈；升级后比较质量、延迟、费用和失败恢复。', 'takeaway'),
    '这是可带走的决策卡。按从上到下的顺序问，但系统可以混合：固定鉴权、Agent 查证、固定审批可以共存。'
    '参考答案：完整文本润色用普通 LLM；已知字段检查与补充条件用普通代码或工作流。下一步依赖运行时证据本身不足以选 Agent；难以枚举路径、需要解释非结构化信息并选择工具时才评估单 Agent。'
    '先验证确定性工作流基线，再判断是否需要单 Agent；只有新增独立上下文、工具权限或专业责任要求时再评估多 Agent。隔离也可由普通服务和工作流落实，必须说明模型决策额外解决什么。记录验收率与调用成本，角色数量不是成果指标。',
    ['patterns'], layout='compact', minutes=3)

add('按复杂度选择方案', '互动 ①：固定字段检查，需要 Agent 吗？',
    p('提交工单时检查设备标识、采集时间、授权状态是否齐全；规则已明确。', 'lead') +
    quiz('fixed-workflow', [
        ('A　普通代码或固定工作流', True, '正确：规则稳定，确定性执行更易测试和解释，不需要模型决定必填项。'),
        ('B　单 Agent 每次决定必填字段', False, '业务规则已确定，交给模型反复选择会造成口径漂移。'),
        ('C　三个 Agent 相互投票', False, '没有独立职责需求；额外协调不改善确定性校验。'),
    ]),
    '先留十秒独立思考，再请后端同学提出实现方案。参考答案 A，字段与规则明确，结果容易测试，不需要模型推理。点错时读出反馈，避免变成猜老师偏好。'
    '追问自由文本输入怎么办：可以用 LLM 提取候选字段，再用确定性规则验证，缺失时让用户确认。这是混合设计，不要求每一步都智能化。'
    '本题故意选择简单任务，说明课程不是推广多 Agent。省下不必要的复杂度，才能把预算花在真正需要动态查证的位置。',
    layout='compact', minutes=3)

add('按复杂度选择方案', '互动 ②：每次缺失的证据不同，如何处理？',
    p('缺电压就读补充记录；读数冲突就查事件时间；失败转人工。所有条件与工具映射已知。', 'lead') +
    quiz('single-agent', [
        ('A　带条件分支与预算的固定工作流', True, '正确：虽然下一步依赖证据，但条件和工具映射可穷举，普通工作流足够。'),
        ('B　只要依据反馈就必须用单 Agent', False, '证据驱动分支也可用 if/else；难以穷举路径、需解释非结构化资料并选工具时才评估 Agent。'),
        ('C　直接配置十个专家 Agent', False, '原始固定字段任务没有新增独立上下文、权限或专业责任要求，无需拆角色。'),
    ]),
    '参考答案 A。缺失字段不同、下一步依赖返回都不构成 Agent 的充分理由。题干已经列出条件与工具映射，写成可测试的路由即可；还应保留预算、超时与失败出口。'
    '改变一道条件再讨论：如果输入是格式不统一的维修描述与日志，需要解释语义，工具组合和查询路径难以预先枚举，则可评估有工具白名单和预算的单 Agent。此时选择变化来自任务需求，而不是把已知 if/else 改叫推理。'
    '请前端同学描述证据不足时的界面，再请后端同学写出本题三条条件分支；用这个反例检验是否真正理解选型标准。',
    layout='compact', minutes=3)

add('按复杂度选择方案', '互动 ③：何时值得拆成多个角色？',
    p('新增要求：敏感日志与资料检索隔离上下文及权限；专业审查岗位独立负责引用验收。', 'lead') +
    quiz('multi-agent', [
        ('A　一个 prompt 包含全部权限和历史', False, '可作为基线，但本题有明确权限与审查隔离要求，全部混合更难落实边界。'),
        ('B　证据、知识、审查分工，协调者汇总', True, '正确：分工对应独立产物、权限和验收，仍需比较额外调用成本。'),
        ('C　重复回答，按多数票决定原因', False, '重复意见不是独立证据；同模型可能共享偏差，多数票也不能授权维修。'),
    ]),
    '参考答案 B，请说出产物不同、权限不同、审查要求不同三个拆分理由。独立职责不等于模型错误相互独立，同一模型的多个角色也可能犯相同错误。'
    '追问是否要四个服务或四个模型：都不需要，可以同进程实现逻辑隔离，部分节点也可以是普通代码。权限应由运行时落实，不能只写在 prompt 里。'
    '若去掉新增隔离要求，原始固定字段任务回到工作流基线即可。B 是给定协作方案中符合新边界的选择，不证明多个模型是唯一实现；权限与专业责任仍需普通工程机制落实。',
    layout='compact', minutes=3)

add('多 Agent 协作设计', '先定义角色产物，再讨论角色数量',
    table(['角色', '输入 → 输出', '职责边界'], [
        ['协调者 Coordinator', '目标与状态 → 子任务、草稿', '路由与汇总，不编造证据'],
        ['证据者 Evidence', '工单标识 → 事实、缺失、引用', '只读取证，不替代知识判断'],
        ['知识者 Knowledge', '症状与上下文 → 资料与条件', '通用说明不等于本次结论'],
        ['审查者 Reviewer', '草稿与证据 → 通过或退回', '核对引用，不授予审批'],
    ]) + p('每个角色只接收完成职责所需的信息与工具。', 'takeaway'),
    '先写四个接口，不急着写复杂 prompt。证据能追到工具记录，知识能追到文档版本，审查指出具体问题，协调者才有依据修订。'
    '若两个角色输入、工具、输出和验收都相同，仅名字不同，先考虑合并。共享底层模型不影响职责隔离，但工具权限需由运行时落实，不能仅靠“不要越权”的提示。'
    '综合实验以新增的上下文、权限与专业责任要求教学四类逻辑边界，规则节点模拟这些角色；原始固定字段任务无需多 Agent。请学员说明去掉新增要求后可合并哪些节点，并与 workflow 比较额外成本。',
    ['multi'], layout='compact', minutes=3)

add('多 Agent 协作设计', '模式 ①：主管 Supervisor，集中分派与汇总',
    '<div class="topology"><div class="top-node">协调者<br><small>分派 · 判断进度 · 汇总</small></div>'
    '<div class="tree-line">↓<span>↓</span>↓</div><div class="leaves"><div>证据</div><div>知识</div><div>审查</div></div></div>' +
    bullets('控制权返回协调者，由它选择下一位角色。',
            '适合：步骤随状态改变，但需要统一出口。',
            '风险：中央瓶颈，以及摘要丢失关键条件。') +
    p('工单：缺电压 → 先补证据 → 再核对资料。', 'foot'),
    '按箭头解释集中控制，专家不必知道全队历史，返回结构化产物即可。协调者根据状态决定继续、补查或停止。'
    '协调者可以是规则路由，也可以由 LLM 提出下一步再经白名单验证。固定路由演示不能宣传为模型自主分派。'
    '若知识者只返回大段文本，版本和限制可能在汇总中丢失。契约化输出、引用保留和明确检查项比简单增加模型更可控。请学员预测正常工单中控制权回到中央的时机，短演示再核对。',
    ['patterns', 'multi'], layout='compact', minutes=3)

add('多 Agent 协作设计', '模式 ②：并行 Parallel，先判断是否独立',
    flow('同一工单快照', '证据 ∥ 候选资料', '等待与合并', '统一验收') +
    bullets('可并行：两项查询从同一输入独立启动。',
            '必须等待：建议依赖双方结果，不能先写后补。',
            '合并：保留时间和来源，不用后写覆盖先写。',
            '失败：区分部分成功、超时与必要证据缺失。'),
    '并行的是证据获取和候选资料检索，资料适用性仍需汇合后核对。先画真实依赖再并发，不是把所有节点连到开始就完成优化。'
    '不同采集条件的读数冲突时不能平均，也不能选更快返回的那份。应保留来源、时间、条件，请求复核。一个任务成功也不能掩盖另一个必要任务失败。'
    '前端逐步播放是展示顺序，不能证明后端真并发。看调度与时间戳才能判断；总耗时还有汇总和审查，不能承诺角色翻倍耗时减半。让学员找出汇合屏障。',
    ['patterns', 'research'], layout='compact', minutes=3)

add('多 Agent 协作设计', '模式 ③：评审 Review，用明确标准修订',
    flow('建议草稿', '按标准审查', '带理由退回', '有限修订') +
    table(['标准', '具体退回理由'], [
        ['可追溯', '结论无引用，或引用记录不存在'],
        ['适用性', '资料版本与设备上下文不匹配'],
        ['边界与完整性', '缺失项未披露，或跳过人工确认'],
    ]) + p('达到修订上限仍不合格 → 请求人工处理。', 'takeaway'),
    '审查输出必须可操作，例如补哪条引用、删哪句越界表述，不只给一个分数。修订者逐条处理，再按同一标准复核。'
    '真实证据缺失不是文案问题，修改措辞不能补齐事实。可以生成注明不足的阶段性结果，但不能标成材料完整的最终建议。'
    '审查可用规则、模型或混合实现；模型通过不代表结论正确，更不代表人工授权。观察修订次数、反馈内容和是否新增有效证据。让学员解释为什么不能循环到所有角色都满意。',
    ['patterns', 'reflexion'], layout='compact', minutes=3)

add('多 Agent 协作设计', '消息 Message：接收方不应该猜上下文',
    split(code('''{
  "run_id": "run-demo",
  "task_id": "collect-evidence",
  "from": "evidence",
  "to": "coordinator",
  "plan_version": 2,
  "status": "partial",
  "evidence_refs": ["E01"],
  "missing": ["voltage"]
}'''), bullets('关联：哪次运行、哪个任务、哪版状态？',
                 '结果：成功、部分成功还是失败？',
                 '依据：引用在哪里，还缺什么？',
                 '接收：重复、过期消息怎样处理？')) +
    p('应用层教学契约，不是框架自动提供的统一协议。', 'foot'),
    '同一工单可多次运行，一次运行有多个子任务，所以 run_id 和 task_id 不可混淆。版本字段只有接收端真的检查才防止旧结果覆盖。'
    'partial 表示部分证据返回，missing 指出下一步需要什么。引用要能查到记录，不能由模型随意生成编号。跨进程还要考虑消息 ID、幂等键、确认与超时，本页只展示最小字段。'
    'Java DTO、Python 类型和前端 TypeScript 类型应共享契约或进行一致性校验，避免某端把 partial 当成 complete。请学员解释一条旧版本消息应如何处理。',
    layout='compact', minutes=3)

add('多 Agent 协作设计', '共享状态 State：事实、草稿与批准分开',
    table(['状态域', '主要写入者', '更新约定'], [
        ['observations', '工具与角色适配器', '保留证据、来源与工具错误'],
        ['plan_version / draft', '协调者', '带修订版本，引用现有证据'],
        ['review / revision_rounds', '审查与编排运行时', '保留原因，限制修订次数'],
        ['report / status', '可信运行时', '只交付建议；不代表人工批准'],
    ]) + p('并行同写一个键，需 reducer 或独立字段；状态对象不等于数据库事务。', 'takeaway'),
    '共享状态是任务工作记录，不是所有聊天历史拼成字符串。事实、建议和批准具有不同可信度与写入来源，必须分开。'
    '两个节点都返回 results 字符串可能覆盖。可以拆成 evidence 与 knowledge，或明确列表合并规则。LangGraph reducer 解决图内合并，不自动处理外部数据库事务与分布式锁。'
    '请两位学员扮演证据和知识角色，说出能写哪些字段。审查者可要求修订草稿，不能改原始证据或设置人工批准。追问多次重试是否会重复追加同一证据，借此说明去重与版本检查。',
    ['state'], layout='compact', minutes=4)

add('多 Agent 协作设计', '协作结束：谁有权说“够了”？',
    table(['条件', '负责判断', '系统出口'], [
        ['产物齐备且审查通过', '校验器 + 编排器', '建议待人工确认'],
        ['证据不足或冲突未解', '角色报告 + 编排器', '补充信息或人工复核'],
        ['无进展或重复分派', '运行时计数与事件检查', '受控停止'],
        ['工具失败或预算耗尽', '工具适配器 + 运行时', '失败 / 停止，保留部分成果'],
    ]) + p('人工介入 HITL：必要时由人复核或决定；统一出口与预算。', 'takeaway'),
    '人工介入 HITL 即 Human-in-the-Loop，指在流程中引入人的复核或决定；标记待确认并不等于已实现审批恢复。请画出一个死循环：协调者要求补资料，资料不可得，审查继续要求补资料。需要全局预算和无进展检测，不能只给每个角色一句适时停止。'
    '进展可以是新增有效证据或消除具体待审问题，反复换措辞不算进展。知识检索成功而证据工具失败，仍不是整次任务成功。'
    '生产系统还需传播用户取消。本课重点覆盖正常、缺失、冲突、工具失败和预算耗尽，轨迹可回放不代表跨进程恢复。请学员说明每个异常出口给用户保留什么。',
    layout='compact', minutes=3)

add('三种框架的工程取舍', '本课为什么选 LangGraph：约束先于框架',
    table(['本课具体约束', '选择依据', '仍须手写'], [
        ['同状态对比固定流、分支、并行、回路', '显式 State / Node / Edge', '状态 schema、路由与 reducer'],
        ['缺失、冲突与预算出口可检查', '图节点与条件边可观察', '证据规则、工具、预算与日志'],
        ['Java 业务与 Python 编排分开', '通过 HTTP 保持服务边界', '鉴权、接口和业务存储'],
    ]) + p('固定字段任务可只用普通代码；LangGraph 是本课展示编排的工具。', 'takeaway'),
    '回到开头三层地图：任务解法和责任划分先确定，框架最后决定。本课要在同一轨迹契约下明确展示分支、汇合与回路，所以选择 LangGraph；不据此声称它的诊断效果更好。'
    '节点、领域规则、消息校验、权限、预算与异常处理仍须手写。图框架不提供维修知识，也不把规则节点变成自主 Agent。',
    ['graph', 'state'], layout='compact', minutes=1)

add('三种框架的工程取舍', '约束改变时：何时考虑另外两种框架',
    table(['约束 / 选择', '适合的抽象', '必须自己承担的工作'], [
        ['显式状态、分支与恢复设计 → LangGraph', 'State / Node / Edge', '领域节点、路由、合并与存储配置'],
        ['已有消息团队，核心是对话委派 → AutoGen', 'AgentChat 团队；Core 消息运行时', '工具、终止、上下文；维护与迁移计划'],
        ['角色按 SOP 交付专业产物 → MetaGPT', 'Role / Action / Team', '业务 SOP、产物验收与依赖适配'],
        ['Java / 客户端团队 → 先定服务边界', 'HTTP 契约与状态 DTO', '语言 SDK、跨服务运维与权限'],
    ], 'selection-matrix') + p('框架匹配开发约束；不能替你证明需要多 Agent。', 'foot'),
    'AutoGen 可在已有 AgentChat 团队、消息交互和委派占主导且能承担维护迁移成本时作为候选。AgentChat 与 Core 的抽象不同，不混用旧版 0.2 示例；新项目还应考虑其官方迁移建议。'
    'MetaGPT 适合业务确有角色 SOP 和明确交付物、团队愿意适配其流程假设的情况；固定字段读取不足以支持采用它。诊断角色、工具和验收依旧要写。'
    '本课代码使用 Python，不代表三个框架在 Java、Python、TypeScript 或 .NET 上功能对等。按所选版本核对 SDK；Java 与客户端可通过服务接口接入，无需为框架重写整个业务系统。',
    ['auto', 'meta', 'graph'], layout='compact', minutes=2)

add('三种框架的工程取舍', '比较 ②：恢复、生态与维护成本',
    table(['维度', 'AutoGen', 'MetaGPT', 'LangGraph'], [
        ['恢复', '按组件保存/加载；核对支持范围', '核对角色、产物持久化机制', '配置检查点、线程与恢复路径'],
        ['生态', 'AgentChat / Core / Extensions', 'Role / Action 与 SOP 示例', 'LangChain 集成；可独立使用'],
        ['成本', 'API 代际、兼容与迁移', '流程适配、Python 依赖', '显式状态、部署与观测'],
    ], 'compare') + p('框架能力不等于项目已具备持久恢复；外部副作用仍需幂等。', 'takeaway'),
    'LangGraph 提供 persistence 与 interrupt，但要配置存储、线程标识、恢复路径和人工输入流程。没有配置不能宣称重启进程可恢复。'
    'AutoGen 要按具体组件和版本核对状态保存语义；MetaGPT 要检查所选角色、动作和产物，不从框架名字推断自动恢复。保存 JSON 轨迹是回放和审计，不是恢复执行。'
    '本课 Demo 不承诺生产持久恢复。生态丰富只是线索，团队能否维护、测试、升级决定采用成本。问学员有检查点是否就可安全重放外部写入，答案还需要幂等和结果核对。',
    ['auto', 'meta', 'persistence'], layout='compact', minutes=3)

add('三种框架的工程取舍', '维护现状：选型前必须核对的事实',
    table(['框架', '官方材料信息', '采用前动作'], [
        ['AutoGen', 'Maintenance Mode；无新功能/增强，社区维护', '评估支持与迁移；新项目慎选'],
        ['MetaGPT', 'README：Python ≥ 3.9 且 &lt; 3.12', '核对 releases、依赖与兼容性'],
        ['LangGraph', '低层有状态编排，混合确定性与 LLM 步骤', '锁定版本，验证恢复与中断配置'],
    ]) +
    p('核对：2026-09-21，依据官方仓库与文档；MetaGPT README 不足以证明维护活跃度。', 'source-note') +
    p('迁移脚注：AutoGen 官方推荐新用户评估 Microsoft Agent Framework；本课仍只讲三种框架。', 'foot'),
    '核对日期为 2026-09-21。AutoGen README 明确 Maintenance Mode，不再新增功能或增强，由社区维护；新用户推荐 Microsoft Agent Framework。维护模式不等于仓库不能使用或现有应用立即失效。'
    'MetaGPT Python 范围来自 README，仍需核对具体 release 与依赖，不能仅凭 README 推断活跃或停更。LangGraph 文档说明能力，不说明本课已全部配置。'
    '日期不是永久承诺，正式立项再检查 releases、问题响应和升级路径。迁移只作脚注，不新增第四套框架教学。',
    ['auto', 'meta', 'graph'], layout='compact', minutes=2)

add('三种框架的工程取舍', 'AutoGen 与 MetaGPT：结构映射即可入门',
    split('<h3>AutoGen：专家作为工具</h3>' + code('''from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool

specialist = AssistantAgent(
    "evidence", model_client=model_client)
specialist_tool = AgentTool(specialist)
coordinator = AssistantAgent(
    "coordinator", model_client=model_client,
    tools=[specialist_tool])'''),
          '<h3>MetaGPT：角色、行动与产物</h3>' + code('''Role: EvidenceRole
  observes: WorkOrderMessage
  Action: CollectEvidence
  produces: EvidenceArtifact

Team: Coordinator + Evidence + Knowledge
SOP: collect -> synthesize -> review
stop: accepted / missing / budget''')) +
    p('左：当前 AgentChat API 片段，省略模型配置与运行。右：结构伪代码，不可直接执行。', 'foot'),
    '左侧使用当前 AssistantAgent 与 AgentTool 命名，不使用旧版 0.2 GroupChat。model_client 需外部提供有效配置；此片段省略领域工具、提示词、异步执行与资源关闭，不作为完整可运行项目。'
    '右侧故意用 Role、Action、Team、SOP 表达结构，不伪造不存在的诊断 SDK。实际实现要按框架接口定义角色、动作、消息和产物。'
    '本页不现场安装三套依赖，重点是指出分派在哪里、状态在哪里、谁判断停止。主实现继续用 LangGraph，避免零基础学员陷入三个框架的版本细节。',
    ['autochat', 'meta'], layout='compact', minutes=2)

add('三种框架的工程取舍', 'LangGraph：把协作设计变成显式图',
    flow('State<br><small>工单与证据</small>', 'Node<br><small>函数或模型</small>',
         'Edge<br><small>依赖与分支</small>', 'End<br><small>解释出口</small>') +
    bullets('节点读取当前信息，返回本次状态更新。',
            '普通边、条件路由与汇合表达控制关系。',
            '固定校验、规则模拟与真实 LLM 节点可以共存。') +
    p('本课：LangGraph 1.2.11 实际编排 + 固定规则模拟决策；未实现真实 LLM 接入。', 'takeaway'),
    '用状态机类比：State 是任务对象，Node 是处理函数，Edge 是执行关系。参数校验节点可以是普通程序，不必叫智能体。'
    '框架允许混合普通函数与模型调用，但课堂当前只实现固定规则决策。未来替换模型节点仍要保留工具结果、schema 和验收器，不会自动提升事实可靠性。后端拒绝真实模型选项，不应现场尝试切换。'
    '检查点和 interrupt 是需要配置的能力。把结果设成待人工确认，不代表已完成跨进程持久暂停与审批恢复。综合实战展示实际 StateGraph API，先理解机制再扩展生产能力。',
    ['graph', 'state', 'interrupt'], layout='compact', minutes=2)

add('工作流基线与三个短演示', '固定工作流 Workflow：完成原始任务',
    flow('读工单与资料', '已知条件补查', '校验证据', '待审报告') +
    bullets('先运行 workflow / missing：缺电压 → 补充读取 → 校验通过。',
            '同 fixtures、工具、验收和轨迹 schema，再比较三种协作方式。',
            '原始任务无需拆角色；后续以新增隔离要求解释协作成本。') +
    demo_button('workflow', 'missing') +
    p('来源：本次本地运行 / 录制教学回放；均为规则决策与合成数据。', 'foot'),
    '本页两分钟先看基线：核对 workflow / missing 和来源标签，运行后找出固定补充条件、read_supplemental 与通过后的待审核报告。基线采用同一 fixtures、工具与轨迹 schema，不靠降低验收标准简化。'
    '先看中文故事线、角色图和当前已观察证据，再展开事件 JSON 核对参数。基线能完成原始三字段任务，接下来仅在新增上下文、权限或专业责任隔离要求下讨论角色模式。'
    '三个短演示各用一个异常观察机制，不能直接作性能排名；章末用“基线与三种模式”统一情景对比 workflow、supervisor、parallel、review。现场运行和录制回放保持明确来源。',
    layout='compact', minutes=2)

add('工作流基线与三个短演示', '短演示 ①：主管委派 Supervisor / 重新分派',
    flow('初次取证', '协调者发现缺失', '分派补充读取', '汇总与审查') +
    bullets('预测：缺少电压证据时，协调者应改变什么？',
            '观察：新反馈、计划修订、read_supplemental 与补齐证据。',
            '验收：补齐后再生成建议，保留重新分派的依据。') +
    demo_button('supervisor', 'missing'),
    '先用三十秒预测，再打开运行台核对 supervisor / missing。现场运行后看初次分派和工具返回；服务不可用就加载对应回放，并说明是历史轨迹。'
    '暂停在协调者发现缺少 E-VOLTAGE 的时刻，观察它依据新反馈修订计划并把补充读取分给证据角色，随后再汇总。这与后面评审演示不同：此处协调者在正式建议前发现问题，review 模式在草稿审查后退回。'
    '检查 read_supplemental 返回以及计划版本、引用和待人工确认状态。路由由固定规则决定，不称为模型自主选择。结束后返回本段，用一句话说明重新分派的触发依据，控制在四分钟。',
    minutes=4)

add('工作流基线与三个短演示', '短演示 ②：并行分析 Parallel / 证据冲突',
    flow('同一输入', '证据 ∥ 知识', '汇合检查', '保留冲突') +
    bullets('预测：读数或资料适用条件冲突时，由谁处理？',
            '观察：独立返回、时间、来源与合并记录。',
            '验收：不覆盖、不投票定因；明确需复核的条件。') +
    demo_button('parallel', 'conflict'),
    '核对 parallel / conflict，说明冲突是合成场景主动设置，不是声称模型自然犯错。运行或加载相同组合回放。'
    '比较两类产物，问为什么不能采用最后返回的结论。当前 conflict 场景通过核对时间戳解释冲突，保留原始读数与适用条件，不删除旧证据。在汇合处检查和解依据，最终建议仍待人工确认；若时间和条件无法解释冲突，设计上应请求人工复核。'
    '页面逐个播放不能证明后台并行，判断要看图和时间戳。不同异常场景下的单次结果不能用于宣称并行更快或更慢。回到演示页，用一句话描述合并规则。',
    minutes=3)

add('工作流基线与三个短演示', '短演示 ③：评审修订 Review / 缺失电压',
    flow('草稿缺电压', '评审退回', '补充电压', '重新审查通过') +
    bullets('预测：缺 voltage，靠改文字能通过验收吗？',
            '观察：退回理由、补充证据、草稿修订前后。',
            '恢复失败分支：资料仍不可得 → 保留缺失项 → 转人工。') +
    demo_button('review', 'missing'),
    '核对 review / missing，先猜审查会退回什么，再现场运行或加载明确标注的回放。暂停在第一条反馈，读出具体缺失，不能只说质量不好。'
    '当前 missing 缺少 voltage 电压证据 E-VOLTAGE，不是采集时间。先看缺电压的草稿和 review 退回，再看计划 Revision 更新 plan_version 与 revision_rounds，随后 read_supplemental 返回电压记录并追加 observations，重写 draft，最后重新审查通过。'
    '用运行台的修订前后对照核对引用与缺失项，再展开事件 JSON 确认 E-VOLTAGE 来源。missing 可恢复并生成待人工确认的报告；若补充不可得则应转人工，tool_failure 展示工具持续失败的分支。规则评审通过不等于人工批准。完成后返回本段回顾。',
    minutes=4)

add('工作流基线与三个短演示', '基线与三种模式：新增复杂度换来了什么',
    table(['模式', '控制与产物', '适用条件', '风险'], [
        ['workflow 基线', '预设分支、固定验收', '原始固定字段任务', '规则需维护'],
        ['Supervisor', '中央分派、统一汇总', '隔离职责需统一调度', '中央瓶颈、摘要失真'],
        ['并行分工', '独立执行、汇合验收', '独立上下文可同时处理', '冲突、覆盖、部分失败'],
        ['评审—修订', '带理由退回、有限迭代', '独立专业审查责任', '无进展、错误反馈'],
    ]) + p('点击“基线与三种模式”：同一情景、来源、预算与验收。', 'takeaway'),
    '用“基线与三种模式”比较 workflow、supervisor、parallel、review；integrated 留给综合案例。先看基线已能交付什么，再解释新隔离要求带来的分派、汇合和独立审查价值。'
    '核对结束状态、证据覆盖、调用量、修订与耗时；workflow 计划保持 v1、修订为 0，没有 Revision/Dispatch，预设补读不等于重规划。规则模拟成功不证明多 Agent 模型质量提升。并行可能降低墙钟时间，却增加总调用量与合并成本。'
    '保持同一情景、运行来源与预算才可比较，多次运行再谈稳定性。不同异常短演示只用于认识机制，回放不能估算当前机器或模型延迟。',
    layout='compact', minutes=2)

add('综合实战与落地', '综合设计：四角色、一份状态、一个出口',
    flow('协调者<br><small>目标与分派</small>', '证据 ∥ 知识<br><small>独立产物</small>',
         '协调者<br><small>综合建议</small>', '审查者<br><small>通过 / 退回</small>') +
    table(['连接处', '必须带上', '异常出口'], [
        ['分派 → 专家', '上下文、子任务与预算', '拒绝不合法请求'],
        ['专家 → 汇合', '引用、来源、缺失与冲突', '部分成功不伪装完整'],
        ['审查 → 协调 / 结束', '具体反馈与修订计数', '超限停止；通过后待人工确认'],
    ]) + p('图中是逻辑角色；规则模拟节点不自动成为真实 LLM Agent。', 'foot'),
    '在新增上下文、工具权限与专业责任隔离的教学假设下找出三种模式：协调者集中分派，证据与知识独立取数，审查回边有限修订。原始固定字段任务用 workflow 即可；四角色不需要四台服务器或四个模型。'
    '协调者在多个阶段执行仍是一个职责：先安排任务，再综合产物。缺引用可退回修订，缺无法获取的证据应进入待补充或停止，不强行重复生成。'
    '问谁能批准真实车辆操作，答案是图中没有模型角色有此权限。本课只生成建议，人工审批是业务边界，没有实现真实车端控制。让学员给每条箭头说出一个必需字段。',
    layout='compact', minutes=3)

add('综合实战与落地', 'LangGraph API 骨架：独立教学示例',
    split('<h3>状态定义</h3>' + code(LANGGRAPH_DEFINITIONS),
          '<h3>节点、汇合与运行</h3>' + code(LANGGRAPH_WIRING)) +
    p('独立 API 示例：与主实现同用 compile().stream(values)，省略四角色、条件路由与预算。', 'foot'),
    '真实 StateGraph API 骨架可在安装兼容 LangGraph 的环境执行。先看独立 evidence 与 knowledge 字段，再看 START 分两支，最后列表形式的起点边等待双方完成。lambda 相当于返回状态更新的小处理器。'
    '固定字符串只展示机制，review 仅标记待人工，没有实际审查；这不是完整四角色实现。运行台完整版需要协调节点、合成数据工具、条件路由、审查与预算。'
    '没有 checkpointer 或 interrupt 配置，不具备生产断点恢复。请学员指出删掉等待汇合可能有什么风险，再到实际运行台核对图与事件。左右代码依次拼接即可运行，以下提供完整示例，依赖 LangGraph 1.2.11。'
    + '\n\n```python\n' + LANGGRAPH_DEFINITIONS + '\n\n' + LANGGRAPH_WIRING + '\n```',
    ['state'], layout='compact code-slide', minutes=3)

add('综合实战与落地', '扩展设计：未来如何替换为 LLM 决策',
    table(['环节', '当前：规则模拟', '未来扩展：真实 LLM'], [
        ['下一步', '固定条件选择，可重复', '根据目标与证据返回结构化决策'],
        ['工具与数据', '执行合成工单只读工具', '同一运行时校验、执行工具'],
        ['验收', '路径、预算、停止状态', '额外评估格式、波动、费用'],
    ]) + p('当前未实现 LLM 接入，也没有可切换的 Ollama 模式；后端拒绝真实模型选项。', 'takeaway'),
    '替换点是角色决策函数，不是把所有代码交给模型。运行时仍验证工具、预算与权限，模型不能改写约束。'
    '真实 LLM 是未来设计扩展，当前没有模型适配器或 Ollama 运行模式，不能通过填配置直接开启。实现时应记录模型调用，配置失败明确报错，禁止静默回退还宣称真实调用。'
    '规则结果用于教学和编排回归。未来模型扩展还要测试格式错误、工具幻觉和无进展，多次运行观察波动。Ollama 链接仅供接口设计参考，不表示已集成。记录简短决策摘要、工具结果与版本，不要求展示完整内部思维。',
    ['ollama'], layout='compact', minutes=2)

add('综合实战与落地', 'HTTP 集成：Java、前端与客户端如何接入',
    flow('前端 / 客户端', 'Java 业务服务', 'Python 编排', '只读工具') +
    table(['接口示意', '目的', '边界'], [
        ['POST /diagnosis/runs', '提交工单，返回 run_id', 'Java 鉴权；密钥保留服务端'],
        ['GET /diagnosis/runs/{id}', '查询状态、事件和建议', '前端区分运行、回放与待确认'],
        ['POST /diagnosis/runs/{id}/approval', '提交人工决定', '鉴权、绑定建议版本与审计'],
    ]) + p('推荐的生产接口契约；不承诺课堂服务已实现这些路径或真实审批。', 'foot'),
    'Java 负责认证、工单访问权、限流与幂等请求。模型密钥和工具凭据不发到浏览器或客户端。Python 返回结构化状态，不让前端猜中文是否代表完成。'
    '前端可轮询，也可另外设计 SSE 或 WebSocket；逐步播放事件不代表已有实时流。客户端不能把模型文本直接转成车端命令。'
    '审批绑定用户、run_id 与建议版本，避免批准旧内容却执行新内容。本页是架构契约，实际课堂请求路径以服务实现为准；没有生产审批恢复或真实车辆控制。请不同岗位各指出一项自己负责的校验。',
    layout='compact', minutes=3)

add('综合实战与落地', '综合运行台：看清证据、反馈与停止',
    '__DIAGNOSIS_LAB__',
    '前一分钟核对 integrated、SYNTH-REMOTE-001 与规则模拟标签，并区分现场服务和录制回放。所有场景只使用规则决策与实际 LangGraph，没有真实 LLM 模式。选择 normal，花两分钟看协调分派、证据、知识、审查和待人工确认。'
    '接着一分钟选 conflict 或 missing：conflict 核对时间戳后解释差异；missing 经 read_supplemental 补齐电压后修订。先看中文故事线、角色图、当前已观察证据和修订前后，再展开事件 JSON、最终报告与状态。用一分钟选 tool_failure，确认保留错误并以 needs_human 请求人工处理。'
    '再用一分钟选 budget，确认 status=stopped，不伪造成功。最后一分钟对比来源、场景、结束原因与建议。服务不可用时用对应回放，口头和界面同时标明回放，不称为实时 LLM 流。'
    '短演示按钮也复用此页；从短演示跳来只完成对应观察后返回，完整七分钟安排在综合环节。本章此前十一分钟用于架构、代码、扩展边界与 HTTP，合计十八分钟综合演示。通过检查不证明真实诊断正确或生产持久恢复。',
    layout='compact', minutes=7)

add('综合实战与落地', '小组练习：等待客户端上传，再恢复任务',
    '<div class="exercise"><span>5 分钟设计练习 · 尚未实现</span><h3>电压资料不在工具中：请求门店通过客户端上传</h3>'
    '<p>画出暂停 → 保存 → 等待上传 → 校验 → 恢复；不要持续占用请求。</p></div>' +
    bullets('分清客户端、Java 业务服务、编排器与审查者的职责。',
            '保存哪些状态？上传消息怎样关联工单、运行与版本？',
            '重复 / 过期上传、越权、超时分别怎样处理？') +
    p('提交：恢复流程 + 上传消息 + 验收条件；参考答案见讲稿与 README。', 'takeaway'),
    '一分钟个人思考、两分钟结对、一分钟展示、一分钟参考答案。这是新增需求，不能调用现有 read_supplemental 假装等待用户上传；当前 Demo 没有上传接口、持久暂停或恢复实现。无需新增上传 Agent，先用业务工作流落实。'
    '参考解：协调者或审查者发现缺电压，编排器持久保存 case_id、run_id、plan_version、observations、draft、review、missing、剩余预算、恢复节点、upload_request_id 与到期时间，状态 waiting_client_upload，然后结束本次请求。Java 服务发出补充请求，客户端显示要求并上传，业务服务校验工单权限、请求版本和内容，编排器只从待补充节点恢复，再审查报告。'
    '消息示例：{type: client_evidence_uploaded, case_id: SYNTH-REMOTE-001, run_id: run-demo, upload_request_id: upload-1, expected_plan_version: 2, message_id: msg-1, idempotency_key: upload-1-v1, evidence_refs: [upload-file-1]}。身份由登录会话确定，不信任消息自报角色；证据角色核对上传内容与采集时间，审查者只验收建议，不能代替客户上传或批准。'
    '参考验收：数据库唯一键和原子状态转换确保重复消息只恢复一次，返回原处理结果；旧 upload_request_id、旧版本或已结束任务的上传保留审计但不覆盖当前证据。崩溃重启读取持久检查点，保留预算，不重跑已完成步骤；超时、取消、越权或资料仍无效给出明确出口，超时和无法补齐转人工。普通状态表也可实现；选 LangGraph 时另配 checkpointer、thread_id 与 interrupt/resume，并验证重放幂等。',
    layout='compact', minutes=5)

add('综合实战与落地', '交付检查清单：能解释，也能验证',
    table(['检查项', '通过标准'], [
        ['选型与角色', '说明为何用工作流 / 单 / 多 Agent，职责不重复'],
        ['事实与建议', '引用存在、条件清楚，缺失与冲突可见'],
        ['失败与终止', '工具失败、预算耗尽、修订超限均有出口'],
        ['运行与产品边界', '规则模拟明确、运行/回放可辨；建议待人工确认'],
    ]) + p('最小交付：一张协作图、一份消息契约、三条正常/异常轨迹。', 'takeaway'),
    '不要只展示正常路径，至少保存正常、证据异常、预算或工具失败三类样本。各岗位挑一项讲如何测试：后端查状态与权限，前端查引用与反馈，客户端查是否可能误触发实际操作。'
    '当前验收覆盖规则模拟与实际 LangGraph，不以此证明 LLM 能力。未来若扩展模型，须记录模型、提示词和版本并多次运行；一次成功不是稳定性证明。性能比较必须使用同场景、同运行来源。'
    '回到两项目标：能说明何时不需要 Agent，也能设计有独立产物、共享状态和出口的小系统。持久化、审批恢复和真实车端接入是后续独立工程，不由本次教学验收代替。',
    layout='compact', minutes=2)

add('综合实战与落地', '参考资料：推理与协作模式',
    references([
        ('react', '推理与行动交错，理解环境反馈'),
        ('plan', '规划、执行与重规划示例'),
        ('reflexion', '语言反馈如何影响下一次尝试'),
        ('patterns', '工作流、Agent 与协作模式'),
        ('research', '研究系统的经验、收益与代价'),
        ('multi', '多 Agent 模式与上下文边界'),
    ]) + p('论文机制、厂商经验与本课教学实现分别标注，不互相替代证据。', 'foot'),
    '零基础先读 Building effective agents 的工作流与 Agent 区别，再读 ReAct、Reflexion 摘要与核心图。规划示例帮助理解依赖，不必先追全部 API。'
    '研究系统文章属于特定经验，学习其分工、上下文和评估方法，不把效果数字套用到远程诊断。阅读时带着谁决定下一步、依据什么证据、何时停止三个问题。'
    '链接支持继续阅读，不表示课程复现了论文评测或作者生产系统。请学员根据自己最薄弱的一项选择一篇资料作为课后阅读。',
    layout='compact', minutes=1)

add('综合实战与落地', '参考资料：框架与道通远程专家',
    references([
        ('auto', '维护模式、AgentChat 与采用前核对'),
        ('meta', 'Role / Action / Team / SOP 与依赖范围'),
        ('graph', '有状态编排；结合 Graph API 阅读'),
        ('persistence', '检查点配置；结合 Interrupts 理解恢复'),
        ('autel', '远程专家业务：客户发单、专家服务与实时沟通'),
    ]) + p('来源与维护信息核对：2026-09-21。工单、读数、知识条目均为合成教学材料。', 'source-note'),
    '本章最后五分钟用于总结与问答：检查清单两分钟，推理资料导读一分钟，本页两分钟开放提问。先请两位学员各回答何时选单 Agent、如何设置终止，再回答一个迁移问题。工程人员先读 LangGraph overview 和 Graph API，需要恢复时再配置并测试 persistence 与 interrupts。'
    'AutoGen 信息以 2026-09-21 官方 README 核对为准，立项再查；MetaGPT 同时检查 releases 和依赖，不能仅凭 README 判断活跃度。'
    '道通远程专家官方页面提供客户与专家连接、远程诊断、编程、防盗、ADAS、咨询及 VIN、导入报告、发布订单的业务背景，并描述实时语音、文字、视频、电话沟通与服务、连接状态。官方 AI 智能匹配表述未披露 LLM 或多智能体实现。接单前资料初审与专家辅助为本课教学设计；合成 U0121、缺失电压与规则后端不代表厂商自主专家系统。',
    layout='compact', minutes=2)

assert len(slides) == 44
assert sum(minutes for _, minutes in CHAPTERS) == 120
assert sum(slide['minutes'] for slide in slides) == 120
assert all(sum(slide['minutes'] for slide in slides if slide['chapter'] == chapter) == minutes
           for chapter, minutes in CHAPTERS)
assert {slide['chapter'] for slide in slides} == {chapter for chapter, _ in CHAPTERS}
