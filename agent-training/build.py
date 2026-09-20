"""Build the offline course, notes, outline, and recorded LangGraph traces."""
import argparse
import json
import sys
import zipfile
from collections import OrderedDict
from html import escape
from pathlib import Path

from content import SOURCES, slides

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'demo'))
from agents import PATTERNS, SCENARIOS, run


def json_script(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')


def build():
    chapters = OrderedDict()
    for slide in slides:
        chapters[slide['chapter']] = chapters.get(slide['chapter'], 0) + slide['minutes']
    if list(chapters.values()) != [5, 13, 13, 12, 22, 12, 15, 28]:
        raise ValueError(f'章节时长与120分钟大纲不符：{chapters}')
    if sum('__DIAGNOSIS_LAB__' in slide['body'] for slide in slides) != 1:
        raise ValueError('课程需要一个诊断运行台')
    sections = []
    lab = (ROOT / 'lab.html').read_text(encoding='utf-8')
    for index, slide in enumerate(slides):
        links = ''.join(f'<a href="{escape(SOURCES[key][1], quote=True)}" target="_blank" rel="noopener">{escape(SOURCES[key][0])} ↗</a>' for key in slide['sources'])
        title = '' if slide['layout'] == 'cover' else '<h2>' + escape(slide['title']) + '</h2>'
        body = slide['body'].replace('__DIAGNOSIS_LAB__', lab)
        sections.append(
            f'<section class="slide {slide["layout"]}" aria-label="{index + 1}. {escape(slide["title"], quote=True)}">'
            f'<div class="slide-content">{title}{body}</div><footer class="slide-footer"><div>'
            f'{links or escape(slide["chapter"] + " · 高级推理与多 Agent 协作")}</div>'
            f'<span class="slide-num">{index + 1:02} / {len(slides)}</span></footer></section>'
        )
    course = [{**slide, 'sources': [SOURCES[key] for key in slide['sources']]} for slide in slides]
    replays = {}
    for pattern in PATTERNS:
        for scenario in SCENARIOS:
            trace = run(pattern=pattern, scenario=scenario)
            expected_success = scenario in ('normal', 'missing', 'conflict')
            if bool(trace['verified']) != expected_success:
                raise RuntimeError(f'轨迹验收失败：{pattern}/{scenario} -> {trace["status"]}')
            replays[f'{pattern}:{scenario}'] = trace
    html = (ROOT / 'template.html').read_text(encoding='utf-8')
    replacements = {
        '__SLIDES__': '\n'.join(sections), '__COURSE__': json_script(course),
        '__REPLAY__': json_script(replays), '__PLAYER__': (ROOT / 'player.js').read_text(encoding='utf-8') + '\n' + (ROOT / 'outing.js').read_text(encoding='utf-8'),
    }
    for token, value in replacements.items():
        html = html.replace(token, value)
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    notes = [
        f'# 高级推理框架与多 Agent 协作 · 讲师讲稿\n\n120 分钟，{len(slides)} 页。'
        '面向 Java 后端、前端、客户端开发者，不预设 Agent 开发经验。\n\n'
        '备课：安装 requirements.txt 后运行 `python demo/server.py`。默认规则模拟决策，'
        'LangGraph 实际编排，工具只读合成资料。离线 HTML 内嵌的是预录轨迹；'
        'completed 仅表示报告生成，仍需人工审核。verified 仅表示证据契约通过。\n'
    ]
    outline = ['# 高级推理框架与多 Agent 协作 · 培训大纲\n\n'
               '120 分钟 · Java 后端 / 前端 / 客户端开发者 · 远程诊断业务仿真\n\n'
               '学习目标：按任务复杂度选择推理与协作方式；设计包含角色、工具、消息、状态和结束条件的简单系统。\n']
    for chapter, minutes in chapters.items():
        outline.append(f'\n## {chapter}｜{minutes:g} 分钟\n\n')
        for index, slide in enumerate(slides):
            if slide['chapter'] == chapter:
                outline.append(f'- {index + 1:02}. {slide["title"]}（{slide["minutes"]:g} 分钟）\n')
    for index, slide in enumerate(slides):
        notes.append(f'\n## {index + 1:02} · {slide["title"]}\n\n{slide["chapter"]} · {slide["minutes"]:g} 分钟\n\n{slide["notes"]}\n')
        if slide['sources']:
            notes.append('\n来源：' + '；'.join(f'[{SOURCES[key][0]}]({SOURCES[key][1]})' for key in slide['sources']) + '\n')
    (ROOT / 'speaker-notes.md').write_text(''.join(notes), encoding='utf-8')
    (ROOT / 'outline.md').write_text(''.join(outline), encoding='utf-8')
    samples = ROOT / 'demo' / 'sample-output'
    samples.mkdir(exist_ok=True)
    for name, trace in replays.items():
        (samples / (name.replace(':', '-') + '-trace.json')).write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
    (samples / 'report.md').write_text('# 仿真远程诊断报告\n\n' + replays['integrated:conflict']['report'], encoding='utf-8')
    print(f'Built {len(slides)} slides / 120 minutes; embedded {len(replays)} validated LangGraph replays.')


def package():
    target = ROOT.parent / 'Agent-Training-HTML-Demo.zip'
    files = [path for path in ROOT.rglob('*') if path.is_file()
             and not any(part in ('__pycache__', '.venv', 'output') for part in path.relative_to(ROOT).parts)
             and path.suffix in ('.py', '.js', '.html', '.md', '.json', '.txt', '.cmd')]
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(ROOT.parent))
    print(f'Packaged {len(files)} files: {target.name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', action='store_true')
    options = parser.parse_args()
    build()
    if options.package:
        package()
