"""Editable course content. All notes are original teaching text; links are sources."""
from html import escape

SOURCES = {
 'react': ('ReAct · ICLR 2023', 'https://arxiv.org/abs/2210.03629'),
 'reflexion': ('Reflexion · NeurIPS 2023', 'https://arxiv.org/abs/2303.11366'),
 'plan': ('LangChain · Plan-and-Execute', 'https://blog.langchain.com/planning-agents/'),
 'auto': ('AutoGen · 官方仓库', 'https://github.com/microsoft/autogen'),
 'meta': ('MetaGPT · 官方仓库', 'https://github.com/FoundationAgents/MetaGPT'),
 'graph': ('LangGraph · 官方概览', 'https://docs.langchain.com/oss/python/langgraph/overview'),
 'state': ('LangGraph · Graph API', 'https://docs.langchain.com/oss/python/langgraph/graph-api'),
 'multi': ('LangChain · Multi-agent', 'https://docs.langchain.com/oss/python/langchain/multi-agent'),
 'ollama': ('Ollama · Chat API', 'https://docs.ollama.com/api/chat'),
}

def p(text, cls=''):
    return f'<p class="{cls}">{text}</p>'

def bullets(*items):
    return '<ul class="points">' + ''.join(f'<li>{x}</li>' for x in items) + '</ul>'

def code(text):
    return '<pre><code>' + escape(text.strip()) + '</code></pre>'

def flow(*items):
    return '<div class="flow">' + '<span class="arrow" aria-hidden="true">→</span>'.join(
        '<div class="node">'+x+'</div>' for x in items) + '</div>'

def split(left, right):
    return f'<div class="split"><div>{left}</div><div>{right}</div></div>'

def table(headers, rows, cls=''):
    return f'<table class="{cls}"><thead><tr>'+''.join(f'<th>{x}</th>' for x in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'

slides = []
def add(chapter, title, body, notes, sources=(), layout=''):
    slides.append(dict(chapter=chapter, title=title, body=body, notes=notes, sources=list(sources), layout=layout))

add('开场', 'Agent 推理与协作',
    '<div class="cover-title">Agent<br><em>推理与协作</em></div>'
    '<p class="cover-sub">ReAct · 规划与反思 · 多 Agent 系统</p>'
    '<div class="cover-line">一份可运行、可观察、可验证的开发者实战课</div>'
    '<div class="cover-meta">90 分钟 / 中文技术培训 / 含双 Agent Demo</div>',
    '【开场，1 分钟】今天研究 Agent 怎样决定下一步、怎样从工具拿到证据，以及多个角色如何接力完成任务。重点是 ReAct。请学员带着一个问题听：如果某一步失败，我怎样判断问题出在模型决策、工具还是编排？培训默认大家了解 Python 函数与基本 LLM 调用，但不要求使用过任何 Agent 框架。说明课程以同一份合成订单数据贯穿，不把演示样本当作真实业务结论。', layout='cover')

add('开场', '本次培训的学习路径',
    '<div class="agenda">'+''.join(f'<div><span>{n}</span><strong>{title}</strong><small>{time}</small></div>' for n,title,time in [
    ('01','ReAct：看见决策循环','25 min'),('02','规划与反思：让执行可修正','15 min'),
    ('03','多 Agent：组织角色与状态','15 min'),('04','框架选型：比较工程取舍','10 min'),
    ('05','双 Agent：现场运行与验收','15 min')])+'</div>'+p('开场 5 分钟 · 练习与讨论 5 分钟','muted'),
    '【2 分钟】先预告学习结果：能画出 Thought–Action–Observation，能区分局部动作和全局计划，能设计失败修正，能解释三类协作架构，最后能跑通双 Agent 的任务。ReAct 占最多时间，因为它既能独立运行，也可以放进规划执行体系的执行器中。介绍 90 分钟分配；若只有 60 分钟，合并 6–8 页、简讲 14 和 23–24 页，保留完整 Demo。')

add('开场', '贯穿案例：订单分析助手',
    p('给你一份订单 CSV，回答：<b>已完成订单的净销售额是多少？各品类表现如何？</b>','lead')+
    split(table(['字段','业务含义'],[['gross','订单原金额'],['refund','退款金额'],['status','completed / cancelled']]),
    '<h3>验收条件</h3>'+bullets('只统计 <code>completed</code>','净销售额 = <code>gross − refund</code>','保留订单 ID，结论能够复算'))+
    p('数据为合成教学样本，金额单位：人民币。','foot'),
    '【2 分钟】先让学员说出任务里容易遗漏的条件：取消订单是否计入？退款如何处理？净销售额是不是利润？把这些转成可检验的成功标准，而不是只要求生成一段漂亮中文。告知数据有 8 行，但先不公布正确答案；后面用真实工具算出来。强调工具与校验器负责数值，模型可以负责选择动作和解释结果。')

add('ReAct', 'Agent 与预定义工作流',
    table(['','预定义工作流','Agent'],[
        ['下一步由谁决定','开发者预先编排','模型依据状态选择动作'],
        ['适用任务','路径稳定、规则明确','步骤随证据变化'],
        ['执行边界','显式分支与流程','也需要工具、预算与验收边界']])+p('同一个系统可以同时包含固定流程与 Agent 决策。','takeaway'),
    '【2 分钟】先澄清词义：函数叫 Agent 并不自动产生智能；关键在于是否有依据状态作决策的机制。固定的 CSV 计算本身用程序更直接，选它做案例是为了让证据可核对。生产系统经常混合二者，例如先固定鉴权，再让模型选查询工具，最后由确定性规则验收。提问：如果只需要每晚固定汇总订单，真的需要多 Agent 吗？预期回答是不一定。', ['multi'])

add('ReAct', 'Thought–Action–Observation 循环',
    '<div class="react-loop"><div data-phase="0"><span>01</span><h3>Thought</h3><p>根据目标与已有证据<br>选择下一步</p></div>'
    '<b>→</b><div data-phase="1"><span>02</span><h3>Action</h3><p>提交有结构的<br>工具调用请求</p></div>'
    '<b>→</b><div data-phase="2"><span>03</span><h3>Observation</h3><p>读取工具返回的<br>数据或错误</p></div></div>'
    '<div class="return-path">Observation 更新上下文 ↶ 下一轮 Thought</div>'
    '<div class="interactive-line"><button id="reactNext">逐步演示</button><span id="reactExplain" aria-live="polite">点击按钮，观察订单任务的第一轮。</span></div>'+
    p('有足够证据则回答；超预算或无法继续则停止。','takeaway'),
    '【4 分钟，重点】逐次点击按钮。第一次显示决策摘要：不知道字段，先检查；第二次是 inspect({})；第三次得到真实字段列表。再点一次，说明新的 Thought 必须利用 Observation，而不是机械重复最初请求。ReAct 原始论文强调推理与行动交错，行动能访问外部环境，证据反过来修订计划。图中环不是无限循环：右侧必须有成功出口与受控停止出口。可请学员复述三步分别由模型还是运行时负责。', ['react'])

add('ReAct', 'Thought：形成下一步决策',
    '<blockquote>“还不知道 CSV 的实际字段。先检查结构，再决定如何计算。”</blockquote>'+
    bullets('输入：用户目标、已知证据、当前约束','输出：下一步意图与简短决策摘要','判断：为什么这个动作有助于完成任务？')+
    p('课堂展示的是教学决策摘要，不是模型完整内部思维。','foot'),
    '【2 分钟】Thought 的价值是把目标与动作联系起来，不是要求模型输出越长越好的思维文本。现代应用往往只记录可审计的简短说明、动作和证据，不需要暴露完整内部推理。这里的引用是人为编写的教学摘要。区分“应该检查字段”与“字段一定叫 sales”：前者是合理行动意图，后者是还未验证的假设。请学员说出此时已知和未知的内容。', ['react'])

add('ReAct', 'Action：模型请求，程序执行',
    split(code('''{
  "tool": "aggregate",
  "args": {
    "gross_field": "gross",
    "refund_field": "refund",
    "status": "completed"
  }
}'''),'<h3>运行时的责任</h3>'+bullets('校验工具名称与参数','检查权限和执行预算','调用工具并捕获结果','保留可关联的调用记录'))+
    p('生成工具调用 JSON ≠ 工具已经执行成功。','takeaway'),
    '【3 分钟】逐项解释工具名、字段和过滤条件。模型只提出请求，宿主程序负责真正执行。一个完整工具定义不仅有名称，还应包含参数 schema、用途与返回值。本例只允许 inspect、aggregate、report，不接收文件路径，也不执行模型生成的任意代码。问学员：模型回复“我已经读取了 CSV”算不算成功？答案要看实际工具返回与日志。', ['react'])

add('ReAct', 'Observation：把环境事实带回循环',
    split('<h3>成功也是证据</h3>'+code('''{
  "ok": true,
  "fields": ["order_id", "category",
             "gross", "refund", "status"],
  "rows": 8
}'''),'<h3>失败同样是证据</h3>'+code('''{
  "ok": false,
  "error": "字段 sales 不存在",
  "available": ["gross", "refund", "status"]
}'''))+
    p('不能把工具错误改写成成功；外部文本也不能覆盖系统指令。','takeaway'),
    '【3 分钟】这两个 JSON 是精简示意，实际日志可以包含更多字段。成功返回让模型知道能用什么；错误告诉模型当前策略哪里不成立。错误应保留具体原因和恢复所需的信息。外部网页或文档即使写着“忽略规则”，仍然只是待分析数据。Observation 也可能过时、为空或不完整，因此需要来源、时间与状态，而不是把任何工具文本都当作真理。', ['react'])

add('ReAct', '一次完整的 ReAct 轨迹',
    table(['轮次','Thought 摘要','Action','Observation'],[
        ['1','先核实数据结构','inspect({})','8 行；有 gross / refund'],
        ['2','按完成状态计算净额','aggregate(…)','6 笔；净额 ¥2,650'],
        ['3','引用结果形成报告','report({})','报告 + 订单证据'],
        ['结束','验收条件满足','Finish','独立复算通过']],'trace-table')+
    p('决策依赖上一轮返回；最终结果可以追溯到工具证据。','takeaway'),
    '【3 分钟】从上往下讲，明确不是一次 prompt 就凭空生成三个动作。每个动作后都把 Observation 加入状态。公布样本结果：办公 1450，数码 1200，总共 2650。最后一行 Finish 在实现中由确定性校验器批准；模型说“完成”还不够。这里的 report 是确定性工具生成文本，便于核对；真实应用可以让模型写解释，但数值和引用仍应校验。', ['react'])

add('ReAct', '最小控制循环',
    code('''for step in range(MAX_STEPS):
    decision = agent.decide(goal, observations)
    if decision.is_final:
        return validate(decision.answer, evidence)

    call = validate_tool_call(decision.action)
    observation = tools.execute(call, timeout=30)
    observations.append(observation)

return stopped("预算耗尽，尚未完成")''')+
    p('教学伪代码 · 状态更新、工具执行与终止条件由运行时落实。','foot'),
    '【3 分钟】用代码把前三页连接起来。agent.decide 是决策边界，validate_tool_call 是执行边界，observations 是反馈通道。伪代码没有展开异常处理；实际 Demo 捕获工具错误并进入重规划。让学员指出如果忘记 append 会发生什么：模型可能重复相同动作，因为它没有得到新证据。再问，如果去掉 MAX_STEPS，坏模型输出或重复错误可能导致无限消耗。', ['react'])

add('ReAct', '常见失败与停止策略',
    table(['现象','应对动作','结束条件'],[
        ['参数或字段不匹配','返回 schema，修正请求','持续无进展则停止'],
        ['工具暂时不可用','有限重试与退避','达到重试或时间预算'],
        ['相同动作反复出现','检测重复，重新规划','无法获得新证据'],
        ['工具结果不足','补充查询或请求信息','说明缺失，避免编造']])+
    p('完成、失败、受控停止，是不同的状态。','takeaway'),
    '【3 分钟】字段错误通常是策略问题，原样重试没有意义；网络瞬断可能适合退避重试，二者不能混为一谈。对有副作用的工具，重试还需要幂等键或结果核对。演示中的 --max-steps 1 会停止且返回非零退出码，不会生成成功报告。可以把最多工具步数、最多模型调用、总时间与费用都纳入预算。强调这些是工程设计建议，不是 ReAct 论文中自动赠送的功能。', ['react'])

add('ReAct', '判断题：下一步应该做什么？',
    p('工具返回：<code>字段 sales 不存在；实际字段包含 gross、refund</code>。','lead')+
    '<div class="quiz" id="quiz"><button data-answer="a">A　继续用 sales 重试三次</button>'
    '<button data-answer="b">B　结合字段证据修正调用，并重新计算</button>'
    '<button data-answer="c">C　直接回复“销售额大约 3,000 元”</button></div>'
    '<p id="quizFeedback" class="quiz-feedback" aria-live="polite">选择一个答案，再解释它如何利用 Observation。</p>',
    '【2 分钟】先让学员举手或投票，再点选。B 是本例的合理选择，但还需要确认 gross 的业务含义，不能只靠名字相似就换字段。A 没有利用新证据；C 没有计算依据。追问：如果工具只返回“发生错误”呢？恢复会更困难，因此好的工具错误信息是 Agent 能力的一部分。用这页过渡到计划修订：局部动作修正还可以进入更高层的任务计划。', ['react'])

add('规划与反思', 'Plan-and-Execute：先形成全局计划',
    flow('Planner<br><small>分解目标与依赖</small>','Executor<br><small>完成当前子任务</small>','检查结果<br><small>完成 / 重规划</small>')+
    split('<h3>计划回答</h3>'+bullets('有哪些步骤？','步骤依赖什么？','每一步如何验收？'),
          '<h3>执行回答</h3>'+bullets('当前步骤该用哪个工具？','结果是否满足条件？','需要把什么反馈给规划者？')),
    '【3 分钟】ReAct 可以边执行边调整局部行动；Plan-and-Execute 把全局拆解显式提出来。不是任何任务都需要预先写十条计划，一步可完成的事情通常不值得增加规划调用。规划者可以较少调用，执行者可以使用较便宜的模型或确定性工具，但是否更省钱要实测，不能保证。我们的执行 Agent 仍可以采用 ReAct，因此两者不是互斥方案。', ['plan'])

add('规划与反思', '计划需要可执行的结构',
    table(['ID','任务','依赖','完成标准'],[
        ['S1','检查 CSV 结构','—','取得真实字段与行数'],
        ['S2','计算净额与品类汇总','S1','有过滤口径、金额和订单 ID'],
        ['S3','生成经营报告','S2','结论引用工具证据']])+
    code('{"plan_version": 1, "step_id": "S2", "status": "pending", "depends_on": ["S1"]}')+
    p('只有依赖满足的步骤才可执行；计划版本用于关联后续反馈。','foot'),
    '【2 分钟】“分析数据”过于含糊，需要可验证的输出契约。说明 S2 为什么依赖 S1：没有实际字段就容易猜错。S3 为什么依赖 S2：不能先写报告再找数字。表中 depends_on 是生产设计示意，最小 Demo 使用固定顺序和已完成步骤列表实现同样的前置关系。并发任务可用 DAG，但这里保持串行有助于课堂观察。', ['plan'])

add('规划与反思', '什么时候重新规划？',
    '<div class="revision"><div><span>PLAN v1</span><h3>S2：按 sales 汇总</h3><p>未验证的字段假设</p></div>'
    '<b>→</b><div><span>OBSERVATION</span><h3>sales 不存在</h3><p>环境反馈推翻原假设</p></div>'
    '<b>→</b><div><span>PLAN v2</span><h3>S2：按 gross − refund</h3><p>保留已完成的 S1</p></div></div>'+
    bullets('原假设被证据推翻','子任务产物不满足验收条件','目标或约束发生变化'),
    '【2 分钟】此页是故障场景的简化表示。强调不必全部从头再来：已检查的字段可以继续使用，但如果数据源发生变化就要重新检查。计划修订要更新版本，保留失败原因，避免执行器仍按旧计划执行。不要每完成一次工具调用就重规划，否则可能比单 Agent 更昂贵；根据依赖、风险和反馈选择检查点。', ['plan'])

add('规划与反思', 'Reflexion：把反馈变成可用经验',
    flow('Actor<br><small>完成一次尝试</small>','Evaluator<br><small>返回具体反馈</small>','Reflection<br><small>总结可执行修正</small>')+
    '<div class="memory-line">反思写入 episodic memory → 下一次尝试读取</div>'+
    p('<b>更新的是上下文中的语言记忆，不是模型权重。</b>','lead')+
    p('反馈可以来自测试、环境得分、工具错误或其他评价信号。','muted'),
    '【3 分钟】按原论文介绍 Actor、评价与自我反思之间的分工。Reflexion 的关键是反思文本被保留，并实际影响下一次尝试；不是在同一段回答后附加“我会更努力”。语言反馈可来自外部，也可以内部模拟，但可靠的外部校验通常更容易审计。我们把反思职责放在规划 Agent，把评价放在确定性工具，仍然只有两个 Agent 角色。Demo 是简化教学实现，不是完整复现论文实验。', ['reflexion'])

add('规划与反思', '有用的反思必须改变下一次行动',
    split('<div class="weak"><h3>信息不足的反思</h3><blockquote>“这次失败了，下次认真一点。”</blockquote><p>没有原因、证据或可执行修正。</p></div>',
          '<div class="strong"><h3>可执行的反思</h3><blockquote>“把 sales 当成字段是未经验证的假设。下次依据 inspect 的实际字段，用 gross − refund 计算。”</blockquote></div>')+
    p('检查反思质量：失败点 → 支持证据 → 修正动作 → 再次验收。','takeaway'),
    '【3 分钟】让学员比较两段反思。第二段明确错误发生在哪里，引用了哪一条证据，下一次行动怎样改变。反思也可能错误，因此不能把所有自我总结永久写进全局记忆；应标注任务范围、时间、证据与验证状态。这里的 memory 只属于一次运行，避免把一个数据集的字段映射当成所有数据集的规则。课后练习可以让学员写一条退款重复扣除的反思。', ['reflexion'])

add('规划与反思', '三种机制可以嵌套组合',
    '<div class="nest"><h3>Plan-and-Execute <small>全局：目标 → 子任务 → 验收</small></h3>'
    '<div><h3>ReAct <small>局部：Thought → Action → Observation</small></h3>'
    '<p>执行当前子任务，随工具证据选择下一步</p></div>'
    '<footer>失败反馈 → Reflexion → 记忆 → 修订计划或下一次尝试</footer></div>'+
    p('规划提供结构，ReAct 连接环境，Reflexion 保留可复用的失败经验。','takeaway'),
    '【2 分钟】用嵌套图收束三个概念。问学员：能否只用 ReAct？可以。能否让计划执行器是普通程序？可以。反思是否总能提高效果？不保证，错误反思会强化坏策略，仍需实验与校验。强调这是一种组合方案，不是必须同时使用全部机制的标准答案。接下来把规划与执行职责拆给两个角色，就自然进入多 Agent。', ['react','plan','reflexion'])

add('多 Agent', '什么时候值得拆成多个 Agent？',
    split('<h3>拆分的理由</h3>'+bullets('知识、工具或权限边界不同','子任务可独立交付与验收','需要不同上下文或评价视角'),
          '<h3>需要付出的代价</h3>'+bullets('更多模型调用与上下文传递','协调、重试与状态合并','更难定位错误与控制延迟'))+
    p('先证明单 Agent 的瓶颈，再用多 Agent 解决具体问题。','takeaway'),
    '【2 分钟】拆角色不是给相同 prompt 改几个名字。可以举客服检索与退款执行具有不同权限、研究与审稿具有不同上下文的例子。两名 Agent 可以使用同一个底层模型，差别来自指令、工具和状态；也可以使用不同模型。额外角色能改善任务隔离，但会增加 token、延迟和错误面。这里的选择建议是工程判断，不是保证性能提升的结论。', ['multi'])

add('多 Agent', 'Supervisor：集中分派与汇总',
    '<div class="topology"><div class="top-node">Supervisor<br><small>分派任务 · 判断完成 · 汇总结果</small></div>'
    '<div class="tree-line">↓<span>↓</span>↓</div><div class="leaves"><div>研究 Agent</div><div>数据 Agent</div><div>写作 Agent</div></div></div>'+
    split(p('<b>适合：</b>任务分工明确、需要统一出口。'),p('<b>代价：</b>中央决策可能成为瓶颈；汇总时可能丢失细节。'))+
    p('返回结构化产物和证据引用，减少只靠对话转述。','foot'),
    '【3 分钟】监督者知道有哪些专家，将任务路由给合适角色。专家可以作为工具被调用，也可以经消息队列返回结果。图中所有叶子都回到 Supervisor，强调控制权集中。用订单例子说：规划者分派计算，执行者返回数据，规划者再决定是否结束。询问如果监督者失效如何恢复：持久化任务状态和检查点比只存一段聊天记录更可靠。', ['multi'])

add('多 Agent', '层次化：把团队作为协作单元',
    '<div class="hierarchy"><div class="top-node">总协调 Agent</div><div class="teams"><div><h3>研究组长</h3><p>检索 Agent　↔　核验 Agent</p></div><div><h3>交付组长</h3><p>编码 Agent　↔　测试 Agent</p></div></div></div>'+
    bullets('上层分解跨团队目标，下层处理领域细节','团队间交换产物契约，减少传递完整历史','限制深度与调用预算，避免逐层放大成本'),
    '【3 分钟】层次化可以看作监督模式的递归组合，不需要把它当成完全独立的神秘架构。优点是隔离上下文与复杂度，代价是多层摘要可能丢失约束。每层都需要明确输入、输出和失败上报机制。让学员思考为什么“总经理、经理、主管、员工”四层模型链未必比两层好：层次必须对应实际任务边界。', ['multi'])

add('多 Agent', 'Swarm：通过交接转移控制权',
    flow('接待 Agent','领域 Agent','处理 Agent')+
    '<div class="handoff-label">handoff = 目标角色 + 当前任务 + 必要上下文 + 返回约定</div>'+
    split('<h3>适用场景</h3>'+p('下一位专家随对话与任务状态变化，例如多领域服务。'),
          '<h3>设计重点</h3>'+p('限制交接次数，定义状态归属，避免 A ↔ B 循环转交。'))+
    p('此处 Swarm 指协作模式；不等同于某个同名 SDK，也不表示必须全连接或并行。','foot'),
    '【2 分钟】Swarm 在业界的用法并不完全统一，此处聚焦去中心化的交接模式。和 Supervisor 每次回中央不同，当前 Agent 可以决定把控制权交给下一位。举例接待者识别是退款问题后交给退款角色。强调交接对象、任务摘要、证据引用与返回条件必须明确；“大家互相聊天”不等于能完成任务。', ['multi'])

add('多 Agent', 'Agent 间通信：用消息契约接力',
    split(code('''{
  "run_id": "run-01",
  "task_id": "S2",
  "from": "executor",
  "to": "planner",
  "plan_version": 1,
  "status": "failed",
  "error": "unknown field: sales",
  "evidence_ref": "E09"
}'''),'<h3>接收方应该知道</h3>'+bullets('这是哪次运行、哪个任务？','对应哪个计划版本？','结果、错误和证据在哪里？','应继续、修订还是停止？')),
    '【2 分钟】这是通用消息契约示意，不是某个框架的固定 API。run_id 把整次运行关联起来，task_id 关联步骤，plan_version 避免过期结果覆盖新计划。跨进程时还要考虑重复消息、ack、幂等和超时；同一进程也应该保留清楚的接口。Demo 的 events 用 run_id、step_id 和 plan_version 表达同类关系，actor 字段记录来源。', ['multi'])

add('多 Agent', '共享状态：先定义谁能写什么',
    table(['状态字段','主要写入者','合并或更新原则'],[
        ['plan / plan_version','规划 Agent','以新版本替换，保留事件历史'],
        ['observations / artifacts','执行运行时','追加证据，避免覆盖其他任务'],
        ['reflection memory','规划 Agent','记录反馈、修正与适用范围'],
        ['status / verified','调度器与校验器','统一结束条件，校验后才完成']])+
    p('并发写入同一字段时，需要 reducer、版本检查或锁；聊天记录不替代状态模型。','takeaway'),
    '【3 分钟】指出 Demo 是串行执行，不声称展示了分布式一致性。表格说的是逻辑归属：模型提出内容，宿主程序验证后真正写入。LangGraph 可用 reducer 定义状态更新，但 reducer 不是万能锁，外部数据库副作用仍要自己设计一致性。举例两个 Agent 同时生成报告路径，若简单覆盖就会丢失结果；用 task_id 到产物的映射比一个共享字符串更稳妥。', ['state'])

add('框架选型', 'AutoGen / MetaGPT / LangGraph',
    table(['维度','AutoGen','MetaGPT','LangGraph'],[
        ['核心抽象','Agent、消息、团队','Role、Action、SOP','State、Node、Edge'],
        ['常见用途','对话式团队与事件协作','按角色组织复杂交付','显式状态与可恢复编排'],
        ['需重点掌握','终止、路由、API 代际','角色产物与流程约束','状态更新、分支与检查点'],
        ['选型代价','维护现状与迁移路径','框架流程和依赖适配','显式编排带来更多设计工作']],'compare')+
    p('核对日期：2026-09-10。AutoGen 官方仓库已标注维护模式，新项目建议评估 Microsoft Agent Framework。','source-note'),
    '【4 分钟】逐列讲抽象，不做没有实测的速度和质量排名。AutoGen 的 Core 提供消息和运行时，AgentChat 提供更高层的团队 API；不要混用老版 0.2 示例与新 AgentChat 写法。MetaGPT 以软件团队角色和 SOP 著称，也有其他用例，不是只能写软件。LangGraph 是较低层的有状态编排基础设施，可独立于 LangChain 使用。当前 AutoGen 仓库的维护模式信息会影响新项目选择，因此必须现场说明，并建议开课前再次核对。', ['auto','meta','graph'])

add('框架选型', '按照项目约束做选择',
    '<div class="selection"><div><strong>显式状态、分支、暂停恢复</strong><span>优先评估 LangGraph；设计检查点与副作用幂等。</span></div>'
    '<div><strong>角色驱动、SOP 与交付产物</strong><span>评估 MetaGPT；确认流程适配与依赖环境。</span></div>'
    '<div><strong>已有 AutoGen 系统或教学研究</strong><span>理解当前 API；新项目同步评估官方后继框架。</span></div></div>'+
    p('固定、短小、低变动任务，也可以直接使用函数与普通工作流。','takeaway'),
    '【3 分钟】这页是工程建议，不是框架官方保证。先问项目是否需要暂停恢复，再问业务是否已存在稳定 SOP，再看已有代码和团队能力。AutoGen 仍值得理解，但不应忽略维护现状。避免因为演示用了两个角色就要求整个生产系统都上多 Agent。我们现场 Demo 用标准库显式编排，目的在于看清机制；迁移到框架时，先映射状态、节点、边与检查点。', ['auto','meta','graph'])

add('框架选型', '落地前的五个检查点',
    '<ol class="checklist"><li><b>正确性</b><span>有可复算的结果和独立验收</span></li>'
    '<li><b>可控性</b><span>工具白名单、参数验证、权限边界</span></li>'
    '<li><b>可终止</b><span>轮次、时间、费用与无进展阈值</span></li>'
    '<li><b>可观察</b><span>任务、动作、证据与计划版本可关联</span></li>'
    '<li><b>可恢复</b><span>检查点、幂等与部分成功处理</span></li></ol>',
    '【3 分钟】把框架特性翻译成团队需要验收的行为。给出一个对照：有日志不代表日志可关联，有 checkpointer 不代表外部写入可安全重复，有多个 Agent 不代表有独立验证。Demo 将前四项做成可观察的最小行为，第五项讨论设计并保留轨迹回放，但不宣称具备生产级断点续跑。课后作业可以补充持久化状态和恢复操作。')

add('现场 Demo', '双 Agent：规划与执行的职责边界',
    flow('规划 Agent<br><small>计划 + 反思 + 修订</small>','共享任务状态<br><small>计划版本 / 证据 / 记忆</small>','执行 Agent<br><small>当前步骤 + 工具选择</small>')+
    code('''python demo/server.py
# 浏览器打开 http://127.0.0.1:8765

# 也可直接在终端运行：
python demo/agents.py --inject-failure''')+
    p('默认：规则模拟模型决策 + 真实 CSV 工具执行。可选 Ollama 模式接入本地真实模型。','source-note'),
    '【4 分钟，开始 Demo】先向观众明确模式，不能把规则模拟说成真实 LLM 调用。默认模式让工具、状态与失败路径稳定可复现；规划和执行决策由规则产生。若预先安装了 Ollama 模型，可用 README 中的真实模式命令，两个角色使用不同指令和上下文。浏览器现场运行调用本地 Python，同一份代码也可以在终端执行。先展示 orders.csv，再指出 PlannerAgent、ExecutorAgent、ToolBox 与 run 四个边界。')

add('现场 Demo', '现场运行：观察一次失败与修正',
    '<div class="demo-controls"><label><input id="inject" type="checkbox" checked> 注入一次字段错误</label>'
    '<button id="runDemo" class="primary">运行 Python Demo</button><button id="replayDemo">加载教学回放</button>'
    '<label class="file-button">导入轨迹<input id="traceFile" type="file" accept=".json,application/json"></label></div>'
    '<p id="demoStatus" class="demo-status" role="status">尚未运行。直接打开 HTML 时可使用已验证轨迹回放。</p>'
    '<div class="demo-layout"><div class="event-list" id="eventList"></div><div class="event-detail">'
    '<div id="eventHeading">选择或逐步播放事件</div><pre id="eventPayload">运行后查看计划、动作、Observation 与反思。</pre></div></div>'
    '<div class="demo-bottom"><button id="stepDemo" disabled>下一事件</button><button id="playDemo" disabled>自动播放</button>'
    '<button id="downloadTrace" disabled>下载轨迹</button><span id="eventCounter">0 / 0</span></div>',
    '【8 分钟】点击运行，说明页面会在 Python 完成后显示完整轨迹，逐步播放是回放，不是实时 token 流。先读 Plan v1，再点 Thought、Action 和 Observation。到 Fault 事件时暂停：这是人为注入的 sales 字段错误，不是声称模型自然犯了错。继续到 Reflexion，看失败点与修正，然后 Plan v2；S1 已完成，所以只剩 S2、S3。最后看 Finish 的 verified=true。取消注入再运行，对比正常路径没有反思。若服务不可用，点击教学回放，页面会明显标注为已录制轨迹。不要把回放当作刚刚运行。')

add('现场 Demo', '结果验收与代码定位',
    '<div class="numbers"><div><small>已完成订单</small><strong>6 <i>笔</i></strong></div><div><small>净销售额</small><strong>¥2,650</strong></div><div><small>办公 / 数码</small><strong>1,450 <i>/</i> 1,200</strong></div></div>'+
    table(['代码入口','现场查看什么'],[['PlannerAgent.plan()','失败反馈如何形成反思与新计划'],['ExecutorAgent.decide()','当前步骤如何选择工具'],['ToolBox.call()','过滤、退款、字段校验如何执行'],['run() / verify()','状态如何流转，结果如何独立复算']])+
    p('试一试：<code>python demo/agents.py --max-steps 1</code> → 受控停止，不输出成功报告。','foot'),
    '【3 分钟】独立复算办公：500 + (600−150) + 500 = 1450；数码：(800−100) + 400 + (200−100) = 1200。取消订单 900 和 200 不计入。强调净销售额不是利润，没有成本就不能谈利润，没有对比期就不能说增长。打开输出 JSON，查看 plan_version、memory、events 和 verified。最后执行预算耗尽命令，说明正常停止和成功不是一回事。')

add('练习与讨论', '把机制迁移到你的任务',
    '<div class="exercise"><span>课后练习</span><h3>加入“地区维度”，并让错误可以被定位</h3>'+
    '<p>扩展数据与验收条件 → 调整计划 → 添加工具参数 → 测试失败修正</p></div>'+
    bullets('什么步骤值得成为独立 Agent？','哪些证据必须写进共享状态？','如果评价器也错了，怎样避免错误反思？')+
    p('练习说明与参考解法见 README；先定义成功标准，再增加角色。','takeaway'),
    '【3 分钟】给出 15–20 分钟的课后动手题，不要求课堂全部完成。增加 region 字段后，按地区汇总净额；故意请求不存在的 area 字段，要求错误指向具体参数。验收应该断言地区合计仍等于 2650，并核对订单证据。参考答案不是“再加一个 Agent”，而是先扩展工具、计划和校验。讨论评价器若只检查文本是否包含数字，就可能放过错误的统计口径。')

add('参考资料', '继续阅读与复习',
    '<div class="references">'+''.join(f'<a href="{SOURCES[k][1]}" target="_blank" rel="noopener">'
    f'<span>{i:02}</span><div><strong>{SOURCES[k][0]}</strong><small>{desc}</small></div><b>↗</b></a>' for i,(k,desc) in enumerate([
    ('react','推理与行动交错的原始论文'),('reflexion','语言反馈、反思与情景记忆'),('plan','规划者与执行器的架构示例'),
    ('auto','当前维护状态、AgentChat 与迁移提示'),('meta','角色、Action 与 SOP'),('graph','状态图、持久执行与人工介入')],1))+'</div>'+
    p('资料核对：2026-09-10 · 论文机制、框架特性与本课程工程建议已区分。','foot'),
    '【2 分钟】最后请学员用三句话复述：ReAct 用环境证据推动下一步；规划把任务与验收显式化；反思让失败经验影响后续尝试。多 Agent 是组织方式，框架是实现工具。引导先读 ReAct 和 Reflexion 摘要，再读官方框架概览。提醒框架维护状态会变化，上课前再次核对 AutoGen 仓库。交付目录中的 sources.md 提供完整链接，speaker-notes.md 可作为备课讲稿。', ['react','reflexion','plan','auto','meta','graph'])

assert len(slides) == 32
