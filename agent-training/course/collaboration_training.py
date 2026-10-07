"""Comparable, source-backed collaboration lessons for slides 13–26."""
from functools import lru_cache
from html import escape
import inspect
import json
from demo.reference import collaboration_patterns as engine
from collaboration_references import references_for

PATTERN_ORDER = ('sequential', 'supervisor', 'hierarchical', 'swarm', 'network')
COPY = {
    'sequential': ('Sequential Chain', '下一步由预先定义的顺序决定',
                   '搜集 → 核算 → 撰写 → 审查', '本例未配置回退边，缺资料后等待补充。',
                   '步骤明确、产物依次依赖的任务', 'sec06'),
    'supervisor': ('Supervisor', '下一步由主管读取状态后决定',
                   '每个成员执行后都向主管汇报', '缺项反馈返回主管，再分派搜集者。',
                   '需要统一分派、验收与权限管理的任务', 'sec03'),
    'hierarchical': ('Hierarchical', '高层分派团队，团队负责人分派成员',
                     'CEO → 负责人 → 成员，结果逐级返回', '交付团队请求补资料，先反馈给 CEO。',
                     '任务可拆成多个有独立边界的子团队', 'sec04'),
    'swarm': ('Swarm', '当前角色通过 handoff 交出控制权',
              '允许交接的关系由各角色工具集限制', '审查者发现缺项，直接交回搜集者。',
              '专业角色之间需要按任务进展交接', 'sec05'),
    'network': ('Network', '当前角色根据结果选择允许的下一跳',
                '本例为全连接；每个节点都能发起路由', '费用专家直接找搜集者补资料。',
                '任务路径多变，需要灵活访问其他角色', 'sec07'),
}
ROLE_LABELS = {'Researcher': '搜集', 'Analyst': '核算', 'Writer': '撰写', 'Critic': '审查',
               'Supervisor': '主管', 'CEO': '总负责人', 'ResearchLead': '资料负责人',
               'DeliveryLead': '交付负责人', 'END': '结束'}


def source_lines(function):
    lines, start = inspect.getsourcelines(function)
    result, in_doc = [], False
    for offset, line in enumerate(lines):
        if '"""' in line:
            if line.count('"""') == 1:
                in_doc = not in_doc
            continue
        if not in_doc and line.strip():
            result.append({'number': start + offset, 'text': line.rstrip()})
    return result


def display_code(pattern):
    functions = {'sequential': engine.run_sequential, 'supervisor': engine.run_supervisor,
                 'hierarchical': engine.run_hierarchical, 'network': engine.network_choice}
    if pattern != 'swarm':
        return source_lines(functions[pattern])
    # Show the local policy and the actual handoff call, each from its real source.
    lines = source_lines(engine.swarm_choice)
    start = next(i for i, line in enumerate(lines) if "if role == 'Critic'" in line['text'])
    return [lines[0], *lines[start:start + 8], *[
        line for line in source_lines(engine.run_peers)
        if 'policy(active' in line['text'] or 'run.control(active' in line['text']
        or 'active = target' in line['text']]]


def code_highlight(pattern, event, code):
    """Map events to executed orchestration statements, not to invented code."""
    kind, actor, target = event['kind'], event['actor'], event['target']
    needle = None
    if pattern == 'sequential':
        needle = 'run.work' if kind == 'work' else 'run.emit' if kind == 'fixed_edge' else None
    elif pattern == 'supervisor':
        needle = {'work': 'run.work', 'dispatch': 'run.control', 'report': 'run.emit'}.get(kind)
    elif pattern == 'hierarchical' and kind == 'dispatch' and actor == 'CEO':
        needle = "'ResearchLead'" if target == 'ResearchLead' else "'DeliveryLead'"
    elif pattern == 'swarm' and kind == 'handoff':
        needle = 'run.control(active'
    elif pattern == 'network' and kind == 'route':
        # Researcher always routes to Analyst before the global missing check.
        if actor == 'Researcher':
            needle = "return 'Analyst', '搜集者"
        elif target == 'END':
            needle = "return 'END'"
        elif target == 'Researcher':
            needle = "return 'Researcher'"
        elif target == 'Analyst':
            needle = "return 'Analyst', '需要"
        elif target == 'Writer':
            needle = "return 'Writer'"
        else:
            needle = "return 'Critic'"
    return next((i for i, line in enumerate(code) if needle and needle in line['text']), None)


@lru_cache(maxsize=1)
def lesson_data():
    result = {}
    for pattern in PATTERN_ORDER:
        code = display_code(pattern)
        traces = {scenario: engine.run_demo(pattern, scenario=scenario)
                  for scenario in ('normal', 'missing')}
        result[pattern] = dict(code=code, traces=traces, highlights={
            scenario: [code_highlight(pattern, event, code) for event in trace['events']]
            for scenario, trace in traces.items()})
    return result


def diagram(pattern):
    workers = ['Researcher', 'Analyst', 'Writer', 'Critic']
    if pattern == 'hierarchical':
        positions = {'CEO': (400, 42), 'ResearchLead': (155, 143), 'DeliveryLead': (555, 143),
                     'Researcher': (130, 266), 'Analyst': (350, 266), 'Writer': (535, 266),
                     'Critic': (720, 266)}
        edges = [('CEO', 'ResearchLead'), ('CEO', 'DeliveryLead'), ('ResearchLead', 'Researcher'),
                 ('DeliveryLead', 'Analyst'), ('DeliveryLead', 'Writer'), ('DeliveryLead', 'Critic')]
        edges += [(b, a) for a, b in edges]
    elif pattern == 'supervisor':
        positions = {'Supervisor': (400, 65), **{role: (100 + i * 200, 250) for i, role in enumerate(workers)}}
        edges = [('Supervisor', role) for role in workers] + [(role, 'Supervisor') for role in workers]
    elif pattern == 'sequential':
        positions = {role: (100 + i * 200, 145) for i, role in enumerate(workers)}
        positions['END'] = (700, 285)
        edges = list(zip(workers, workers[1:])) + [('Critic', 'END')]
    else:
        positions = dict(zip(workers, [(170, 85), (630, 85), (630, 270), (170, 270)]))
        positions['END'] = (400, 175)
        edges = ([(role, target) for role, targets in engine.SWARM_LINKS.items() for target in sorted(targets)]
                 if pattern == 'swarm' else [(a, b) for a in workers for b in workers if a != b] + [(a, 'END') for a in workers])
    markup = ['<svg class="ct-graph" viewBox="0 0 800 340" role="img" aria-label="'
              + escape(COPY[pattern][0]) + ' 的允许连接与当前执行路径">']
    # Local ids avoid marker collisions between the diagram and code slides.
    for a, b in edges:
        x1, y1 = positions[a]
        x2, y2 = positions[b]
        dx, dy = x2 - x1, y2 - y1
        length = (dx * dx + dy * dy) ** .5
        ux, uy = dx / length, dy / length
        cut = min(72 / max(abs(ux), .001), 33 / max(abs(uy), .001))
        sx, sy = x1 + ux * cut - uy * 5, y1 + uy * cut + ux * 5
        ex, ey = x2 - ux * cut - uy * 5, y2 - uy * cut + ux * 5
        arrow = f'{ex},{ey} {ex - ux * 11 - uy * 5},{ey - uy * 11 + ux * 5} {ex - ux * 11 + uy * 5},{ey - uy * 11 - ux * 5}'
        markup.append(f'<g data-ct-edge="{a}:{b}"><path d="M{sx},{sy} L{ex},{ey}"/><polygon points="{arrow}"/></g>')
    for role, (x, y) in positions.items():
        markup.append(f'<g data-ct-node="{role}" transform="translate({x - 72} {y - 32})">'
                      '<rect width="144" height="64" rx="10"/>'
                      f'<text x="72" y="27">{ROLE_LABELS[role]}</text>'
                      f'<text class="ct-role-en" x="72" y="48">{role}</text></g>')
    markup.append('</svg>')
    return ''.join(markup)


def controls():
    return ('<div class="ct-controls"><div class="ct-scenarios" role="group" aria-label="演示情景">'
            '<button data-ct-scenario="normal" aria-pressed="false">资料完整</button>'
            '<button data-ct-scenario="missing" aria-pressed="true">首次漏餐费</button></div>'
            '<div><button data-ct-action="back">上一步</button> '
            '<button class="primary" data-ct-action="next">开始演示</button> '
            '<button data-ct-action="reset">重播</button> '
            '<button data-ct-action="finish">查看结果</button></div>'
            '<span data-ct-progress>准备开始</span></div>')


def state_panel():
    return ('<div class="ct-state"><h3>当前状态</h3><dl>'
            '<div><dt>场馆资料</dt><dd data-ct-state="evidence">未查询</dd></div>'
            '<div><dt>餐费</dt><dd data-ct-state="meal">未查询</dd></div>'
            '<div><dt>费用核算</dt><dd data-ct-state="analysis">未开始</dd></div>'
            '<div><dt>建议</dt><dd data-ct-state="proposal">未生成</dd></div>'
            '<div><dt>验收</dt><dd data-ct-state="approved">未通过</dd></div></dl>'
            '<p class="ct-history-note">上一步显示当时的独立状态快照</p></div>')


def demo_body(pattern, with_code=False):
    name, rule, path, missing, _, _ = COPY[pattern]
    payload = json.dumps(lesson_data()[pattern], ensure_ascii=False).replace('<', '\\u003c')
    if with_code:
        code = ''.join(f'<span class="ct-code-line" data-ct-line="{i}"><i>{line["number"]}</i>'
                       f'<code>{escape(line["text"])}</code></span>'
                       for i, line in enumerate(lesson_data()[pattern]['code']))
        main = ('<div class="ct-code"><div class="ct-code-heading">可运行 Python 源码节选 · 原文件行号</div>'
                + f'<pre>{code}</pre><a href="demo/reference/collaboration_patterns.py" target="_blank">查看完整源码 ↗</a></div>'
                + '<div class="ct-code-side">' + diagram(pattern) + state_panel() + '</div>')
    else:
        main = '<div class="ct-diagram-area">' + diagram(pattern) + f'<p class="ct-path">{escape(path)}</p></div>' + state_panel()
    return (f'<div class="ct-demo {"ct-with-code" if with_code else ""}" data-ct-pattern="{pattern}">'
            f'<p class="ct-rule">{escape(rule)}</p>' + controls()
            + '<div class="ct-main">' + main + '</div>'
            + '<div class="ct-event" aria-live="polite"><b data-ct-event-title>先预测：缺餐费时，谁决定下一步？</b>'
            '<p data-ct-event-message>点击开始演示，查看当前角色、消息和状态变化。</p></div>'
            f'<p class="ct-caption">{escape(missing)} 灰线为允许连接；青色为当前消息或控制流。</p>'
            '<p class="ct-provenance">Python 生成的离线轨迹回放 · 角色决策为规则模拟 · 无模型调用</p>'
            f'<script type="application/json" data-ct-data>{payload}</script></div>')


def table(headers, rows, cls=''):
    return f'<table class="ct-table {cls}"><thead><tr>' + ''.join(f'<th>{escape(item)}</th>' for item in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join(f'<td>{item}</td>' for item in row) + '</tr>' for row in rows) + '</tbody></table>'


def training_slides(seconds_budget):
    result = []
    def add(title, body, notes, sources=('collab_multi', 'collab_patterns'), weight=100):
        result.append(dict(chapter='协作模式详解', title=title, body=body, notes=notes,
                           sources=list(sources), layout='collaboration-training-slide',
                           source_section='training', weight=weight))
    add('同一个任务，换五种协作方式',
        '<p class="ct-intro">两大一小，雨天出游，预算 300 元。<br>交付一份包含票价、交通和餐费的可核验建议。</p>'
        '<div class="ct-role-strip">' + ''.join(f'<div><b>{ROLE_LABELS[role]}</b><span>{role}</span><p>{text}</p></div>' for role, text in zip(
            engine.ROLES, ['查询场馆与餐费', '核算全部费用', '筛选并生成建议', '独立检查证据'])) + '</div>'
        '<div class="ct-prompt"><b>给五种模式同一个问题</b><p>首次查询漏掉餐费。谁发现？谁安排补充？最终能否交付？</p></div>'
        '<p class="ct-footnote">共享状态：资料 → 核算 → 建议 → 验收。角色职责与输入相同，只改变协作控制流。<br>'
        '本章合成票价与前章不同；城市博物馆三人总价为 240 元。角色决策使用规则模拟。</p>',
        '先交代同一个任务和四个角色。正常结果都是博物馆240元，单看结果无法辨别协作方式。'
        '主讲首次漏餐费情景，不能把缺失餐费按0元处理。请学员每次预测下一位角色与决策者。'
        '本章用纯Python规则角色执行控制流，不调用模型；页面回放构建时生成的真实执行事件。', weight=80)
    for pattern in PATTERN_ORDER:
        name, rule, path, missing, use, sid = COPY[pattern]
        notes = (f'共同条件为雨天、300元、两大一小。{rule}。{path}。先用首次漏餐费，按开始演示/下一步；'
                 f'在反馈处停下，请学员预测，再执行。{missing}适合{use}。切资料完整会重置当前演示；'
                 '上一步回看历史状态，重播返回未执行状态。灰线为允许连接，青色为当前消息或交接。')
        if pattern == 'swarm':
            notes += '本例角色交接白名单见SWARM_LINKS，不是固定轮询，也未实现并行。'
        if pattern == 'network':
            notes += '本例采用全连接路由，从Writer起步；Swarm与Network可以重叠，不是互斥类别。'
        add(name + ' · 看谁决定下一步', demo_body(pattern), notes, references_for(sid, '', 0), 100)
        add(name + ' · 对照关键代码', demo_body(pattern, True),
            '投影只展示实际Python程序的关键源码节选，行号对应demo/reference/collaboration_patterns.py。'
            '先指出决策和状态更新的位置，再点击下一步观察高亮。没有对应可见代码的事件不强行高亮；'
            '层次化页展示高层控制代码，团队内部事件在流程图和状态中观察。'
            + notes + '完整源码和演示ZIP可课后使用，代码没有第三方依赖。', references_for(sid, '代码实现', 1), 120)
    rows = []
    for pattern in PATTERN_ORDER:
        name, rule, _, missing, use, _ = COPY[pattern]
        status = '等待补充' if pattern == 'sequential' else '补齐后通过'
        rows.append([name, escape(rule), escape(missing), status])
    add('五种模式对比 · 同样的缺项，不同的路径',
        '<p class="ct-rule">选择模式时，先问谁掌握控制权，再问异常如何返回。</p>'
        + table(['模式', '谁决定下一步', '首次漏餐费后的处理', '本例结果'], rows)
        + '<div class="ct-prompt"><b>课堂讨论</b><p>固定步骤已经足够时，增加主管会带来什么收益和额外成本？</p></div>'
        '<p class="ct-footnote">本例顺序链没有回退；顺序工作流也可以显式添加重试或补充路径。'
        '<br>Swarm 描述交接机制，Network 描述连接与路由，两者可组合；本例均为串行执行。</p>',
        '先请学员复述谁决策，再对照缺项路径。五种模式不是互斥或能力升级。'
        '这里不比较模型性能，也不用仿真的步骤数证明模型成本。顺序链缺项等待是本例配置，不是所有顺序链的固有限制。')
    add('课堂练习 · 给顺序链补一条异常路径',
        '<p class="ct-intro">费用专家发现餐费缺失。<br>如何让顺序链在保留已有资料的情况下继续？</p>'
        '<div class="ct-exercise"><ol><li>画出补资料的返回边，标明谁触发。</li>'
        '<li>补齐后从哪个角色恢复？哪些旧产物需要失效？</li>'
        '<li>如果一直补不齐，何时停止，向谁说明原因？</li></ol></div>'
        '<details class="ct-answer"><summary>展开参考思路</summary><p>核算发现缺项 → 搜集补充 → 重新核算 → 撰写 → 审查。'
        '<br>保留已有证据，清除旧核算、旧建议和验收标记；限制补充次数，失败时等待人工输入。</p></details>'
        '<p class="ct-footnote"><a href="dist/collaboration-demo.zip" download>下载完整演示包</a> · '
        '<a href="docs/collaboration-demo-guide.md" target="_blank">运行与练习指南 ↗</a></p>',
        '留约一分钟给学员画返回边。参考思路仅为设计练习，不声称当前run_sequential已经实现回退。'
        '课后在独立演示包中改代码并重新执行，特别检查旧核算、旧建议失效以及补充次数限制。', weight=80)
    add('从规则演示接入真实模型',
        '<p class="ct-rule">协作方式由控制流体现；角色智能由模型、上下文与工具提供。</p>'
        + table(['位置', '现在的教学代码', '接入模型时的修改'], [
            ['角色执行', '<code>worker(role, state, scenario)</code>', '角色独立上下文 + 模型和工具，返回状态更新'],
            ['主管决策', '<code>supervisor_choice(state)</code>', '输出结构化的成员选择与决策摘要'],
            ['对等决策', '<code>swarm_choice / network_choice</code>', '当前角色输出交接或下一跳，校验允许连接'],
            ['执行边界', '状态快照、验收与步骤上限', '保留；并补充超时、工具失败和持久化恢复'],
        ], 'ct-bridge-table')
        + '<p class="ct-takeaway">先用可复现的轨迹学会控制流，再用真实模型观察决策的不确定性。</p>'
        '<p class="ct-footnote">原 LangGraph / AutoGen 框架片段：'
        '<a href="assets/imported/multi-agent-source.html#sec03" target="_blank">原文参考 ↗</a>（未补全的片段不能直接运行）'
        '<br><a href="dist/collaboration-demo.zip" download>课后可运行代码：纯 Python，无 API Key 或联网要求</a></p>',
        '说明规则模拟和真实Agent的边界。替换worker只能让角色调用模型；要实现模型自主路由，还需替换主管或当前角色的决策函数。'
        '顺序链仍可保持固定边。框架原文只作参考，部分片段未补全；现场无需切换不同框架API。'
        '下一页进入智能软件开发团队，将刚才的角色、消息、状态和结束条件迁移到开发场景。', weight=100)
    total = sum(slide['weight'] for slide in result)
    durations = [seconds_budget * slide.pop('weight') // total for slide in result]
    for index in range(seconds_budget - sum(durations)):
        durations[index] += 1
    for slide, seconds in zip(result, durations):
        slide.update(seconds=seconds, minutes=seconds / 60)
        slide['notes'] = f'【{seconds // 60} 分 {seconds % 60:02} 秒】' + slide['notes']
    return result
