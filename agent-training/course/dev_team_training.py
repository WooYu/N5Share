"""MetaGPT development design and Review Agent lab; execution stays in VS Code."""
from html import escape

DEV_TEAM_SECONDS = 900
DEV_TEAM_SOURCES = {
    'meta_roles': ('MetaGPT · Role 与消息订阅', 'https://github.com/FoundationAgents/MetaGPT/blob/v0.8.2/metagpt/roles/role.py'),
    'meta_review': ('MetaGPT · 内置代码评审参考', 'https://github.com/FoundationAgents/MetaGPT/blob/v0.8.2/metagpt/actions/write_code_review.py'),
    'meta_team': ('MetaGPT · Team 与环境', 'https://github.com/FoundationAgents/MetaGPT/blob/v0.8.2/metagpt/team.py'),
}


def flow(*nodes):
    return '<div class="dev-flow">' + ''.join(f'<div><span>0{i}</span><b>{escape(title)}</b><p>{escape(detail)}</p></div>'
                                              for i, (title, detail) in enumerate(nodes, 1)) + '</div>'


def panels(left, right):
    return '<div class="dev-grid">' + ''.join('<div class="dev-panel"><h3>' + escape(title) + '</h3><ul>'
        + ''.join('<li>' + escape(item) + '</li>' for item in items) + '</ul></div>' for title, items in (left, right)) + '</div>'


def table(headers, rows):
    return '<table class="dev-table"><thead><tr>' + ''.join(f'<th>{escape(v)}</th>' for v in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join(f'<td>{escape(v)}</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'


def development_slides():
    result = []
    def add(title, lead, body, takeaway, notes, seconds, sources=('meta_roles', 'meta_team')):
        result.append(dict(chapter='智能开发团队实战', title=title,
            body='<p class="dev-lead">' + escape(lead) + '</p>' + body + '<p class="dev-takeaway">' + takeaway + '</p>',
            notes=notes, seconds=seconds, minutes=seconds / 60, sources=list(sources),
            source_section='sec08', layout='dev-team-slide'))
    add('实战案例：智能软件开发团队', '用 MetaGPT 组织开发团队，重点做一个能验证、能复审的 Review Agent。',
        flow(('需求', '任务看板与验收'), ('设计', '接口与产物依赖'), ('代码变更', '教学 PR 与模型修复'), ('评审交付', '证据、测试、人工决定'))
        + panels(('具体交付', ['新增任务、列表查询、修改状态', 'SQLite 保存，刷新后状态保留', '前端、后端、固定测试和启动说明']),
                 ('贯穿本章的问题', ['评审需要哪些上下文？', '怎样判断意见有真实证据？', '修复后怎样重新评审并验收？'])),
        '在 VS Code 中查看角色、工具和状态，再运行评审与修复。',
        (
        '本章做一个任务看板，重点检查 Review Agent 怎样读材料、定位问题和复审。首轮 PR 由讲师提供，用于复现缺陷。PM 与 Architect 用模型整理需求和设计，Reviewer 独立评审，开发角色根据意见和测试失败修复。\n\n'
        'MetaGPT 按 SOP 传递专业产物，角色由消息订阅触发。讲解时分别指出模型判断、程序检查和人工批准的位置。'
    ), 60)
    add('把前面的知识变成开发设计', '对照角色、状态和工具，找到对应的实现文件。',
        table(['前面学过', '本案例怎样设计', '实现位置'], [
            ['角色与上下文', 'PM、Architect、Developer、Reviewer、Tester', 'team.py · Role'],
            ['顺序与异常回路', '需求 → 设计 → PR → 评审 → 测试；失败退回', '订阅 + Host 门禁'],
            ['共享状态与消息', '产物引用、版本、问题、测试、预算', 'session.py · state.json'],
            ['工具调用与验收', '读 diff / 契约，执行固定测试，核验输出', 'tools.py · contracts.py'],
            ['记忆与恢复', '隔离本轮上下文；待审批材料落盘', 'rc.news · 人工审批入口'],
        ]), '模型负责判断与修复；程序负责工具权限、次数限制和交付条件。',
        (
        '用表格对照角色、上下文、工具、状态与协作。正常路径按产物依赖推进，异常回退由 Host 触发。MetaGPT 提供 Role、Action 和消息环境。\n\n'
        'ArtifactRole 只传入本轮 rc.news，旧版本消息保留用于审计。待审批材料会保存到文件，新进程可以提交人工决定；这份保存不支持在任意节点恢复整个团队。'
    ), 90)
    add('MetaGPT：用产物和订阅组织团队', '下一角色收到相应 Action 产生的消息，才开始行动。',
        flow(('PM → Architect', '需求契约与设计文档'), ('Developer', '候选代码与版本'), ('Reviewer', '问题证据与结论'), ('Tester → 人工', '固定验收与审批材料'))
        + panels(('框架中的对应关系', ['Role：职责与本轮输入', 'Action：产生结果或执行检查', '_watch：订阅上游行动的消息']),
                 ('异常回路由 Host 触发', ['评审或测试失败 → FixRequested', '开发修复 → RepairCode 消息', 'Reviewer 订阅修复，再做新评审'])),
        '本例自定义 ReviewCode Action；内置 WriteCodeReview 用作参考。',
        (
        '打开 team.py，查看 build_team、_watch 和 Message.cause_by。Reviewer 订阅 PrepareChange 与 RepairCode，Tester 订阅 ReviewCode；Host 把 FixRequested 发给修复角色。\n\n'
        '首轮导入与失败修复使用同一开发职责的两个单 Action 实例。自定义 Action 调用已有模型网关，MetaGPT 内部客户端不发请求。'
    ), 75)
    add('Review Agent 设计①：先定义输入契约', '除 diff 外，评审还需要相关代码、需求和验证材料。',
        table(['输入', '本例材料', '用来回答'], [
            ['变更范围', 'base / head 摘要 + 统一 diff', '哪些代码发生了变化？'],
            ['完整相关代码', 'board.py 原始行号 + 前端调用方', '行为、依赖与边界是什么？'],
            ['需求契约', '状态只允许 todo / doing / done', '什么情况算真实缺陷？'],
            ['验证证据', '固定测试源码 + 本轮实际输出', '结论怎样复现？'],
            ['上下文清单', '已读取、缺失、截断与当前版本', '还缺什么？能否完成评审？'],
        ]), '缺失或截断 → needs_context；未检查不能写成“通过”。',
        (
        '打开 collect_context 和 context-0.json，核对 diff、完整文件、调用方、需求与测试。base/head 是内容哈希；diff 由实际文件生成，定位行号来自完整文件。\n\n'
        '本例固定收集四份材料，incomplete 情景故意省略需求。接入实际 PR 时，需要从确定的 commit 读取变更，按调用关系补充资料，并记录缺失、截断和未覆盖范围。'
    ), 105)
    add('Review Agent 设计②：工具、证据与结构化意见', '请求检查工具，读取实际结果，再输出可定位的问题。',
        flow(('读取 diff', '核对变更与版本'), ('补齐上下文', '契约、代码、调用方'), ('执行固定测试', '真实错误与退出码'), ('输出并校验', '问题、定位、证据'))
        + panels(('每条问题必须包含', ['严重度、文件、原始行号', '代码原文、触发条件与影响', '修复建议及验证测试名']),
                 ('教学 PR 中的真实问题', ['移除校验后 deleted 可以写入', '正常界面操作可能掩盖接口缺陷', '验证拒绝非法状态且数据未变'])),
        '先核对格式、文件和证据，再用测试与人工判断结论。',
        (
        'ReviewCode.run 先让模型请求三个白名单工具，由宿主执行。第二次请求带上实际 observations，再生成评审结论。validate_review 检查字段、严重度、文件、行号和原文。\n\n'
        '教学缺陷是移除状态校验后，deleted 能写入数据库；test_invalid_status_is_rejected 可以复现。程序校验能确认引用存在，问题是否成立还要看契约、测试和人工判断。\n\n'
        '本课 high/medium 阻断交付，low 作为建议。只报告本次变更新增的缺陷，风格和无关重构不作阻断；代码注释按待审资料处理。'
    ), 150, ('meta_review', 'meta_roles'))
    add('修复、复审与人工门禁怎样落到代码', '任何一次代码变化，都必须重新获得评审和测试证据。',
        flow(('退回', '问题 + 真实测试输出'), ('开发修复', '只修改 board.py'), ('旧结果失效', '清空旧评审与测试'), ('重新验收', '新评审 + 固定测试'))
        + panels(('交付条件', ['代码与验收材料版本匹配', '评审通过，固定测试通过', '人工批准当前版本']),
                 ('失败时怎样结束', ['上下文不足 → 补充材料', '最多 2 轮修复，耗尽转人工', '模型失败、超时或过期 → 停止'])),
        '待审批材料落盘；新进程可批准／退回，批准前核对版本并重跑验收。',
        (
        'RepairCode 只接收 board.py 源码，编译通过后写入并清空旧评审与测试。固定测试由讲师维护，开发角色不能修改。delivery_gate 核对当前版本、评审和测试。\n\n'
        'max_repairs=2、max_model_calls=12 限制修复轮数和模型请求。人工决定要附 revision，过期版本和重复审批会被拒绝。这里保存与核对审批材料，不执行 Git 合并或部署，也不恢复整个团队。'
    ), 120)
    add('切换 VS Code：运行评审、修复与复审', '打开本次输入、评审和测试文件，检查修复是否有效。',
        table(['顺序', '打开的位置', '观察与操作'], [
            ['1 · 设计', 'team.py / actions.py', 'Role、Action、_watch 和当前消息'],
            ['2 · 输入', 'context-0.json / candidate/board.py', '核对 diff、契约、行号与版本'],
            ['3 · 评审', 'review-0.json / tests-0.json', '问题定位与真实失败，预测修复'],
            ['4 · 复审', 'review-1.json / tests-1.json', '比较版本、意见和重跑的测试'],
            ['5 · 交付', 'state.json / serve_board.py', '显式批准，运行看板操作验收'],
        ]), '<a href="docs/dev-team-demo-guide.md" target="_blank">演示手卡 ↗</a> · VS Code 选择“开发团队 · Review 与修复”按 F5。',
        (
        '【4分30秒】课前确认独立环境和模型连接。F5 运行 buggy，每个 Action 后可按 Enter 继续。把本次输出目录加入 VS Code，读取 context、diff、tests-0 和 review-0，让学员预测修复。\n\n'
        '继续查看模型修改、review-1 与 tests-1。状态到 waiting_approval 后批准当前 revision，再启动 serve_board，新增任务、修改状态并刷新，检查是否持久保存。\n\n'
        '另用 clean、incomplete 和 max-repairs=0 展示无缺陷、缺资料和停止出口。模型可能失败或超限，按本次状态解释；展示历史产物时标明是回放。'
    ), 270)
    add('接入团队的 PR 流程', '用历史 PR 检查误报、漏报和问题定位，再决定阻断规则。',
        panels(('先建立评估样本', ['有缺陷、无缺陷、上下文不足', '检查误报、漏报和定位准确性', '用人工结论校准阻断等级']),
               ('再接入实际研发流程', ['固定 PR 版本，按依赖收集材料', '结果去重，修复后重新评审', '让人确认是否阻断合并'])),
        '跨系统协作时，还要定义身份、消息与工具接口。',
        (
        '用历史 PR 盲测，人工标注问题，记录变更覆盖、误报、漏报、定位和可复现比例，再决定阻断等级。意见数量不能说明评审质量。\n\n'
        '本例还没有大型仓库检索、CI 鉴权或自动 PR 评论。接入团队流程前，需要用实际任务验证这些能力和评审准确率。'
    ), 30)
    assert sum(s['seconds'] for s in result) == DEV_TEAM_SECONDS
    return result
