"""Build a fully self-contained HTML presentation and speaker notes."""
import json
import sys
from pathlib import Path
from html import escape
from content import slides, SOURCES

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'demo'))
from agents import run

def json_script(obj):
    return json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c')

def build():
    sections=[]
    for i,s in enumerate(slides):
        links=''.join(f'<a href="{SOURCES[k][1]}" target="_blank" rel="noopener">{SOURCES[k][0]} ↗</a>' for k in s['sources'])
        title='' if s['layout']=='cover' else '<h2>'+s['title']+'</h2>'
        sections.append(f'<section class="slide {s["layout"]}" aria-label="{i+1}. {escape(s["title"])}">'
            f'<div class="slide-content">{title}{s["body"]}</div><footer class="slide-footer"><div>{links or escape(s["chapter"]+" · Agent 推理与协作")}</div><span class="slide-num">{i+1:02} / {len(slides)}</span></footer></section>')
    course=[{**s,'sources':[SOURCES[k] for k in s['sources']]} for s in slides]
    replays={'normal':run(inject_failure=False),'failure':run(inject_failure=True)}
    if not all(v['verified'] for v in replays.values()):
        raise RuntimeError('不能嵌入未经验证的成功轨迹')
    html=(ROOT/'template.html').read_text(encoding='utf-8').replace('__SLIDES__','\n'.join(sections)).replace('__COURSE__',json_script(course)).replace('__REPLAY__',json_script(replays))
    (ROOT/'index.html').write_text(html,encoding='utf-8')
    notes=['# Agent 推理与协作 · 讲师讲稿\n\n90 分钟，32 页。备注中的时间为建议，可按听众调整。\n\n演讲前：运行 `python demo/server.py`，打开浏览器到本地 8765 端口。默认规则模拟决策，真实 CSV 工具。离线回放明确标记为历史轨迹。\n']
    for i,s in enumerate(slides):
        notes.append(f'\n## {i+1:02} · {s["title"]}\n\n{s["notes"]}\n')
        if s['sources']:
            notes.append('\n来源：'+'；'.join(f'[{SOURCES[k][0]}]({SOURCES[k][1]})' for k in s['sources'])+'\n')
    (ROOT/'speaker-notes.md').write_text(''.join(notes),encoding='utf-8')
    sample=ROOT/'demo'/'sample-output';sample.mkdir(exist_ok=True)
    for name,trace in replays.items():
        (sample/(name+'-trace.json')).write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (sample/'report.md').write_text('# 样本订单报告\n\n'+replays['failure']['report'],encoding='utf-8')
    print(f'Built {len(slides)} slides; embedded two verified simulation traces.')

if __name__=='__main__':
    build()
