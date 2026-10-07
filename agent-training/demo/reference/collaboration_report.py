"""Standalone HTML and Markdown views of executed collaboration traces."""
from html import escape
import json

MECHANISMS = {
    'supervisor': ('主管根据返回状态选择下一个成员，每次执行后都回到主管。',
                   'Supervisor ⇄ Researcher / Analyst / Writer / Critic'),
    'hierarchical': ('CEO 委派子团队；团队负责人调度成员，缺项逐级反馈后跨团队处理。',
                     'CEO\n ├─ ResearchLead ⇄ Researcher\n └─ DeliveryLead ⇄ Analyst / Writer / Critic'),
    'swarm': ('当前角色通过允许的 handoff 交出控制权；审查者可交回搜集者。',
              'Researcher → Critic → Analyst → Writer → Critic\nCritic → Researcher（资料缺失）\nCritic → Writer（方案需要修订）'),
    'sequential': ('下一步由代码预先指定；资料缺失不会自动增加回退边。',
                   'START → Researcher → Analyst → Writer → Critic → END'),
    'network': ('共享路由函数读取当前输出与状态；每个角色都可直接路由到其他角色。',
                'Researcher ⇄ Analyst ⇄ Writer ⇄ Critic\n   任意两个角色之间均允许路由；不是固定轮询'),
}
STATUS = {'completed': '完成并通过审查', 'needs_input': '资料缺失，等待补充',
          'no_solution': '当前约束无解', 'step_limit': '达到步骤上限'}
KIND = {'dispatch': '分派', 'report': '汇报', 'work': '执行', 'handoff': '交接控制权',
        'route': '对等路由', 'fixed_edge': '固定顺序', 'escalate': '逐级反馈',
        'start': '开始', 'finish': '结束', 'stop': '停止'}


def result_text(trace):
    if trace['status'] == 'step_limit':
        return '步骤上限已到，保留中间资料；协作流程尚未完成。'
    if trace['state']['approved']:
        return trace['state']['proposal']['text']
    return '缺少餐费资料，无法完整核算。需要补充资料后重新运行固定流水线。'


def summary_row(trace, html=False):
    values = [trace['pattern'], STATUS[trace['status']], str(trace['steps']),
              str(trace['state']['research_rounds']), result_text(trace)]
    if html:
        values[0] = f'<a href="#{trace["pattern"]}">{escape(values[0])}</a>'
        return '<tr><td>' + '</td><td>'.join([values[0], *(escape(v) for v in values[1:])]) + '</td></tr>'
    return '| ' + ' | '.join(values) + ' |'


def html_section(trace):
    pattern = trace['pattern']
    state = trace['state']
    mechanism, diagram = MECHANISMS[pattern]
    steps = ''.join(
        f'<li class="event {event["kind"]}"><div class="event-heading">'
        f'<span class="number">{event["index"]:02d}</span>'
        f'<strong>{escape(event["actor"])} → {escape(event["target"])}</strong>'
        f'<span class="tag">{escape(KIND[event["kind"]])}</span>'
        f'<small>步骤 {event["step"]}</small></div>'
        f'<p>{escape(event["reason"])}</p>'
        + (f'<p class="output">{escape(event["message"])}</p>' if event['message'] else '')
        + (f'<p class="changes">状态变更：{escape(", ".join(event["changed"]))}</p>'
           if event['changed'] else '')
        + '<details><summary>查看这一步的状态快照</summary><pre>'
        + escape(json.dumps(event['state'], ensure_ascii=False, indent=2)) + '</pre></details></li>'
        for event in trace['events'])
    visited = ' → '.join(e['actor'] for e in trace['events'] if e['kind'] == 'work')
    costs = ''
    if state['analysis']:
        rows = ''.join('<tr>' + ''.join(f'<td>{escape(str(row[key]))}</td>'
                                      for key in ('venue', 'tickets', 'transport', 'meal', 'total'))
                       + '</tr>' for row in state['analysis'])
        costs = '<h3>实际核算结果 / 元</h3><div class="table-wrap"><table><thead><tr><th>候选</th><th>两大一小门票</th><th>交通</th><th>餐费</th><th>总计</th></tr></thead><tbody>' + rows + '</tbody></table></div>'
    return (f'<section id="{pattern}"><div class="section-title"><h2>{escape(trace["label"])}</h2>'
            f'<a href="#top">回到对比 ↑</a></div><p>{escape(mechanism)}</p>'
            f'<pre class="topology">{escape(diagram)}</pre>'
            f'<p class="path"><strong>本次实际成员执行顺序</strong><br>{escape(visited or "尚未执行成员")}</p>'
            f'<div class="result {trace["status"]}"><span>{escape(STATUS[trace["status"]])}</span>'
            f'<p>{escape(result_text(trace))}</p></div>{costs}'
            '<h3>执行轨迹 <small>分派、汇报及执行均记录；展开可查看历史状态</small></h3>'
            f'<ol class="timeline">{steps}</ol>'
            f'<p><a href="{pattern}-trace.json">打开原始 JSON 轨迹</a></p></section>')


def write_report(traces, output):
    first = traces[0]
    weather = '雨天' if first['state']['weather'] == 'rain' else '晴天'
    scenario = '资料完整' if first['scenario'] == 'normal' else '首次遗漏餐费'
    context = f"两大一小 · {weather} · 预算 {first['state']['budget']} 元 · {scenario}"
    markdown = [f'# 五种协作模式运行对比\n\n{context}',
                '规则模拟，使用合成资料；未调用模型。步骤统计角色执行和动态控制决策，'
                '不是模型调用量、Token 数或性能基准。',
                '| 模式 | 状态 | 步骤 | 资料查询 | 结果 |\n| --- | --- | ---: | ---: | --- |\n'
                + '\n'.join(summary_row(t) for t in traces)]
    for trace in traces:
        mechanism, diagram = MECHANISMS[trace['pattern']]
        markdown.extend([f'\n## {trace["label"]}\n\n{mechanism}',
                         f'```text\n{diagram}\n```', result_text(trace)])
        for event in trace['events']:
            markdown.append(f"- {event['index']:02d}. **{event['actor']} → {event['target']}** "
                            f"[{KIND[event['kind']]}] {event['reason']}"
                            + (f"；{event['message']}" if event['message'] else ''))
    (output / 'comparison.md').write_text('\n\n'.join(markdown) + '\n', encoding='utf-8')
    navigation = ''.join(f'<a href="#{t["pattern"]}">{escape(t["pattern"])}</a>' for t in traces)
    rows = ''.join(summary_row(t, html=True) for t in traces)
    document = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>五种协作模式 · 实际运行报告</title><style>
:root { color-scheme: light; --ink:#172638; --muted:#586779; --paper:#f3f5f7; --accent:#176253; }
* { box-sizing:border-box; } body { margin:0; background:var(--paper); color:var(--ink); font:16px/1.7 "Segoe UI","Microsoft YaHei",sans-serif; }
main { max-width:1160px; margin:auto; padding:36px 24px 64px; } h1 { font-size:clamp(28px,4vw,44px); line-height:1.25; margin:12px 0; }
h2 { font-size:24px; margin:0; } h3 { font-size:18px; margin:28px 0 12px; } p { margin:10px 0; } a { color:var(--accent); text-underline-offset:3px; }
.eyebrow { font-size:13px; letter-spacing:2px; color:var(--accent); font-weight:700; } .context { font-size:20px; }
.note,small { color:var(--muted); } small { font-size:12px; font-weight:400; } nav { display:flex; gap:10px; flex-wrap:wrap; margin:24px 0; }
nav a { padding:7px 16px; background:#fff; border:1px solid #d4dde3; border-radius:6px; text-decoration:none; }
section { background:#fff; border:1px solid #dce3e8; border-radius:10px; padding:28px; margin-top:32px; scroll-margin-top:16px; }
.section-title { display:flex; align-items:baseline; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.table-wrap { overflow-x:auto; } table { border-collapse:collapse; width:100%; background:#fff; font-size:14px; }
td,th { text-align:left; padding:12px 14px; border-bottom:1px solid #e0e6eb; } th { background:#e7edf1; white-space:nowrap; }
pre { white-space:pre-wrap; overflow-wrap:anywhere; padding:16px; background:#f1f4f7; border-radius:6px; font:13px/1.65 Consolas,"Microsoft YaHei",monospace; }
.topology { background:#172638; color:#ecf5fa; font-size:15px; } .path { border-left:3px solid #7c94ae; padding:10px 16px; background:#f3f6f9; overflow-wrap:anywhere; }
.result { border-left:4px solid var(--accent); padding:14px 20px; background:#edf7f3; margin:20px 0; } .result span { font-weight:700; }
.result.needs_input,.result.step_limit { border-color:#a96617; background:#fff5e4; } .result.no_solution { border-color:#52688b; background:#eef2f9; }
.timeline { list-style:none; padding:0; } .event { border-left:2px solid #dce4eb; padding:4px 0 20px 20px; } .event-heading { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.number { color:#687a8e; font:13px Consolas,monospace; } .tag { font-size:12px; padding:1px 8px; border-radius:4px; background:#e8edf2; }
.work .tag { color:#176253; background:#dbf1e9; } .handoff .tag,.route .tag { background:#e5eafb; color:#394c88; } .escalate .tag { background:#fff1d9; color:#96580b; }
.event p { margin:6px 0; font-size:14px; } .output { font-weight:600; } .changes { color:#586779; } details { font-size:13px; color:#586779; }
summary { cursor:pointer; padding:4px 0; } details pre { color:var(--ink); max-height:420px; overflow:auto; } footer { margin-top:28px; color:var(--muted); font-size:13px; }
@media(max-width:600px) { main { padding:20px 12px; } section { padding:18px 14px; } .event { padding-left:12px; } }
@media print { body { background:#fff; } main { max-width:none; } details,nav { display:none; } section { break-before:page; } .event { break-inside:avoid; } }
</style></head><body><main id="top"><header><div class="eyebrow">SLIDES 12–26 / EXECUTED TRACE</div>
<h1>五种协作模式，如何完成同一个任务</h1>'''
    document += (f'<p class="context">{escape(context)}</p>'
                 '<p class="note">本报告来自 Python 实际执行的控制流。角色决策由确定性规则模拟，'
                 '资料为合成数据，无模型调用。各模式共用角色、数据、费用规则及验收条件。</p></header>'
                 f'<nav aria-label="模式目录">{navigation}</nav>'
                 '<div class="table-wrap"><table><thead><tr><th>模式</th><th>状态</th><th>步骤</th>'
                 f'<th>资料查询</th><th>交付结果</th></tr></thead><tbody>{rows}</tbody></table></div>'
                 '<p class="note">步骤 = 角色执行 + 动态控制决策；汇报与日志不另计。'
                 '这些数字反映本实现的控制开销，不能用于判断模型质量或框架性能。</p>'
                 + ''.join(html_section(t) for t in traces)
                 + '<footer>HTML 可离线打开。Swarm 与 Network 的定义有重叠：此处分别演示受限 handoff 和全连接路由；'
                   '两者都允许动态交接，都不等于并行执行。规则模拟展示协作机制，真实 Agent 还需模型决策与独立上下文。</footer>'
                   '</main></body></html>')
    (output / 'comparison.html').write_text(document, encoding='utf-8')
