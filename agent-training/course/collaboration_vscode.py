"""Slides guide the instructor into full source files and actual VS Code runs."""
from html import escape
from pathlib import Path
from collaboration_references import references_for

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ('sequential', 'supervisor', 'hierarchical', 'swarm', 'network')
LESSONS = {
    'sequential': ('Sequential Chain', '外层下一步由固定边决定', 'sec06',
                   'Researcher → Analyst → Writer → Critic',
                   ['看 add_edge：顺序已写在图中。', '角色内部实际调用模型和资料工具。', '缺资料时保留缺项；本例未配置回退。'],
                   'graph.add_edge(START'),
    'supervisor': ('Supervisor', '主管模型读取当前状态，选择下一成员', 'sec03',
                   '每个 Worker 完成后都返回主管',
                   ['在 supervisor() 处设断点。', '看模型选择与 Command(goto=...)。', '切 missing，观察主管是否重新派 Researcher。'],
                   '    def supervisor(state):'),
    'hierarchical': ('Hierarchical', 'CEO 调度团队，团队负责人调度成员', 'sec04',
                     '父图 → 编译后的团队子图 → 父图',
                     ['先看两个 build_*_team() 的独立图。', '再看父图把编译后的团队注册为节点。', '缺项时交付团队向 CEO 反馈，不跨层调用成员。'],
                     '    def ceo(state):'),
    'swarm': ('Swarm', '当前角色选择 handoff，交出控制权', 'sec05',
              '允许交接的对象由 HANDOFFS 定义',
              ['先看每个角色的 HANDOFFS 白名单。', '在 agent_node() 中看模型返回的 next_role。', '交接由当前角色发起；没有主管或固定轮询。'],
              '    def agent_node(role):'),
    'network': ('Network', '当前节点选择允许的下一跳或结束', 'sec07',
                '节点内执行角色职责 → 模型决定下一跳',
                ['本例从 Writer 开始，先发现资料不足。', '每个角色都能访问其他对等角色。', '没有中央 Router；与 Swarm 的机制可重叠。'],
                '    def peer_node(role):'),
}


def source_excerpt(pattern):
    path = ROOT / 'demo' / 'collaboration_live' / f'{pattern}.py'
    lines = path.read_text(encoding='utf-8').splitlines()
    anchor = LESSONS[pattern][5]
    start = next(i for i, line in enumerate(lines) if anchor in line)
    selected = lines[start:start + (7 if pattern == 'sequential' else 9)]
    return '<pre class="ct-vscode-source"><code>' + escape('\n'.join(selected)) + '</code></pre>'


def file_link(pattern):
    path = f'demo/collaboration_live/{pattern}.py'
    return f'<a href="{path}" target="_blank">{path} ↗</a>'


def _original_training_slides(seconds_budget):
    from collaboration_training import diagram
    result = []
    def add(title, body, notes, sources=('collab_multi', 'collab_patterns'), weight=100):
        result.append(dict(title=title, body=body, notes=notes, chapter='协作模式详解',
                           layout='collaboration-training-slide vscode-training-slide',
                           source_section='training', sources=list(sources), weight=weight))
    add('同一个任务，五份真实代码',
        '<p class="ct-intro">两大一小，雨天出游，预算 300 元。<br>在 VS Code 中运行完整 LangGraph + 模型程序。</p>'
        '<div class="ct-role-strip">' + ''.join(f'<div><b>{name}</b><span>{role}</span><p>{duty}</p></div>' for name, role, duty in [
            ('搜集', 'Researcher', '请求资料工具，读取证据'), ('核算', 'Analyst', '调用费用工具，检查缺项'),
            ('撰写', 'Writer', '模型生成预算内建议'), ('审查', 'Critic', '模型审查 + 程序核验')]) + '</div>'
        '<div class="ct-prompt"><b>共同输入，真实执行</b><p>normal：完整资料；missing：首次返回漏餐费。<br>观察谁决定下一步、消息怎样返回、何时结束。</p></div>'
        '<p class="ct-footnote">DeepSeek 主配置；连接失败切换现有 OpenAI/Codex 备用。<br>模型请求与 LangGraph 编排真实执行；场馆资料为固定课堂数据。</p>',
        '本章以VS Code完整源码和集成终端为主。先解释角色分工，再开demo/collaboration_live。'
        'normal和missing使用同一个工具，后者第一次返回没有餐费。DeepSeek主用，OpenAI/Codex备用。'
        '真实模型输出和路径不保证每次一致；实际工具证据和程序验收决定能否交付。', weight=80)
    for pattern in PATTERNS:
        name, rule, sid, flow, points, _ = LESSONS[pattern]
        add(name + ' · 先看协作结构',
            f'<p class="ct-rule">{escape(rule)}</p><div class="ct-vscode-layout"><div class="ct-vscode-diagram">'
            + diagram(pattern) + f'<p class="ct-path">{escape(flow)}</p></div>'
            + '<div class="ct-vscode-observe"><h3>打开源码后观察</h3><ol>'
            + ''.join(f'<li>{escape(point)}</li>' for point in points) + '</ol></div></div>'
            + '<div class="ct-prompt"><b>源码入口</b><p>' + file_link(pattern) + '</p></div>'
            '<p class="ct-footnote">先指出结构和控制权，再切换 VS Code。对照下一页的运行命令与断点。</p>',
            f'{name}：{rule}。{flow}。' + ' '.join(points)
            + '本页只有结构说明，实际演示在VS Code里执行。Swarm与Network可重叠，本例均为串行活跃角色。',
            references_for(sid, '', 0), 100)
        command = f'python demo/run_collaboration.py --pattern {pattern} --scenario missing --step'
        add(name + ' · VS Code 关键代码与运行',
            '<p class="ct-rule">完整源码包含节点、边、角色、工具、模型连接和结束条件。</p>'
            + source_excerpt(pattern)
            + '<div class="ct-vscode-run"><b>在项目根目录的 VS Code 集成终端运行</b>'
            f'<pre><code>{escape(command)}</code></pre></div>'
            '<div class="ct-vscode-bottom"><p>' + file_link(pattern) + '</p>'
            '<p>终端看：模型请求 → 工具返回 → 路由/汇报 → 状态 → 最终结果。</p></div>'
            '<p class="ct-footnote">F5：选择“真实协作 · ' + name + '”。每个节点返回后按 Enter 继续。<br>'
            '源码节选用于定位；完整程序请在 VS Code 中阅读和运行，图与 JSON 轨迹来自本次执行。</p>',
            '提前选好Python解释器并安装requirements.txt。在VS Code运行和调试选择对应的真实协作配置。'
            f'打开demo/collaboration_live/{pattern}.py，在关键路由或边定义处设断点。'
            '公共角色在agents.py、工具在tools.py、状态在state.py；runtime.py负责终端过程与保存结果。'
            '先normal快速确认结果，再missing观察补充路径。真实模型可能产生不同决策，用实际日志讨论。'
            '显示决策摘要，不展示内部思维过程。', references_for(sid, '代码实现', 1), 120)
    add('五种模式对比 · 从实际轨迹回看控制权',
        '<p class="ct-rule">对比这次执行中的决策者、返回路径和验收结果。</p>'
        '<table class="ct-table"><thead><tr><th>模式</th><th>谁决定下一步</th><th>缺项时观察什么</th><th>源码机制</th></tr></thead><tbody>'
        + ''.join('<tr>' + ''.join(f'<td>{escape(value)}</td>' for value in row) + '</tr>' for row in [
            ('Sequential Chain', '预定义的固定边', '没有回退边，等待补充', 'add_edge'),
            ('Supervisor', '主管模型', '成员反馈后重新分派', 'Command + 返回主管'),
            ('Hierarchical', '各层负责人模型', '子团队反馈给父图', '编译后的子图'),
            ('Swarm', '当前活跃角色', '白名单内的交接', 'HANDOFFS + Command'),
            ('Network', '当前角色节点', '直接选择其他角色', '节点内 Command'),
        ]) + '</tbody></table>'
        '<div class="ct-prompt"><b>打开本次输出</b><p>demo/output/collaboration-live/&lt;本次目录&gt;<br>比较 trace.json 与 report.md；以实际执行为准。</p></div>'
        '<p class="ct-footnote">模型不确定性会改变路径与耗时；框架负责调度，程序验收负责守住结果边界。<br>Swarm 与 Network 可组合；本例固定顺序不代表所有顺序工作流都不能回退。</p>',
        '用实际运行目录里的五份JSON和报告对比，不用规则示意的步骤数估算模型能力或成本。'
        'normal一般得到博物馆240元。missing的设计目标是固定链保留缺项，其他模式经反馈补齐；'
        '模型可能提前结束、选择不允许路由或重复循环，代码会拒绝或停止，保留轨迹供讨论。')
    add('课堂练习 · 修改完整代码，再运行验证',
        '<p class="ct-intro">给顺序链加一条补资料的返回路径。<br>让改动通过一次真实运行来证明。</p>'
        '<div class="ct-exercise"><ol><li>打开 sequential.py，设计缺项后的条件边。</li>'
        '<li>回到 Researcher 补资料，再重新核算、撰写、审查。</li>'
        '<li>设置循环上限，检查旧建议是否失效。</li></ol></div>'
        '<details class="ct-answer"><summary>展开验收标准</summary><p>首次没有餐费时不得通过；补齐后完整费用为240元。'
        '<br>日志出现实际返回路径，JSON中保存新证据与审查结果；达到上限时明确停止。</p></details>'
        '<p class="ct-footnote"><a href="dist/collaboration-demo.zip" download>下载完整 VS Code 演示包</a> · '
        '<a href="docs/collaboration-demo-guide.md" target="_blank">准备、断点和运行指南 ↗</a></p>',
        '这是一道现场或课后改代码的练习，当前固定链没有实现返回边。先指出add_edge和条件路由的差别，'
        '让学员修改完整文件后跑missing，观察真实图路径。tools.read_sources会重置旧核算、建议和验收标记。', weight=80)
    add('真实模型配置 · DeepSeek 主用，OpenAI 备用',
        '<p class="ct-rule">模型选择、编排结构和资料工具分别配置。</p>'
        '<table class="ct-table ct-bridge-table"><thead><tr><th>位置</th><th>完整源码</th><th>课堂观察</th></tr></thead><tbody>'
        + ''.join('<tr>' + ''.join(f'<td>{escape(value)}</td>' for value in row) + '</tr>' for row in [
            ('模型顺序', 'demo/model_backup.py', 'DeepSeek 优先；连接失败明确切换备用，保留当前状态'),
            ('角色与工具', 'collaboration_live/agents.py、tools.py', '模型提出工具请求；Python 实际执行并返回证据'),
            ('编排与记录', 'collaboration_live/五种模式.py、runtime.py', '图实际调度，逐节点打印，保存本次轨迹与报告'),
        ]) + '</tbody></table>'
        '<div class="ct-vscode-run"><b>课前只检查连接配置，不发起模型调用</b>'
        '<pre><code>python demo/run_collaboration.py --check-model</code></pre></div>'
        '<p class="ct-footnote">AG2 Playground 可选讲 3–5 分钟：'
        '<a href="https://playground.ag2.ai/" target="_blank" rel="noopener">协作机制的框架对照 ↗</a><br>'
        '推荐选 Sequential Chat / Nested Chat；Auto Pattern 为集中选择，不能直接当作 Swarm。'
        '<br>网站作为补充资源；本章完整代码、模型与运行过程以 VS Code 为主。</p>',
        'DeepSeek主配置，现有OpenAI/Codex连接备用；配置存放在本机，不打包密钥。先check-model，备课时再实际运行。'
        '备用沿用现有CCSwitch Codex客户端连接，若其供应商要求官方客户端，不要拿这份凭据填进网站。'
        'AG2 Playground已经核对有Sequential Chat、Nested Chat、Auto Pattern和条件handoff。'
        '推荐作为可选框架对照，最多3–5分钟，不逐个重复五模式。Auto Pattern是管理者集中选择。', weight=100)
    total = sum(slide['weight'] for slide in result)
    durations = [seconds_budget * slide.pop('weight') // total for slide in result]
    for index in range(seconds_budget - sum(durations)):
        durations[index] += 1
    for slide, seconds in zip(result, durations):
        slide.update(seconds=seconds, minutes=seconds / 60)
        slide['notes'] = f'【{seconds // 60} 分 {seconds % 60:02} 秒】' + slide['notes']
    return result


def training_slides(seconds_budget):
    original = _original_training_slides(seconds_budget)
    task = original[0]
    task['title'] = '案例：雨天出游，预算 300 元'
    roles = task['body'].split('<div class="ct-role-strip">', 1)[1].split('<div class="ct-prompt">', 1)[0]
    task['body'] = ('<p class="ct-intro">两位大人带一个孩子，安排半日出游。</p>'
                    + '<div class="ct-role-strip">' + roles
                    + '<div class="ct-prompt"><b>两种情况</b><p>资料齐全：给出预算内的方案。<br>餐费缺失：补齐资料后再判断是否超支。</p></div>')
    comparison = original[11]
    comparison['title'] = '五种协作模式：谁决定下一步'
    rows = [
        ('Sequential Chain', '固定步骤', '搜集 → 核算 → 撰写 → 审查', '步骤固定，前后有依赖'),
        ('Supervisor', '主管', '成员完成后返回主管', '统一分派和验收'),
        ('Hierarchical', '各层负责人', '总负责人 → 团队 → 成员', '任务可拆成多个子团队'),
        ('Swarm', '当前角色', '交给允许接手的角色', '按任务进展转交专家'),
        ('Network', '当前节点', '直接选择其他角色', '路径随结果变化'),
    ]
    comparison['body'] = ('<table class="ct-table"><thead><tr><th>模式</th><th>谁决定下一步</th><th>任务怎样传递</th><th>适用任务</th></tr></thead><tbody>'
                          + ''.join('<tr>' + ''.join(f'<td>{escape(value)}</td>' for value in row) + '</tr>' for row in rows)
                          + '</tbody></table><p class="ct-footnote">Swarm 强调角色交接，Network 强调节点路由；两者的实现可以重叠。<br>'
                          '<a href="https://playground.ag2.ai/" target="_blank" rel="noopener">打开 AG2 Playground ↗</a>：在浏览器中试运行协作示例，下一页对照使用。</p>')
    comparison['notes'] = (
        '用本次运行目录中的五份 JSON 和报告对照表格。normal 通常得到博物馆 240 元；'
        'missing 首次漏餐费，固定链没有返回边，其他模式可以选择反馈路径。'
        '实际模型可能提前结束或反复循环，按日志说明程序怎样反馈、修正或停止。\n\n'
        '课后可给顺序链增加条件返回边，再运行 missing。资料重新读取后，旧核算、建议和验收标记会清空。'
        '模型与编排分别配置：DeepSeek 主用，连接失败后使用现有 OpenAI/Codex 备用，配置留在本机。'
        '比较成本与能力时，要使用真实调用记录。AG2 Playground 用于观察另一套框架中的协作机制。')
    def demo_link(slug, label):
        return f'<a href="https://playground.ag2.ai/demos/{slug}/" target="_blank" rel="noopener">{label} ↗</a>'
    demos = [
        ('Sequential Chain', demo_link('sequential-chat', 'Sequential Chat'), '依次处理；前一轮摘要传给后一轮'),
        ('Supervisor', demo_link('auto-pattern', 'Auto Pattern'), '管理者根据上下文选择下一发言者'),
        ('Hierarchical', demo_link('nested-chat', 'Nested Chat'), '外层 Writer 委托内部流程，再收回结果'),
        ('Swarm', demo_link('llm-condition', 'LLM Condition'), 'Triage 判断条件，把请求交给专家'),
        ('Network', demo_link('network-conversation', 'Conversation Channel'), '体验对等通信；下一跳路由看本课代码'),
    ]
    playground = dict(
        title='AG2 Playground：协作模式对照与使用',
        chapter=task['chapter'], source_section='training',
        layout=task['layout'] + ' playground-guide-slide',
        sources=list(comparison['sources']),
        body='<p class="ct-footnote"><a href="https://playground.ag2.ai/" target="_blank" rel="noopener">playground.ag2.ai ↗</a> · 浏览器中的交互示例，运行时可查看角色消息。</p>'
             '<table class="ct-table"><thead><tr><th>本课模式</th><th>网站示例 · 点击打开</th><th>重点观察</th></tr></thead><tbody>'
             + ''.join('<tr><td>' + mode + '</td><td>' + link + '</td><td>' + point + '</td></tr>' for mode, link, point in demos)
             + '</tbody></table><div class="ct-prompt"><b>怎么用</b><p>首页选 Classic → 打开示例 → 在 Demo 中输入任务并运行。<br>切到 Code，对照消息顺序、分派或交接的代码。</p></div>'
             '<p class="ct-footnote">先试 Sequential Chat：选 “How computers store data”，点击 Run。<br>上表按机制对照；Nested Chat 体现嵌套委托，网站的 Network 是通信运行时。</p>',
        notes='建议用3分钟操作一个示例，其他入口供学员自行体验。首页目前分AG2与Classic；前四个示例位于Classic，'
              'Conversation Channel在AG2的Network分类。表内链接直接进入Demo；要对照Code，从首页打开相应卡片。'
              'Sequential Chat选How computers store data后点Run，观察Curriculum、Planning、Formatting和最终教案。'
              'Auto Pattern由管理者选择发言者，不能解释成无主管Swarm；Nested Chat展示两层委托，'
              '并不等于本课完整的分层团队图；LLM Condition展示Triage条件交接，不能据此推断任意角色都能互相交接。'
              'Conversation Channel为两方自由通信，不规定发言顺序，也不等于本课每个节点选择下一跳的Network。'
              '本课Network完整机制仍对照demo/collaboration_live/network.py。'
              '网站使用自己的模型和任务，不会继承本机模型配置；不把出游案例当成网站已接入的业务工具。'
              '核实来源：2026-10-08网站首页示例代码、分类和Sequential Chat页面。',
    )
    result = [task, comparison, playground]
    explanations = [
        '固定边规定执行顺序；本例缺资料时等待补充。',
        '成员完成后返回主管，由主管决定继续分派还是结束。',
        '团队内部完成分工，再把结果返回上一层负责人。',
        '当前角色发起交接，接手对象必须在允许名单内。',
        '节点完成自己的任务后，选择其他角色或结束。',
    ]
    pattern_notes = {
        'sequential': (
            '打开 demo/collaboration_live/sequential.py，在 build_graph 的 add_edge 处设断点。'
            'Researcher、Analyst、Writer、Critic 的顺序在外层图中确定，角色内部仍会调用模型和工具。\n\n'
            '先用 normal 看完整结果，再用 missing 看餐费缺失。本例没有回退边，会保留缺项并等待补充。'
            '公共角色在 agents.py，工具在 tools.py，状态在 state.py，runtime.py 负责日志与保存。'
            '课前选好解释器、安装 requirements.txt；其他模式共用这些文件。'),
        'supervisor': (
            '打开 demo/collaboration_live/supervisor.py，在 supervisor() 处看当前状态与模型选择。'
            '成员完成后返回主管，Command(goto=...) 把任务交给下一个角色。\n\n'
            '运行 missing，在费用角色报告缺项后暂停。请学员预测主管会选谁，再核对实际路径。'
            '主管可以重新派 Researcher，也可能作出不合格选择；以日志里的修正或停止为准。'),
        'hierarchical': (
            '打开 demo/collaboration_live/hierarchical.py，先看两个 build_*_team()，再看父图把编译后的团队图注册为节点。'
            'CEO 选团队，团队负责人选成员，结果逐级返回。\n\n'
            '在 ceo / lead 处检查输入和返回。missing 情景下，交付团队需要向 CEO 反馈，'
            '不会直接跨层调用搜集者。JSON 中的 namespace 可以对照实际子图执行。'),
        'swarm': (
            '打开 demo/collaboration_live/swarm.py，看 HANDOFFS 定义的允许对象。'
            '在 agent_node() 中检查模型返回的 next_role，交接由当前角色发起。\n\n'
            '运行 missing，观察审查者能否把任务交回搜集者。箭头规定允许关系，执行时不必绕图一圈。'
            '本例一次只有一个活跃角色；界面显示行动摘要，完整记录保存到本次目录。'),
        'network': (
            '打开 demo/collaboration_live/network.py，在 peer_node() 看角色工作完成后怎样选择下一跳或 END。'
            '本例从 Writer 开始，让资料不足出现在第一次处理结果中。\n\n'
            '每个节点都可访问其他对等角色，路由决定留在当前节点。与 Swarm 对照时，看允许连接和交接方式的差别。'
            '两种机制可以重叠，本例也都串行执行；请求不允许的目标或超出上限时，程序会拒绝或停止。'),
    }
    for index, pattern in enumerate(PATTERNS):
        structure, example = original[1 + index * 2:3 + index * 2]
        example['title'] = LESSONS[pattern][0] + '：代码示例'
        example['body'] = (source_excerpt(pattern)
                           + '<div class="ct-prompt"><p>' + explanations[index] + '</p></div>'
                           + '<div class="ct-vscode-bottom"><p>' + file_link(pattern) + '</p></div>')
        example['notes'] = pattern_notes[pattern]
        example['notes'] += f'\n\n运行命令：python demo/run_collaboration.py --pattern {pattern} --scenario missing --step。每个节点返回后按 Enter 继续。'
        result.append(example)
    # Fewer projected pages; retain time for the live source walkthroughs.
    weights = [80, 100, 100, 120, 120, 120, 120, 120]
    durations = [seconds_budget * weight // sum(weights) for weight in weights]
    for index in range(seconds_budget - sum(durations)):
        durations[index] += 1
    import re
    for slide, seconds in zip(result, durations):
        slide.update(seconds=seconds, minutes=seconds / 60)
        slide['notes'] = re.sub(r'【\d+ 分 \d{2} 秒】', '', slide['notes'])
        slide['notes'] = f'【{seconds // 60} 分 {seconds % 60:02} 秒】' + slide['notes']
    return result
