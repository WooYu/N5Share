"""Build the offline course, notes, outline, and recorded LangGraph traces."""
import argparse
import json
import sys
import zipfile
from collections import OrderedDict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'course'))
from content import CHAPTERS, SOURCES, duration_text, slides
from glossary import GLOSSARY, PRONUNCIATION_NOTE
from architectures import OUTING_TRADEOFFS, DIAGNOSIS_TRADEOFFS, ARCHITECTURE_TRADEOFFS

sys.path.insert(0, str(ROOT / 'demo'))
from agents import PATTERNS, SCENARIOS, run


def json_script(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')


def build():
    course_duration = duration_text(sum(slide['seconds'] for slide in slides))
    chapters = OrderedDict()
    for slide in slides:
        chapters[slide['chapter']] = chapters.get(slide['chapter'], 0) + slide['seconds']
    if list(chapters.items()) != CHAPTERS:
        raise ValueError(f'章节时长与大纲不符：{chapters}')
    has_diagnosis_lab = any('__DIAGNOSIS_LAB__' in slide['body'] for slide in slides)
    sections = []
    lab = (ROOT / 'web/lab.html').read_text(encoding='utf-8') if has_diagnosis_lab else ''
    for index, slide in enumerate(slides):
        links = ''.join(f'<a href="{escape(SOURCES[key][1], quote=True)}" target="_blank" rel="noopener">{escape(SOURCES[key][0])} ↗</a>' for key in slide['sources'])
        reference_label = '相关参考：' if index < 11 and links else ''
        title = '' if slide['layout'] == 'cover' else '<h2>' + escape(slide['title']) + '</h2>'
        body = slide['body'].replace('__DIAGNOSIS_LAB__', lab)
        sections.append(
            f'<section class="slide {slide["layout"]}" aria-label="{index + 1}. {escape(slide["title"], quote=True)}">'
            f'<div class="slide-content">{title}{body}</div><footer class="slide-footer"><div>'
            f'{reference_label}{links or escape(slide["chapter"] + " · 高级推理与多 Agent 协作")}</div>'
            f'<span class="slide-num">{index + 1:02} / {len(slides)}</span></footer></section>'
        )
    course = [{**slide, 'sources': [SOURCES[key] for key in slide['sources']]} for slide in slides]
    replays = {}
    for pattern in PATTERNS if has_diagnosis_lab else ():
        for scenario in SCENARIOS:
            trace = run(pattern=pattern, scenario=scenario)
            expected_success = scenario in ('normal', 'missing', 'conflict')
            if bool(trace['verified']) != expected_success:
                raise RuntimeError(f'轨迹验收失败：{pattern}/{scenario} -> {trace["status"]}')
            replays[f'{pattern}:{scenario}'] = trace
    html = (ROOT / 'web/template.html').read_text(encoding='utf-8')
    replacements = {
        '__SLIDES__': '\n'.join(sections), '__COURSE__': json_script(course),
        '__REPLAY__': json_script(replays), '__PLAYER__': '\n'.join((ROOT / 'web' / name).read_text(encoding='utf-8') for name in ('speaker-notes.js', 'player.js', 'outing.js', 'outing-live.js', 'collaboration-import.js', 'collaboration-training.js')),
        '__GLOSSARY__': json_script([{'id': key, **value} for key, value in GLOSSARY.items()]),
        '__PRONUNCIATION_NOTE__': escape(PRONUNCIATION_NOTE),
        '__DEMO_TRADEOFFS__': json_script(dict(outing=OUTING_TRADEOFFS, diagnosis=DIAGNOSIS_TRADEOFFS, architecture=ARCHITECTURE_TRADEOFFS)),
        '__IMPORT_STYLES__': '\n'.join((ROOT / 'web' / name).read_text(encoding='utf-8') for name in ('collaboration-import.css', 'collaboration-training.css', 'framework-training.css', 'dev-team.css', 'speaker-notes.css')),
    }
    for token, value in replacements.items():
        html = html.replace(token, value)
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    notes = [
        f'# 高级推理框架与多 Agent 协作 · 讲师讲稿\n\n{course_duration}，{len(slides)} 页。'
        '面向 Java 后端、前端、客户端开发者，不预设 Agent 开发经验。\n\n'
        '备课时打开 [课件](../index.html)，在 VS Code 中运行协作代码。'
        '安装 requirements.txt 后，用 `python demo/run_collaboration.py` 运行五种模式，'
        '用 `python demo/server.py` 启动七种架构的真实模型入口。'
        'HTML 中的“下一步”使用规则示意和固定课堂资料。\n\n'
        '每页包含可直接照讲的现场讲稿，以及按需选讲的概念、类比、业务实例、误区和互动。'
        '原定时长是课堂安排，包含操作与停顿；扩展材料不必全部朗读，初学者课程可增加讲解时间。\n\n'
        '听发音：打开网页按 N，在“术语发音与释义”中选择“听发音”或“慢速”，'
        '也可切换全课词库搜索。Markdown 保留音标和释义，播放请使用网页。'
        + PRONUNCIATION_NOTE + '\n'
    ]
    outline = ['# 高级推理框架与多 Agent 协作 · 培训大纲\n\n'
               f'{course_duration} · Java 后端 / 前端 / 客户端开发者 · 架构与协作模式演示\n\n'
               '学习目标：判断任务适合用程序、工作流还是 Agent；画出角色、工具、消息、状态和结束条件。\n']
    for chapter, seconds in chapters.items():
        outline.append(f'\n## {chapter}｜{duration_text(seconds)}\n\n')
        for index, slide in enumerate(slides):
            if slide['chapter'] == chapter:
                outline.append(f'- {index + 1:02}. {slide["title"]}（{duration_text(slide["seconds"])}）\n')
    for index, slide in enumerate(slides):
        notes.append(f'\n## {index + 1:02} · {slide["title"]}\n\n{slide["chapter"]} · {duration_text(slide["seconds"])}\n\n{slide["notes"]}\n')
        notes.append(f'\n### 本页术语\n\n[在网页中打开本页并按 N 听发音](../index.html#{index + 1})\n\n')
        for term in slide['terms']:
            notes.append(f'- **{term["label"]} {term["ipa"]}（{term["meaning"]}）**：{term["explanation"]}\n')
        if slide['sources']:
            notes.append('\n来源：' + '；'.join(f'[{SOURCES[key][0]}]({SOURCES[key][1]})' for key in slide['sources']) + '\n')
    notes.append('\n## 全课术语速查\n\n' + PRONUNCIATION_NOTE + '\n\n')
    for term in GLOSSARY.values():
        notes.append(f'- **{term["label"]} {term["ipa"]}（{term["meaning"]}）**：{term["explanation"]}\n')
    (ROOT / 'docs/speaker-notes.md').write_text(''.join(notes), encoding='utf-8')
    (ROOT / 'docs/outline.md').write_text(''.join(outline), encoding='utf-8')
    samples = ROOT / 'test-results/diagnosis-samples'
    if replays:
        samples.mkdir(parents=True, exist_ok=True)
    for name, trace in replays.items():
        (samples / (name.replace(':', '-') + '-trace.json')).write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
    if replays:
        (samples / 'report.md').write_text('# 仿真远程诊断报告\n\n' + replays['integrated:conflict']['report'], encoding='utf-8')
    print(f'Built {len(slides)} slides / {course_duration}; embedded {len(replays)} validated LangGraph replays.')


def package():
    target = ROOT / 'dist/Agent-Training-HTML-Demo.zip'
    target.parent.mkdir(parents=True, exist_ok=True)
    files = [path for path in ROOT.rglob('*') if path.is_file()
             and not any(part in ('__pycache__', '.venv', '.venv-metagpt', '.langgraph_api', 'output', 'test-results', 'work-notes', 'generated-examples', 'dist') for part in path.relative_to(ROOT).parts)
             and path.suffix in ('.py', '.js', '.cjs', '.css', '.html', '.md', '.json', '.txt', '.cmd', '.ps1', '.png', '.pdf')]
    collaboration_package = ROOT / 'dist/collaboration-demo.zip'
    if collaboration_package.is_file():
        files.append(collaboration_package)
    files.extend(ROOT / name for name in ('.gitignore', '.gitattributes', 'config/.env.example'))
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
