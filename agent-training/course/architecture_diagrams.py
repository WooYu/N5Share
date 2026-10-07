"""Native vector diagrams matching the supplied architecture infographic."""
from html import escape


COLORS = ['#087443', '#2454ce', '#6737b5', '#bc510d', '#087d80', '#693ab7', '#2454ce']
TINTS = ['#edf9f2', '#eff5ff', '#f6f1ff', '#fff5eb', '#edfafa', '#f6f1ff', '#eff5ff']


def diagram(index, prefix):
    color, tint = COLORS[index - 1], TINTS[index - 1]
    ink, stroke = '#17243b', '#465365'
    marker = f'{prefix}-arrow-{index}'
    viewbox = '0 0 300 184'

    def text(x, y, label, size=13, fill=ink, weight=500, anchor='middle'):
        return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" '
                f'font-weight="{weight}" fill="{fill}">{escape(label)}</text>')

    def box(x, y, width, height, label='', active=False, size=13):
        return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="5" '
                f'fill="{tint if active else "#fff"}" stroke="{color if active else "#b9c4d3"}" stroke-opacity=".5" stroke-width="1.2"/>'
                + (text(x + width / 2, y + height / 2 + size * .35, label, size) if label else ''))

    def edge(path, dashed=False, both=False):
        return (f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="1.4" '
                'stroke-linejoin="round" stroke-linecap="round" '
                + ('stroke-dasharray="4 3" ' if dashed else '')
                + f'marker-end="url(#{marker})" '
                + (f'marker-start="url(#{marker})" ' if both else '') + '/>')

    def icon(x, y, kind, scale=1):
        shapes = {
            'user': '<circle cx="16" cy="8" r="6" fill="#53575b"/><path d="M4 32v-5a12 12 0 0 1 24 0v5Z" fill="#53575b"/>',
            'brain': ('<path d="M16 5C11-2 5 2 5 8C0 9 0 16 3 19C0 24 3 30 8 30C8 36 15 36 16 30Z"/>'
                      '<path d="M18 5C23-2 29 2 29 8C34 9 34 16 31 19C34 24 31 30 26 30C26 36 19 36 18 30Z"/>'
                      '<path d="M5 8c6-1 8 3 6 7M3 19c5-4 10-1 9 3M8 30c-1-5 3-7 5-7M29 8c-6-1-8 3-6 7M31 19c-5-4-10-1-9 3M26 30c1-5-3-7-5-7"/>'),
            'tools': ('<path d="M24 3a8 8 0 0 0-9 11L3 26a3 3 0 0 0 4 4l12-12a8 8 0 0 0 11-9l-5 5-5-5Z" fill="#e2e4e6"/>'
                      '<path d="m3 3 4-2 7 7-3 3Z" fill="#72777d"/><path d="m11 11 15 15" stroke-width="3"/>'
                      '<path d="m23 25 3-3 5 5-4 4Z" fill="#e2e4e6"/>'),
            'output': '<rect x="5" y="1" width="24" height="33" rx="2" fill="#fff0cb"/><path d="M10 9h14M10 15h14M10 21h14M10 27h9"/>',
            'agent': ('<rect x="3" y="10" width="26" height="21" rx="5" fill="#f4f7ff"/>'
                      '<path d="M16 3v7M0 18h3m26 0h3M11 25h10"/>'
                      '<circle cx="10" cy="18" r="1.6" fill="#26335c"/><circle cx="22" cy="18" r="1.6" fill="#26335c"/>'
                      '<circle cx="16" cy="3" r="2" fill="#f4f7ff"/>'),
            'state': '<rect x="4" y="3" width="25" height="26" rx="3" fill="#fff"/><path d="M4 10h25"/><path d="M10 15h2m7 0h2m-11 6h2m7 0h2" stroke-width="2.5"/>',
        }
        return (f'<g transform="translate({x} {y}) scale({scale})" stroke="{"#26335c" if kind == "agent" else "#4d5258"}" '
                f'stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round">{shapes[kind]}</g>')

    if index == 1:
        viewbox = '0 0 320 136'
        body = (icon(15, 38, 'user', 1.1) + icon(100, 38, 'brain', 1.1)
                + icon(183, 38, 'tools', 1.1) + icon(270, 38, 'output', 1.1)
                + edge('M 54 56 H 86') + edge('M 139 56 H 173') + edge('M 225 56 H 258')
                + text(33, 109, '用户输入', 16) + text(118, 109, 'LLM', 16)
                + text(201, 109, '工具调用', 16) + text(287, 109, '输出', 16))
    elif index == 2:
        body = ''
        for y, label in [(4, 'Thought（思考）'), (51, 'Action（调用工具）'),
                         (98, 'Observation（结果）'), (145, '继续思考...')]:
            body += box(48, y, 195, 32, label, True, 14)
            if y != 145:
                body += edge(f'M 145 {y + 34} V {y + 45}')
        body += edge('M 251 161 H 263 Q 280 161 280 142 V 38 Q 280 20 261 20 H 251', dashed=True)
    elif index == 3:
        body = (box(3, 10, 131, 34, 'Planner（规划）', True, 14)
                + edge('M 137 27 H 160') + box(163, 10, 134, 34, 'Executor（执行）', True, 14)
                + edge('M 68 47 V 66') + edge('M 230 47 V 66')
                + box(7, 70, 123, 107) + box(173, 70, 114, 107))
        for y, label in [(92, '1. 步骤 1'), (116, '2. 步骤 2'), (140, '3. 步骤 3'), (165, '...')]:
            body += text(68, y, label, 14)
        for y, label in [(92, '执行步骤 1'), (116, '执行步骤 2'), (140, '执行步骤 3'), (165, '...')]:
            if y < 165:
                body += f'<path d="M173 {y + 7}h114" stroke="#d5dce6"/>'
            body += text(230, y, label, 14)
    elif index == 4:
        body = (box(85, 3, 130, 32, 'Orchestrator', True, 14)
                + edge('M 124 37 43 67') + edge('M 150 37 V 67') + edge('M 177 37 251 67'))
        for x, label in [(7, 'Agent A'), (108, 'Agent B'), (209, 'Agent C')]:
            body += box(x, 72, 84, 67, active=True) + icon(x + 26, 78, 'agent') + text(x + 42, 128, label, 13)
        body += text(295, 146, '...', 10)
        for x, width, label in [(2, 62, 'Planner'), (71, 58, 'Coder'), (136, 72, 'Reviewer'), (215, 83, 'Tool Agent')]:
            body += box(x, 154, width, 26, label, size=12)
    elif index == 5:
        viewbox = '0 0 220 300'
        body = (icon(45, 3, 'user', .75) + text(122, 22, '用户输入', 14)
                + edge('M 110 31 V 45') + box(12, 49, 196, 37, 'Intent Router（意图识别）', True, 13)
                + edge('M 110 89 V 105 H 37 V 117') + edge('M 110 105 V 117')
                + edge('M 110 105 H 183 V 117'))
        for x, label in [(6, 'Skill A'), (79, 'Skill B'), (152, 'Skill C')]:
            body += (box(x, 121, 62, 34, label, True, 14) + edge(f'M{x + 31} 159 V 175')
                     + box(x + 4, 179, 54, 30, '执行', size=14) + edge(f'M{x + 31} 213 V 229')
                     + box(x + 1, 233, 60, 34, '输出结果', size=13))
    elif index == 6:
        viewbox = '0 0 300 205'
        body = (box(80, 10, 140, 82, active=True) + text(150, 39, 'Blackboard', 18, color, 600)
                + text(150, 63, '（共享状态）', 15, color) + icon(134, 76, 'state')
                + edge('M77 48 H35 V126', both=True) + edge('M150 110 V126')
                + edge('M223 48 H265 V126', both=True))
        for x, label in [(1, 'Agent A'), (116, 'Agent B'), (231, 'Agent C')]:
            body += box(x, 131, 68, 66, active=True) + icon(x + 18, 136, 'agent') + text(x + 34, 186, label, 13)
    else:
        viewbox = '0 0 440 170'
        body = ''
        for x, label in [(8, 'Node A'), (112, 'Node B'), (216, 'Node C'), (320, 'Node D')]:
            body += box(x, 10, 77, 34, label, True, 14)
            if x != 320:
                body += edge(f'M{x + 81} 27 H{x + 101}')
        body += (edge('M254 47 V86') + edge('M401 27 H430 V125 H401')
                 + edge('M150 47 V61 H107 V125 H125', both=True)
                 + box(129, 108, 77, 34, 'Node E', True, 14)
                 + box(320, 108, 77, 34, 'Node F', True, 14)
                 + '<path d="M254 88 291 125 254 162 217 125Z" fill="#e6f2e1" stroke="#b1cba8" stroke-width="1.2"/>'
                 + text(254, 130, '条件判断', 13)
                 + edge('M213 125 H209') + edge('M294 125 H317'))

    return (f'<svg class="architecture-diagram" viewBox="{viewbox}" role="img" '
            f'aria-labelledby="{prefix}-diagram-title-{index}" xmlns="http://www.w3.org/2000/svg">'
            f'<title id="{prefix}-diagram-title-{index}">架构 {index} 流程图</title>'
            f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
            f'<path d="M0 1 9 5 0 9Z" fill="{stroke}"/></marker></defs>{body}</svg>')


def tool_marks():
    """Compact vector marks with live tool names and reference captions."""
    marks = [
        ('LangGraph', '', '<circle cx="12" cy="12" r="11" fill="#075a43"/><path d="m5 8 3 8m0-4 4-4m-1 0 4 8m-1-4 4-4" stroke="#fff" stroke-width="1.8" fill="none"/>'),
        ('Temporal', '(Workflow<br>engine)', '<path d="M10 2h4v7h7v4h-7v9h-4v-9H3V9h7Z" stroke="#243144" stroke-width="1.4" fill="none"/><path d="M8 2h8M8 22h8" stroke="#243144"/>'),
        ('Airflow', '(Workflow<br>scheduler)', '<path d="M12 12 2 3Q12-1 12 12" fill="#39b5df"/><path d="M12 12 21 2Q25 12 12 12" fill="#db5561"/><path d="M12 12 22 21Q12 25 12 12" fill="#31b69b"/><path d="M12 12 3 22Q-1 12 12 12" fill="#f2b83a"/>'),
        ('n8n', 'n8n (Workflow<br>automation)', '<path d="M4 12h5l6-6h5M9 12l6 6h5" stroke="#d73078" stroke-width="2" fill="none"/><g fill="#fff" stroke="#d73078" stroke-width="1.8"><circle cx="4" cy="12" r="2.8"/><circle cx="20" cy="6" r="2.8"/><circle cx="20" cy="18" r="2.8"/></g>'),
        ('Prefect', '', '<path d="M5 20V5l9-3 6 4v8l-9 3v5Z" fill="#187baf"/><path d="M11 7v15M11 7l9-1M11 13l9-2" stroke="#053f64" stroke-width="1.5" fill="none"/>'),
    ]
    return ('<div class="architecture-tool-logos" aria-label="LangGraph；Temporal；Airflow；n8n；Prefect">'
            + ''.join(f'<div class="architecture-tool"><div class="architecture-tool-name">'
                      f'<svg viewBox="0 0 24 24" aria-hidden="true">{mark}</svg><span>{name}</span></div>'
                      f'<small>{caption}</small></div>' for name, caption, mark in marks) + '</div>')
