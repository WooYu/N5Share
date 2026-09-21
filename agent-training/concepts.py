"""Editable, accessible teaching diagrams placed before the seven demos."""
from html import escape


def node(x, y, width, title, *details, height=92, tone='blue'):
    colors = {'blue': ('#edf3fb', '#215bea'), 'green': ('#e4f6ef', '#087f79'), 'amber': ('#fff4df', '#a56812')}
    fill, stroke = colors[tone]
    center = x + width / 2
    body = f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    title_y = y + (31 if details else height / 2 + 8)
    body += f'<text x="{center}" y="{title_y}" text-anchor="middle" class="diagram-title">{escape(title)}</text>'
    for i, detail in enumerate(details):
        body += f'<text x="{center}" y="{y + 60 + i * 27}" text-anchor="middle" class="diagram-copy">{escape(detail)}</text>'
    return body


def arrow(stage, points, label='', x=None, y=None, feedback=False):
    color = '#087f79' if feedback else '#6d87a5'
    body = f'<path d="{points}" fill="none" stroke="{color}" stroke-width="3" marker-end="url(#arrow-{stage}-{int(feedback)})"/>'
    if label:
        body += f'<text x="{x}" y="{y}" text-anchor="middle" class="diagram-label">{escape(label)}</text>'
    return body


def svg(stage, description, body, height=310):
    markers = ''.join(f'<marker id="arrow-{stage}-{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>' for i, color in enumerate(('#6d87a5', '#087f79')))
    return f'<svg class="concept-diagram" viewBox="0 0 1200 {height}" role="img" aria-labelledby="concept-title-{stage} concept-desc-{stage}"><title id="concept-title-{stage}">能力概念图 {stage}</title><desc id="concept-desc-{stage}">{escape(description)}</desc><defs>{markers}</defs>{body}</svg>'


def concept(stage):
    if stage == 1:
        title = '概念 ①：LLM 根据上下文生成回答'
        definition = '大语言模型把你的需求和已有信息，组织成一段回答或一份建议。'
        drawing = svg(1, '用户需求与已提供的信息进入大语言模型，模型生成出游建议。当前天气和报价还需要另行核实。',
            node(20, 78, 300, '输入：需求与上下文', '两大一小，周六半日', '总预算 300 元', height=120) +
            arrow(1, 'M 326 138 H 434', '交给模型', 380, 113) +
            node(440, 78, 300, 'LLM：生成内容', '理解要求，组织语言', '根据已有上下文作答', height=120, tone='green') +
            arrow(1, 'M 746 138 H 854', '生成', 800, 113) +
            node(860, 78, 320, '输出：候选建议', '“可以考虑公园或博物馆”', '天气与费用还待核实', height=120) +
            '<text x="600" y="260" text-anchor="middle" class="diagram-label">看到流畅的回答，还需要核对它依据了哪些事实。</text>')
        example = '先看模型能否说清需求，再看它是否主动说明缺少天气与报价。'
        takeaway = '本阶段解决：把自然语言需求变成可读的建议。'
        notes = '先从左到右读图。用户提供同行人数、时间与预算，模型结合这些上下文生成建议。它可能利用训练中学到的知识，但没有自动获得今天的天气和实时价格。能生成自然语言不代表已完成查询，也不保证事实正确。用“先给一个想法，出发前还要核实”帮助零基础学员理解。下一页只观察回答及其对未知信息的说明，不把模型随机措辞作为好坏标准。'
        sources = ['patterns']
    elif stage == 2:
        title = '概念 ②：RAG 先查资料，再参考资料回答'
        definition = '检索增强生成：从资料库找出相关片段，把片段与问题一起交给模型。'
        drawing = svg(2, '问题用于检索资料库，命中资料与原问题共同交给模型，模型生成带来源的回答。资料库不等于实时工具。',
            node(20, 160, 230, '用户问题', '雨天如何安排出游？') +
            node(290, 20, 265, '资料库', 'D01：雨天选室内', 'D02：费用要算全', height=112) +
            arrow(2, 'M 256 206 H 294') +
            node(300, 160, 255, '检索：找到相关片段', '本例命中 D01、D02', tone='green') +
            arrow(2, 'M 430 137 V 155') +
            arrow(2, 'M 560 206 H 650', '一起输入', 605, 183) +
            node(655, 160, 220, '模型生成回答', '问题＋命中资料') +
            arrow(2, 'M 881 206 H 940') +
            node(945, 160, 235, '回答附上来源', '“选室内 [D01]”') +
            '<text x="840" y="75" text-anchor="middle" class="diagram-label">资料更新后，检索结果也能随之更新。</text>' +
            '<text x="840" y="107" text-anchor="middle" class="diagram-label">检索本身不会修改模型权重。</text>')
        example = '模型现在有了“雨天选室内”的依据；本周是否下雨、各场馆多少钱，还要继续查询。'
        takeaway = '比上一阶段多了：可引用的外部资料。'
        notes = 'RAG 可以类比开卷回答。问题先交给检索程序，从资料库选取相关片段；程序将片段、来源编号和原问题一并提供给模型，模型再回答。库大时不必把整库塞进提示词。解释两条课程资料D01和D02，特别区分规则资料与当下天气、具体费用。引用使依据可追踪，但检索可能漏掉资料，资料也可能过期，仍要检查来源是否支持结论。本课真实模式使用关键词检索，同样能演示“检索后生成”的机制，不要求一开始就讲向量数据库。'
        sources = ['patterns']
    elif stage == 3:
        title = '概念 ③：工具调用让模型请求程序办事'
        definition = '模型决定调用什么、传什么参数；宿主程序负责检查与执行，再把结果交回模型。'
        drawing = svg(3, '模型提出工具名称和参数，宿主程序验证并调用工具。工具返回数据或错误，宿主把结果交还模型生成回答。',
            node(20, 35, 300, '模型提出请求', 'calculate_cost(P03)') +
            arrow(3, 'M 326 81 H 434', '名称＋参数', 380, 58) +
            node(440, 35, 300, '宿主程序', '检查参数、权限与上限', tone='green') +
            arrow(3, 'M 746 81 H 854', '执行', 800, 58) +
            node(860, 35, 320, '费用工具', '计算门票＋交通＋餐费') +
            arrow(3, 'M 1020 133 V 188') +
            node(860, 195, 320, '工具返回', '90＋40＋80＝210 元') +
            arrow(3, 'M 854 241 H 746', '结果或错误', 800, 218, feedback=True) +
            node(440, 195, 300, '宿主记录返回值', '保留调用参数和结果', tone='green') +
            arrow(3, 'M 434 241 H 326', '交回模型', 380, 218, feedback=True) +
            node(20, 195, 300, '模型结合结果回答', '“总费用为 210 元”'))
        example = '“我查过了”需要对应真实的调用记录；天气查询、费用计算都由程序实际执行。'
        takeaway = '比 RAG 多了：请求程序查询、计算或执行允许的操作。'
        notes = '按上排从左到右、下排从右到左读图。模型不会凭一句话直接操作工具，它先返回工具名称和参数，宿主程序核验后执行，再回传数据或错误。模型得到Observation后才能据此继续。RAG侧重查找已有资料，工具可访问接口或执行计算；检索也可以封装成一种工具，两者可以组合。本课程所有工具只读合成数据，不订票不付款。已有接口也必须有参数校验、权限和调用上限。下一页重点找出请求、执行、返回三个位置，避免把模型输出工具JSON当作已经执行成功。'
        sources = ['patterns']
    elif stage == 4:
        title = '概念 ④：ReAct 根据每次反馈决定下一步'
        definition = '每获得一次观察结果，就重新判断下一步行动，直到能交付或必须停止。'
        drawing = svg(4, 'Thought简短判断、Action实际行动、Observation观察结果形成循环。观察后检查能否交付，不能交付则继续判断；成功、无解或达到上限时结束。',
            node(20, 30, 250, 'Thought · 判断', '还缺什么证据？') +
            arrow(4, 'M 276 76 H 324') +
            node(330, 30, 245, 'Action · 行动', '请求费用计算工具') +
            arrow(4, 'M 581 76 H 624') +
            node(630, 30, 250, 'Observation', '观察：自然馆 310 元') +
            arrow(4, 'M 886 76 H 929') +
            node(935, 30, 245, '能交付或应停止？', '检查目标与执行上限', tone='green') +
            arrow(4, 'M 990 128 V 196 H 145 V 128', '否：把新证据带入下一轮判断', 550, 181, feedback=True) +
            arrow(4, 'M 1120 128 V 240', '是', 1150, 197) +
            node(870, 245, 310, '返回结果或说明无解', height=52, tone='green') +
            '<text x="390" y="266" text-anchor="middle" class="diagram-label">本例：310 元超预算，再查 210 元的候选。</text>')
        example = '工具调用给出一次结果；ReAct 继续用结果决定“还要查什么”。'
        takeaway = '比单次工具调用多了：观察后的决策循环。'
        notes = 'Thought在课堂上只展示简短决策摘要，不要求也不展示模型内部完整思维。Action是模型提出的行动，经宿主实际执行；Observation是工具回传的证据。根据310元超预算这条观察，下一轮可以改查其他候选。满足条件后结束，没有候选、工具持续失败、预算或步数用完也必须结束。ReAct不要求每个任务都出现同样的调用顺序。这个小任务的固定规则也能写成工作流，课堂用它来展示观察怎样影响下一次判断。'
        sources = ['react']
    elif stage == 5:
        title = '概念 ⑤：Plan-and-Execute 先规划，再执行'
        definition = '先把目标拆成带依赖的任务清单，再让执行器按计划完成，并逐项记录结果。'
        drawing = svg(5, '规划者把出游目标拆成查天气与目录、筛选场馆、核算费用、验收四项任务。执行器按这些依赖执行，计划和实际进度分开记录。',
            node(20, 30, 235, '规划者', '拆任务、标依赖', '说明怎样算完成', height=120, tone='green') +
            arrow(5, 'M 261 88 H 322', '计划', 290, 64) +
            node(330, 40, 185, '① 收集资料', '天气＋候选') +
            arrow(5, 'M 521 86 H 550') +
            node(555, 40, 185, '② 筛选场馆', '依赖①的结果') +
            arrow(5, 'M 746 86 H 775') +
            node(780, 40, 180, '③ 核算费用', '依赖②的候选') +
            arrow(5, 'M 966 86 H 995') +
            node(1000, 40, 180, '④ 验收建议', '核对预算与证据') +
            arrow(5, 'M 750 138 V 196', '把计划交给执行器', 900, 173) +
            node(330, 203, 850, '执行器：按依赖执行，记录实际结果', '已完成的证据保留；失败或条件变化时反馈给规划者', height=93) +
            '<text x="130" y="224" text-anchor="middle" class="diagram-label">先有任务清单</text>' +
            '<text x="130" y="258" text-anchor="middle" class="diagram-label">再看实际进度</text>')
        example = '先查天气与场馆，再筛选和算总价；只写出计划，还不能宣布任务完成。'
        takeaway = '比 ReAct 多了：执行前可检查的全局计划与任务依赖。'
        notes = '先指规划者，再沿四项任务读依赖。规划的产物是任务清单，不是最终答案。天气和目录可以独立查询，但筛选需要前面的结果，总价需要候选，最终建议需要经过验收。执行器可以是普通函数，也可以在子任务内部使用ReAct。规划与执行分开后，学员能先检查是否漏了费用或验收条件，再看执行进度。遇到失败时可以调整受影响步骤，保留仍有效的证据。下一页观察模型先生成了什么计划，再对照实际执行了哪些步骤。'
        sources = ['plan']
    elif stage == 6:
        title = '概念 ⑥：Reflexion 把失败反馈变成改进动作'
        definition = '在规划执行之后记录“哪里错、下一次怎么改”，再把这份反思带入新的尝试。'
        drawing = svg(6, '计划v1执行后产生失败反馈，反思把问题变成具体修改动作，形成计划v2并重新执行验收。反思保存在上下文中，不更新模型权重。',
            node(20, 25, 250, '计划 v1 与初次尝试', '“公园，费用 100 元”', '教学错误草稿', height=118) +
            arrow(6, 'M 276 84 H 324') +
            node(330, 25, 245, '执行结果接受验收', '漏算 80 元餐费', '雨天不应选户外', height=118, tone='amber') +
            arrow(6, 'M 581 84 H 624') +
            node(630, 25, 250, 'Reflexion · 反思', '先核对天气', '再把三项费用算全', height=118, tone='green') +
            arrow(6, 'M 886 84 H 929') +
            node(935, 25, 245, '计划 v2', '筛选室内候选', '核算后重新验收', height=118) +
            arrow(6, 'M 1058 149 V 216 H 452 V 149', '按修订计划再执行，检查是否真的改好', 730, 199, feedback=True) +
            '<text x="600" y="279" text-anchor="middle" class="diagram-label">300 元可选博物馆 210 元；200 元仍无解，应说明并停止。</text>')
        example = '反思记录是“下次执行的提醒”，会进入后续上下文，不会直接改变模型权重。'
        takeaway = '与规划执行组合：计划 → 执行 → 反馈 → 反思 → 修订 → 再验收。'
        notes = '先说清初次失败草稿是教学主动注入的样本，不能声称模型必然犯这个错误。Reflexion把失败反馈整理为可执行的后续指令，例如先验证天气、费用必须包含餐费，再将它用于计划v2和新的执行。Reflexion不是重复问一次，也不是仅修改语气，更不是现场训练模型权重。这个简化演示强调反馈进入后续上下文，并由程序再次核对是否改好。没有新证据、同一错误反复出现或无可行候选时，应停止而非无限自我修改。'
        sources = ['plan', 'reflexion']
    elif stage == 7:
        title = '概念 ⑦：多 Agent 按职责协作'
        definition = '不同角色各自处理任务，再通过消息交付结果；共享状态保存大家共同认可的进度与证据。'
        body = '<text x="195" y="30" text-anchor="middle" class="diagram-title">Supervisor · 主管</text>'
        body += '<text x="600" y="30" text-anchor="middle" class="diagram-title">层次化 · 分层管理</text>'
        body += '<text x="1000" y="30" text-anchor="middle" class="diagram-title">Swarm · 按需交接</text>'
        body += node(90, 60, 210, '主管', height=54, tone='green')
        body += arrow(7, 'M 140 120 V 151 H 95 V 177') + arrow(7, 'M 250 120 V 151 H 295 V 177')
        body += node(20, 185, 155, '天气角色', height=56) + node(220, 185, 155, '费用角色', height=56)
        body += '<text x="195" y="287" text-anchor="middle" class="diagram-label">统一分派，结果交回主管</text>'
        body += node(505, 60, 190, '总主管', height=48, tone='green')
        body += arrow(7, 'M 550 114 V 128 H 490 V 140') + arrow(7, 'M 650 114 V 128 H 710 V 140')
        body += node(415, 146, 150, '出游组长', height=48) + node(635, 146, 150, '预算组长', height=48)
        body += arrow(7, 'M 490 200 V 222') + arrow(7, 'M 710 200 V 222')
        body += node(415, 230, 150, '天气角色', height=48) + node(635, 230, 150, '费用角色', height=48)
        body += node(890, 60, 220, '天气角色', height=48)
        body += arrow(7, 'M 1000 114 V 143', '交接', 1070, 135)
        body += node(890, 150, 220, '费用角色', height=48, tone='green')
        body += arrow(7, 'M 1000 204 V 230', '交接', 1070, 224)
        body += node(890, 237, 220, '汇总角色', height=48)
        drawing = svg(7, '主管模式由主管分派天气与费用角色并收回结果；层次化由总主管管理组长再管理专业角色；Swarm按需要把控制权从天气交给费用再交给汇总。三种模式都需要角色间通信和共享状态。', body)
        drawing += '<div class="concept-state"><span><b>消息</b>：谁交给谁、交付结果、证据来源</span><span><b>共享状态</b>：预算、已有证据、计划版本、完成情况</span></div>'
        example = '天气角色排除户外，费用角色核算总价，汇总角色找到同时满足两项条件的方案。'
        takeaway = '多个角色可以共用同一个模型；分工要有收益，协作要有明确出口。'
        notes = '先讲角色，不从模型数量讲起。天气角色和费用角色分别拥有职责与上下文，可以调用同一个底层模型。左图Supervisor集中分派和汇总，中图层次化增加组长层级，右图Swarm由当前角色按需要把任务和控制权交接给下一角色，不能随机无限转交。箭头表示任务或控制权的方向，结果通过消息交付。消息像一次交接单，写清发送方、接收方、任务、结果和来源；共享状态像共同维护的任务记录，保存预算、证据、计划版本和完成状态。主管模式也可以构成层次化中的一层；并行是执行方式，评审是反馈方式，可以组合在这些组织方式里。最后回到例子：天气和费用取交集，300元雨天可以得到博物馆210元。'
        sources = ['multi', 'patterns']
    else:
        raise ValueError('Concept stage must be 1–7')
    html = (f'<p class="concept-definition">{definition}</p>' + drawing +
            f'<p class="concept-example">{example}</p><p class="takeaway">{takeaway}</p>')
    return {'title': title, 'body': html, 'notes': notes, 'sources': sources}
