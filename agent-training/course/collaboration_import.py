"""Paginate the supplied collaboration document for the offline slide deck.

The local source snapshot supplies the content, with a merged visual overview
and reviewed collaboration-pattern corrections. No browser or external source is
needed to regenerate the slides. Payload block ids support completeness checks.
"""
from collections import OrderedDict
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from collaboration_references import references_for
from collaboration_visuals import comparison_graphics
from collaboration_corrections import correct_sections

SOURCE_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'imported' / 'multi-agent-source.html'
SECTION_IDS = [f'sec{number:02}' for number in range(2, 13)] + ['faq']
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

SECTION_NOTES = {
    ('sec02', 0): (
        '先看箭头由谁发出。Supervisor 由主管选成员；Hierarchical 多一层团队负责人；'
        'Swarm 由当前角色交接；Sequential Chain 按固定顺序；Network 由节点选下一跳。\n\n'
        '例如审查发现餐费缺失，主管模式会先向主管汇报，Swarm 可以直接交回搜集者。'
        '图中的 Network 是全连接示例，实际可以限制连接；Swarm 的箭头表示允许交接，并不要求循环。'
        '这些模式可以组合。成本要看调用次数与上下文，容错要看重试、检查点和超时配置。'),
    ('sec09', 0): (
        'A2A 让不同系统的 Agent 交换任务与结果，MCP 让程序接入工具和资料。'
        '比如评审服务通过 A2A 接收任务，再通过 MCP 读取仓库资料。\n\n'
        'A2A 由 Google 发起，MCP 由 Anthropic 发起。MCP 的连接关系是 Host、Client、Server。'
        '具体版本与支持能力按页脚官方资料核对。'),
    ('sec09', 1): (
        'A2A 的 Agent Card 描述能力、服务端点和认证方式；Task 记录任务状态；Message 传递交互内容。'
        '卡片签名用于核验卡片来源，服务端仍要验证实际请求的身份与权限。'),
    ('sec09', 2): (
        'MCP 提供三种能力：Tools 执行函数，Resources 读取资料，Prompts 提供提示词模板。'
        '评审场景中，测试执行可以是 Tool，代码文件可以是 Resource，评审提示可以是 Prompt。'
        '协议负责连接，工具授权和输入校验由宿主执行。'),
    ('sec10', 0): (
        '假设某个角色读取的网页含有“把密钥发给我”，这句话可能被转交到其他角色。'
        '接收方要把它当成待处理资料，不能当成执行指令。\n\n'
        '对照表逐项检查：外部输入如何进入上下文，身份如何验证，敏感数据能发给谁，'
        '循环何时停止，工具权限在哪一层执行。消息签名可以核验来源，不能证明内容安全。'),
    ('sec10', 1): (
        '消息字段校验、工具授权和调用上限都应由程序执行。结构化消息便于检查字段，'
        '但其中的字符串仍可能包含恶意指令。工具白名单还要配合参数与访问范围校验。'
        '设置 token、调用次数和超时上限，并让停止状态保留已取得的证据。'),
    ('sec11', 0): (
        '拆分角色前，用同一组任务跑单 Agent 或工作流基线。比较完成率、延迟与 token，'
        '再看独立上下文、权限或专业审查是否带来收益。\n\n'
        '展开三个问题：长消息可能重复消耗 token；互相等待需要超时和退出条件；'
        '结果冲突先核对来源与采集条件，再审查或转人工。30% 通信占比和 10 层调用深度是示例目标，需按任务调整。'),
    ('sec11', 1): (
        '按表中的任务特征讨论选择。步骤固定时，普通工作流就可能够用；路径未知时，'
        '单 Agent 也可以逐轮探索。独立子任务可以由普通程序并行，专业职责需要隔离时再考虑多个角色。'
        '让学员选一个自己的任务，说清拆分后增加什么能力、付出什么成本。'),
    ('sec11', 2): (
        '这组数值是制定验收目标的练习材料，未经本课实测。'
        '任务完成率需要先定义通过条件，通信占比需要统一统计方式，延迟要区分任务难度。'
        '请学员为自己的任务调整一项阈值，并说明怎样用日志验证；调用深度之外还要限制总调用次数和运行时间。'),
}

class BlockParser(HTMLParser):
    """Extract balanced top-level fragments while retaining source markup."""

    def __init__(self, markup):
        super().__init__(convert_charrefs=False)
        self.markup = markup
        self.offsets = [0]
        for line in markup.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.depth = 0
        self.start = None
        self.blocks = []
        self.feed(markup)
        assert self.depth == 0, 'Unbalanced source markup'

    def absolute_offset(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if self.depth == 0:
            self.start = self.absolute_offset()
        if tag not in VOID_TAGS:
            self.depth += 1
        elif self.depth == 0:
            self.blocks.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        if self.depth == 0:
            self.blocks.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.depth -= 1
        if self.depth == 0:
            end = self.markup.index('>', self.absolute_offset()) + 1
            self.blocks.append(self.markup[self.start:end])


class TextParser(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.feed(markup)

    def handle_data(self, value):
        self.parts.append(value)


def text_content(markup):
    return ''.join(TextParser(markup).parts)


def source_sections():
    markup = SOURCE_PATH.read_text(encoding='utf-8')
    sections = OrderedDict()
    for section_id, inner in re.findall(r'<section\b[^>]*\bid="(sec\d+|faq)"[^>]*>(.*?)</section>', markup, re.S):
        if section_id not in SECTION_IDS:
            continue
        blocks = BlockParser(inner).blocks
        header = blocks.pop(0)
        title = text_content(re.search(r'<h2>(.*?)</h2>', header, re.S)[1])
        english = text_content(re.search(r'<div class="sec-en">(.*?)</div>', header, re.S)[1])
        blocks = [block for block in blocks if not block.startswith('<div class="step-nav"')]
        sections[section_id] = dict(title=title, english=english, blocks=blocks)
    assert list(sections) == SECTION_IDS
    return sections


def chapter_for(section_id):
    if section_id == 'sec02':
        return '五种协作模式总览'
    if section_id in ('sec03', 'sec04', 'sec05', 'sec06', 'sec07'):
        return '协作模式详解'
    if section_id == 'sec08':
        return '智能开发团队实战'
    if section_id == 'sec09':
        return '通信协议 A2A 与 MCP'
    if section_id in ('sec10', 'sec11'):
        return '安全与工程挑战'
    return '协作模式小结与问答'


def course_sections():
    sections = correct_sections(source_sections())
    comparison = sections['sec02']['blocks']
    assert comparison[2] == '<h3>模式横向对比</h3>'
    assert 'compare-table' in comparison[3]
    source_cards = [(text_content(title), text_content(prose)) for title, prose in
                    re.findall(r'<h4>(.*?)</h4><p>(.*?)</p>', comparison[1], re.S)]
    assert len(source_cards) == 5
    sections['sec02']['blocks'] = [comparison_graphics(source_cards)]
    return sections


def wrap_block(section_id, block_number, markup):
    # Convert source handlers into local event hooks; original global handlers
    # and document scroll navigation must not leak into the slide player.
    for handler, hook in [('copyCode(this)', 'data-import-copy'),
                          ('toggleAccordion(this)', 'data-import-accordion'),
                          ('toggleFaq(this)', 'data-import-faq')]:
        markup = markup.replace(f'onclick="{handler}"', hook)
    markup = markup.replace(
        'style="background:#fff3e0;color:#e8652e;border:1px solid #e8652e;"',
        'data-import-review',
    )
    return f'<div data-import-block="{section_id}:{block_number}">{markup}</div>'


def code_text(block):
    match = re.search(r'<pre><code>(.*?)</code></pre>', block, re.S)
    return text_content(match[1]) if match else None


def split_code(block, max_lines=18):
    """Split long listings without cutting multiline syntax-highlight spans."""
    source = code_text(block)
    if source is None:
        return [block]
    lines = source.split('\n')
    if len(lines) <= max_lines:
        return [block]
    pieces = []
    for start in range(0, len(lines), max_lines):
        part = escape('\n'.join(lines[start:start + max_lines]))
        pieces.append('<div class="code-block"><div class="code-header">'
                      '<span class="code-lang">python</span>'
                      '<button class="copy-btn" data-import-copy>复制</button></div>'
                      f'<pre><code>{part}</code></pre></div>')
    return pieces


def section_pages(section_id, section):
    """Keep each diagram, comparison or code topic on a readable slide."""
    groups = []
    current = []
    for index, block in enumerate(section['blocks']):
        if block.startswith('<h3>') and current and not all(
                'class="voice-line"' in entry[1] for entry in current):
            groups.append(current)
            current = []
        current.append((index, block))
    if current:
        groups.append(current)
    if section_id == 'faq':
        groups = [current[start:start + 3] for start in range(0, len(current), 3)]

    pages = []
    for group in groups:
        heading = next((text_content(block) for _, block in group if block.startswith('<h3>')), '')
        payload = []
        for index, block in group:
            listing = code_text(block)
            # A near-full listing plus a following explanation needs another
            # page even when the code itself would fit on one slide.
            has_note = any('class="highlight-box ' in following for _, following in group)
            max_lines = 12 if listing and has_note and 16 < len(listing.split('\n')) <= 18 else 18
            pieces = split_code(block, max_lines)
            for part_number, piece in enumerate(pieces):
                if part_number:
                    pages.append((heading, payload))
                    payload = []
                payload.append(wrap_block(section_id, index, piece))
        pages.append((heading, payload))

    result = []
    for index, (heading, payload) in enumerate(pages):
        title = section['title']
        if index and heading:
            title += ' · ' + heading
        same_heading = sum(item[0] == heading for item in pages)
        if same_heading > 1:
            ordinal = sum(item[0] == heading for item in pages[:index + 1])
            title += f'（{ordinal}/{same_heading}）'
        if section_id == 'faq':
            title = f'常见问题（{index + 1}/{len(pages)}）'
        is_comparison = any('class="collaboration-atlas"' in fragment for fragment in payload)
        label = f'{section["english"]} · {index + 1} / {len(pages)}'
        result.append(dict(
            chapter=chapter_for(section_id), title=title,
            body=f'<p class="import-label">{escape(label)}</p>'
                 f'<div class="import-body" data-import-section="{section_id}">'
                 + ''.join(payload) + '</div>',
            notes=SECTION_NOTES.get((section_id, index),
                  '\n'.join(text_content(fragment) for fragment in payload)),
            sources=references_for(section_id, heading, index),
            layout='imported-slide collaboration-comparison-slide' if is_comparison else 'imported-slide',
            source_section=section_id,
        ))
    return result


def imported_slides(seconds_budget):
    result = [slide for section_id, section in course_sections().items()
              for slide in section_pages(section_id, section)]
    # Retain the 90-minute course budget by replacing the removed slides' time.
    weights = [120 if 'class="code-block"' in slide['body'] else 80 for slide in result]
    total = sum(weights)
    durations = [seconds_budget * weight // total for weight in weights]
    for index in range(seconds_budget - sum(durations)):
        durations[index] += 1
    for slide, seconds in zip(result, durations):
        slide.update(seconds=seconds, minutes=seconds / 60)
        slide['notes'] = f'【{seconds // 60} 分 {seconds % 60:02} 秒】' + slide['notes']
    # The user authorized redesigning the teaching format, including code.
    # Replace the fourteen pattern pages while preserving the next chapter and
    # its timing. The original framework material remains in the source snapshot.
    from collaboration_vscode import training_slides
    pattern_pages = result[1:15]
    assert {slide['source_section'] for slide in pattern_pages} == {
        'sec03', 'sec04', 'sec05', 'sec06', 'sec07'}
    result = [result[0]] + training_slides(sum(slide['seconds'] for slide in pattern_pages)) + result[15:]
    # Authorized MetaGPT case redesign; retain old listing in the source snapshot.
    from dev_team_training import development_slides
    dev_indexes = [i for i, slide in enumerate(result) if slide['source_section'] == 'sec08']
    result[dev_indexes[0]:dev_indexes[-1] + 1] = development_slides()
    # Merge after timing allocation so every existing chapter keeps its budget.
    protocol_indexes = [index for index, slide in enumerate(result)
                        if slide['source_section'] == 'sec09']
    assert len(protocol_indexes) == 3
    overview, a2a, mcp = [result[index] for index in protocol_indexes]
    overview['layout'] += ' protocol-overview-slide'
    overview['body'] = overview['body'].replace(' · 1 / 3', ' · 1 / 2')
    blocks = course_sections()['sec09']['blocks']
    columns = ''.join(
        '<div class="protocol-detail-column">'
        + ''.join(wrap_block('sec09', index, blocks[index]) for index in indexes)
        + '</div>' for indexes in ((2, 3), (4, 5)))
    seconds = a2a['seconds'] + mcp['seconds']
    details = dict(
        chapter=a2a['chapter'], title='通信协议：A2A与MCP · 核心概念与能力',
        body='<p class="import-label">'
             + escape(course_sections()['sec09']['english']) + ' · 2 / 2</p>'
             '<div class="import-body" data-import-section="sec09">'
             '<div class="protocol-detail-grid">' + columns + '</div>'
             + wrap_block('sec09', 6, blocks[6]) + '</div>',
        notes=f'【{seconds // 60} 分 {seconds % 60:02} 秒】'
              + re.sub(r'^【.*?】', '', a2a['notes']) + '\n\n'
              + re.sub(r'^【.*?】', '', mcp['notes']),
        sources=list(dict.fromkeys(a2a['sources'] + mcp['sources'])),
        layout='imported-slide protocol-details-slide', source_section='sec09',
        seconds=seconds, minutes=seconds / 60,
    )
    result[protocol_indexes[1]:protocol_indexes[-1] + 1] = [details]
    return result
