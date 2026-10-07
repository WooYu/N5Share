"""Inline vector diagrams for comparing the five collaboration control flows."""
from html import escape


PATTERNS = ('supervisor', 'hierarchical', 'swarm', 'sequential', 'network')


def circle(name, x, y, active=False):
    return (f'<g class="comparison-node{" is-active" if active else ""}" data-node="{name}">'
            f'<rect x="{x - 25}" y="{y - 25}" width="50" height="50" rx="8"/>'
            f'<g class="comparison-robot" transform="translate({x - 11} {y - 17})" aria-hidden="true">'
            '<path d="M 11 1 V 5 M 1 11 H 3 M 19 11 H 21"/>'
            '<rect x="3" y="5" width="16" height="13" rx="4"/>'
            '<circle cx="8" cy="10" r="1"/><circle cx="14" cy="10" r="1"/>'
            '<path d="M 8 14 H 14"/></g>'
            f'<text class="comparison-agent-name" x="{x}" y="{y + 17}">Agent {escape(name)}</text></g>')


def manager(name, x, y, width=100):
    return (f'<g class="comparison-manager" data-node="{name}">'
            f'<rect x="{x - width / 2}" y="{y - 20}" width="{width}" height="40" rx="9"/>'
            f'<text x="{x}" y="{y + 6}">{escape(name)}</text></g>')


def edge(pattern, source, target, path, kind='dispatch', muted=False):
    return (f'<path class="comparison-edge {kind}{" is-muted" if muted else ""}" '
            f'data-source="{source}" data-target="{target}" data-kind="{kind}" '
            f'd="{path}" marker-end="url(#comparison-arrow-{pattern}{"-muted" if muted else ""})"/>')


def graph(pattern, label, network_roles=4):
    edges, nodes = [], []
    description = ''
    caption = ''
    if pattern == 'supervisor':
        description = '主管统一选择成员。成员完成工作后返回主管，再由主管选择下一步。'
        for name, x in (('A', 38), ('B', 112), ('C', 186)):
            edges.append(edge(pattern, '主管', name, f'M {112 + (x-112)*.35} 75 L {x-5} 151'))
            edges.append(edge(pattern, name, '主管', f'M {x+7} 151 L {120 + (x-112)*.3} 75', 'return', True))
            nodes.append(circle(name, x, 177))
        nodes.append(manager('主管', 112, 55))
        caption = '分派 ↓　汇报 ↑　再分派'
    elif pattern == 'hierarchical':
        description = '高层主管分派给两个团队主管，团队主管各自调度成员，再逐级汇总。'
        nodes.append(manager('总主管', 112, 30))
        for name, x in (('团队 1', 57), ('团队 2', 167)):
            edges.append(edge(pattern, '总主管', name, f'M 112 50 L {x} 85'))
            nodes.append(manager(name, x, 105, 90))
        for name, x, parent in (('A', 26, 57), ('B', 83, 57), ('C', 141, 167), ('D', 198, 167)):
            team = '团队 1' if parent == 57 else '团队 2'
            edges.append(edge(pattern, team, name, f'M {parent} 125 L {x} 158'))
            nodes.append(circle(name, x, 184))
        caption = '逐级分派，结果逐级汇总'
    elif pattern == 'swarm':
        description = '箭头是允许的交接关系，不是固定循环。当前角色自主决定是否交接及交给谁，也可直接结束。'
        edges.extend([
            edge(pattern, 'A', 'B', 'M 93 40 C 155 20 178 57 172 92', 'handoff', True),
            edge(pattern, 'B', 'C', 'M 155 135 C 140 164 118 184 87 186', 'handoff', True),
            edge(pattern, 'C', 'A', 'M 44 166 C 13 118 22 63 48 53', 'handoff', True),
            edge(pattern, 'A', 'B', 'M 93 40 C 155 20 178 57 172 92', 'selected'),
        ])
        nodes.extend([circle('A', 69, 44, True), circle('B', 172, 118), circle('C', 62, 187)])
        caption = '按需交接，也可直接结束'
    elif pattern == 'sequential':
        description = '外层固定从 A 到 B 再到 C；各阶段仍可使用工具和重试。此图省略阶段内部的执行过程。'
        edges.extend([
            edge(pattern, 'A', 'B', 'M 112 61 L 112 86', 'fixed'),
            edge(pattern, 'B', 'C', 'M 112 137 L 112 162', 'fixed'),
        ])
        nodes.extend([circle('A', 112, 35), circle('B', 112, 111), circle('C', 112, 188)])
        caption = 'A → B → C，顺序预先确定'
    else:
        description = '图示为全连接对等网络，各节点按允许连接选择下一跳。强调色箭头是一条示例路径，全连接不是所有实现的要求。'
        positions = {'A': (47, 48), 'B': (177, 48), 'C': (177, 178), 'D': (47, 178)}
        paths = [
            ('A', 'B', 'M 74 40 L 150 40'), ('B', 'A', 'M 150 56 L 74 56'),
            ('B', 'C', 'M 185 75 L 185 151'), ('C', 'B', 'M 169 151 L 169 75'),
            ('C', 'D', 'M 150 186 L 74 186'), ('D', 'C', 'M 74 170 L 150 170'),
            ('D', 'A', 'M 39 151 L 39 75'), ('A', 'D', 'M 55 75 L 55 151'),
            ('A', 'C', 'M 71 63 L 161 153'), ('C', 'A', 'M 153 163 L 63 73'),
            ('B', 'D', 'M 161 73 L 71 163'), ('D', 'B', 'M 63 153 L 153 63'),
        ]
        if network_roles == 3:
            description = 'Planner、Executor、Reviewer 各自在节点内部执行任务，并自主选择允许的下一节点或结束。没有独立的中央决策 Router。'
            positions = {'A': (47, 48), 'B': (177, 48), 'C': (112, 178)}
            paths = [
                ('A', 'B', 'M 74 40 L 150 40'), ('B', 'A', 'M 150 56 L 74 56'),
                ('A', 'C', 'M 51 75 L 94 151'), ('C', 'A', 'M 105 151 L 64 75'),
                ('B', 'C', 'M 160 75 L 119 151'), ('C', 'B', 'M 130 151 L 173 75'),
            ]
        for source, target, path in paths:
            edges.append(edge(pattern, source, target, path, 'route', True))
        for source, target, path in paths:
            if (source, target) in (('A', 'C'), ('C', 'B')):
                edges.append(edge(pattern, source, target, path, 'selected'))
        nodes.extend(circle(name, x, y, name == 'A') for name, (x, y) in positions.items())
        caption = '各节点按允许连接路由'
    title_id = 'comparison-title-' + pattern
    desc_id = 'comparison-desc-' + pattern
    svg = (f'<svg class="comparison-graph" viewBox="0 0 224 224" role="img" '
           f'aria-labelledby="{title_id} {desc_id}" data-pattern="{pattern}">'
           f'<title id="{title_id}">{escape(label)} 控制流示意</title>'
           f'<desc id="{desc_id}">{escape(description)}</desc><defs>'
           f'<marker id="comparison-arrow-{pattern}" viewBox="0 0 8 8" refX="7" refY="4" '
           'markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 Z" fill="var(--pattern-accent)"/></marker>'
           f'<marker id="comparison-arrow-{pattern}-muted" viewBox="0 0 8 8" refX="7" refY="4" '
           'markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 Z" fill="#9aabc2"/></marker>'
           '</defs>' + ''.join(edges + nodes) + '</svg>')
    return svg, caption


def comparison_graphics(source_cards):
    """Keep the supplied sec02 names and prose, with diagrams replacing the table."""
    cards = []
    for index, (pattern, (title, prose)) in enumerate(zip(PATTERNS, source_cards), 1):
        english, chinese = title.split(' · ', 1)
        definition, scenario = prose.split('适合', 1)
        svg, caption = graph(pattern, english)
        cards.append(
            f'<article class="comparison-pattern" data-comparison-pattern="{pattern}">'
            f'<header><div class="comparison-heading"><span class="comparison-index">{index}</span>'
            f'<h4>{escape(english)}</h4></div><strong>{escape(chinese)}</strong></header>'
            f'<div class="comparison-drawing">{svg}</div>'
            f'<p class="comparison-caption">{escape(caption)}</p>'
            f'<p class="comparison-definition">{escape(definition)}</p>'
            f'<p class="comparison-use">适合{escape(scenario)}</p></article>')
    return ('<div class="collaboration-atlas">'
            '<div class="comparison-legend"><span><i class="manager-key"></i>主管 / 团队负责人</span>'
            '<span><i class="member-key"></i>A 至 D 为专业角色</span>'
            '<span class="comparison-legend-route">箭头为控制流；灰色为可选连接</span></div>'
            '<div class="comparison-patterns">' + ''.join(cards) + '</div>'
            '<p class="comparison-note">以上为教学分类，可组合且存在重叠；Swarm 按需交接，Network 图示为全连接示例。<br>'
            '调用开销取决于次数与上下文；容错需要重试、检查点和超时设计，不能仅按模式定高低。</p>'
            '</div>')
