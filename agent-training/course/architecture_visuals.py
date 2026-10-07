"""Large, self-contained diagrams for the seven architecture walkthroughs."""
from html import escape


# A single fixed canvas keeps projection and small-screen scaling predictable.
# Nodes: id, x, y, width, title, responsibility. Edges carry stable playback ids.
DIAGRAMS = {
    1: dict(nodes=[
        ('input', 20, 125, 170, '用户任务', '目标与约束'),
        ('agent', 310, 125, 225, '单 Agent / LLM', '理解 · 调用 · 汇总'),
        ('rag', 675, 20, 230, 'RAG / 文档库', '检索规则 · 带引用'),
        ('tool', 675, 230, 230, '工具 / 宿主程序', '校验参数 · 查天气与费用'),
        ('output', 1050, 125, 180, '回答', '汇合规则与事实')], edges=[
        ('input-agent', 'M190 165 H310', 245, 150, '任务'),
        ('agent-rag', 'M535 145 H585 V50 H675', 610, 34, '检索请求'),
        ('rag-agent', 'M675 77 H615 V177 H535', 619, 197, '文档引用'),
        ('agent-tool', 'M535 183 H585 V260 H675', 622, 248, '工具请求'),
        ('tool-agent', 'M675 290 H555 V204 H500', 581, 313, '工具返回'),
        ('agent-output', 'M535 165 H1050', 940, 149, '有依据的回答')]),
    2: dict(nodes=[
        ('input', 20, 55, 170, '用户任务', '天气 + 预算约束'),
        ('decision', 290, 55, 200, '决策 / Agent', '依据已有观察选行动'),
        ('tool', 630, 55, 210, '行动 / Tool', '查询天气或计算费用'),
        ('observation', 630, 225, 210, '观察 / 返回值', '事实结果进入上下文'),
        ('output', 1040, 55, 190, '结束', '满足条件 / 无解停止')], edges=[
        ('input-decision', 'M190 95 H290', 240, 77, '输入'),
        ('decision-tool', 'M490 95 H630', 560, 77, '选择下一工具'),
        ('tool-observation', 'M735 135 V225', 830, 188, '宿主执行并返回'),
        ('observation-decision', 'M630 265 H390 V135', 452, 247, '观察改变下一轮决策'),
        ('decision-output', 'M490 65 V20 H1135 V55', 845, 15, '检查结束条件')]),
    3: dict(nodes=[
        ('input', 20, 70, 150, '用户任务', '目标与约束'),
        ('planner', 250, 70, 195, 'Planner', '拆步骤 · 定依赖'),
        ('executor', 555, 70, 195, 'Executor', '工具执行 · 交付草稿'),
        ('validate', 850, 70, 170, '验收', '完整费用 · 天气'),
        ('reflection', 555, 245, 230, 'Reflexion / 反馈', '失败原因 → 修订动作'),
        ('output', 1100, 70, 130, '结果', '建议 / 无解')], edges=[
        ('input-planner', 'M170 110 H250', 210, 91, '输入'),
        ('planner-executor', 'M445 110 H555', 500, 91, '计划 v1 / v2'),
        ('executor-validate', 'M750 110 H850', 800, 91, '提交'),
        ('validate-output', 'M1020 110 H1100', 1060, 91, '通过 / 无解'),
        ('validate-reflection', 'M935 150 V285 H785', 975, 230, '首次失败'),
        ('reflection-planner', 'M555 285 H347 V150', 385, 266, '反馈修订计划')]),
    4: dict(nodes=[
        ('input', 20, 125, 160, '用户任务', '统一约束'),
        ('supervisor', 275, 125, 190, '主管 Agent', '分派 · 等待交付'),
        ('weather', 575, 25, 230, '天气 Agent', '天气与场馆适配'),
        ('cost', 575, 225, 230, '费用 Agent', '三项费用与预算'),
        ('merge', 925, 125, 165, '主管汇总', '两份结果取交集'),
        ('output', 1150, 125, 100, '回答', '留引用')], edges=[
        ('input-supervisor', 'M180 165 H275', 228, 149, '输入'),
        ('supervisor-weather', 'M465 145 H510 V65 H575', 510, 47, '任务 A'),
        ('supervisor-cost', 'M465 185 H510 V265 H575', 510, 292, '任务 B'),
        ('weather-merge', 'M805 65 H867 V145 H925', 870, 47, '天气消息'),
        ('cost-merge', 'M805 265 H867 V185 H925', 870, 292, '费用消息'),
        ('merge-output', 'M1090 165 H1150', 1120, 149, '交付')]),
    5: dict(nodes=[
        ('input', 20, 125, 160, '用户输入', '出游 / 费用 / 模糊'),
        ('router', 270, 125, 185, 'Intent Router', '识别意图 · 选技能'),
        ('outing_plan', 565, 20, 245, '出游 Skill', '流程 + D01 / D02'),
        ('budget_check', 565, 130, 245, '费用 Skill', '流程 + D02'),
        ('clarify', 565, 245, 245, '澄清出口', '意图不足先问清'),
        ('execute', 920, 75, 170, '执行技能', '按技能边界调工具'),
        ('output', 1150, 75, 100, '输出', '按约定')], edges=[
        ('input-router', 'M180 165 H270', 225, 149, '输入'),
        ('router-outing_plan', 'M455 145 H505 V60 H565', 510, 43, '出游'),
        ('router-budget_check', 'M455 165 H565', 510, 150, '费用'),
        ('router-clarify', 'M455 185 H505 V285 H565', 510, 312, '未知'),
        ('outing_plan-execute', 'M810 60 H867 V100 H920', 866, 43, '按需加载'),
        ('budget_check-execute', 'M810 170 H867 V135 H920', 867, 199, '按需加载'),
        ('execute-output', 'M1090 115 H1150', 1120, 98, '交付')]),
    6: dict(nodes=[
        ('weather', 45, 35, 230, '天气角色', '读取目标 · 发布天气'),
        ('catalog', 45, 235, 230, '场馆角色', '发布场馆 · 解锁费用'),
        ('board', 475, 120, 310, '共享黑板 + 调度器', '字段 · 版本 · 就绪条件'),
        ('cost', 995, 35, 230, '费用角色', '场馆名单齐备才能触发'),
        ('summary', 995, 235, 230, '汇总角色', '证据齐备才能触发')], edges=[
        ('board-weather', 'M475 140 H365 V55 H275', 380, 38, '缺天气 → 触发'),
        ('weather-board', 'M275 95 H325 V167 H475', 351, 189, '发布天气'),
        ('board-catalog', 'M475 185 H365 V255 H275', 367, 248, '缺场馆名单 → 触发'),
        ('catalog-board', 'M275 295 H415 V202 H500', 392, 318, '发布场馆名单'),
        ('board-cost', 'M785 140 H885 V55 H995', 879, 38, '场馆名单齐备 → 触发'),
        ('cost-board', 'M995 95 H925 V167 H785', 900, 189, '发布费用'),
        ('board-summary', 'M785 185 H885 V255 H995', 891, 248, '证据齐备 → 触发'),
        ('summary-board', 'M995 295 H835 V202 H760', 872, 318, '发布结论')]),
    7: dict(nodes=[
        ('START', 10, 125, 90, 'START', '入口'),
        ('weather', 150, 125, 135, 'weather', '读天气'),
        ('catalog', 335, 125, 135, '场馆工具', '查场馆名单'),
        ('indoor_filter', 525, 20, 180, 'indoor_filter', '只保留室内'),
        ('all_places', 525, 235, 180, 'all_places', '保留全部场馆'),
        ('cost', 755, 125, 110, 'cost', '完整费用'),
        ('validate', 915, 125, 130, 'validate', '验收预算'),
        ('recommend', 1100, 20, 150, 'recommend', '建议出口'),
        ('no_solution', 1100, 235, 150, 'no_solution', '无解出口'),
        ('END', 1125, 125, 100, 'END', '有限结束')], edges=[
        ('START-weather', 'M100 165 H150', 125, 146, ''),
        ('weather-catalog', 'M285 165 H335', 310, 146, ''),
        ('catalog-indoor_filter', 'M470 145 H495 V60 H525', 492, 34, 'rain'),
        ('catalog-all_places', 'M470 185 H495 V275 H525', 492, 310, 'sun'),
        ('indoor_filter-cost', 'M705 60 H735 V145 H755', 730, 42, ''),
        ('all_places-cost', 'M705 275 H735 V185 H755', 730, 307, ''),
        ('cost-validate', 'M865 165 H915', 890, 146, ''),
        ('validate-recommend', 'M1045 145 H1070 V60 H1100', 1068, 34, '通过'),
        ('validate-no_solution', 'M1045 185 H1070 V275 H1100', 1068, 310, '超额'),
        ('recommend-END', 'M1175 100 V125', 1235, 114, ''),
        ('no_solution-END', 'M1175 235 V205', 1235, 222, '')]),
}


LIMITATION_MARKS = {
    1: dict(nodes=['agent', 'rag', 'tool'], edges=['rag-agent', 'tool-agent'], text='规则缺少当天事实；检索与工具出错会影响同一 Agent 的回答。'),
    2: dict(nodes=['decision', 'observation'], edges=['observation-decision'], text='每次观察后再调用：往返越多，调用与等待越多；需限制循环。'),
    3: dict(nodes=['validate', 'reflection'], edges=['validate-reflection', 'reflection-planner'], text='要求变化后要重新检查：修订计划增加步骤，仍需事实验收。'),
    4: dict(nodes=['merge'], edges=['weather-merge', 'cost-merge'], text='主管要等两份消息并合并：增加协调开销；本例角色串行执行。'),
    5: dict(nodes=['router', 'clarify'], edges=['router-clarify'], text='“帮我看看”无法选技能：先澄清；本例关键词路由有识别边界。'),
    6: dict(nodes=['board', 'cost', 'summary'], edges=['board-cost', 'board-summary'], text='资料不齐，费用 / 汇总角色只能等待；版本要管理，本例未演示并发冲突。'),
    7: dict(nodes=['catalog', 'validate'], edges=['catalog-indoor_filter', 'catalog-all_places', 'validate-no_solution'], text='晴雨与预算出口都预先写好：新增路径要改图，本例未实现恢复。'),
}


def architecture_canvas(number, label):
    diagram = DIAGRAMS[number]
    marker = f'walk-arrow-{number}'
    mark = LIMITATION_MARKS[number]
    parts = [f'<svg class="architecture-canvas" viewBox="0 0 1260 335" role="img" aria-label="{escape(label)}的组件、信息流与局限标记">',
             f'<desc>{escape(mark["text"])}</desc>',
             f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="context-stroke"/></marker></defs>']
    for key, path, x, y, text in diagram['edges']:
        limitation = ' data-vis-limitation="edge"' if key in mark['edges'] else ''
        parts.append(f'<g class="walk-edge" data-vis-edge="{key}"{limitation}><path d="{path}" marker-end="url(#{marker})"/>')
        if text:
            parts.append(f'<text x="{x}" y="{y}" text-anchor="middle">{escape(text)}</text>')
        parts.append('</g>')
    for key, x, y, width, title, subtitle in diagram['nodes']:
        limitation = ' data-vis-limitation="node"' if key in mark['nodes'] else ''
        parts.append(f'<g class="walk-node" data-vis-node="{key}"{limitation} transform="translate({x} {y})">'
                     f'<rect width="{width}" height="80" rx="8"/>'
                     f'<text class="walk-title" x="{width / 2}" y="31" text-anchor="middle">{escape(title)}</text>'
                     f'<text class="walk-subtitle" x="{width / 2}" y="58" text-anchor="middle">{escape(subtitle)}</text>')
        if limitation:
            parts.append(f'<g class="walk-limit-pin"><title>局限位置：{escape(mark["text"])}</title>'
                         f'<circle cx="{width - 8}" cy="5" r="11"/><text x="{width - 8}" y="11" text-anchor="middle">!</text></g>')
        parts.append('</g>')
    parts.append('</svg>')
    return ''.join(parts)


WALKTHROUGH_COPY = {
    1: ('关键事件：先想到公园，查到下雨后改建议', '谁处理下一步？同一个 Agent。', '同一个角色用规则和事实修正建议，协调成本较低。', '检索质量与工具可靠性影响结果；复杂上下文会集中在一个角色。', '资料问答 + 少量业务工具'),
    2: ('关键事件：自然馆 310 元太贵，改查博物馆 210 元', '谁处理下一步？Agent 根据最新观察决定。', '查到超预算后再换候选，满足要求就停止查询。', '多轮调用增加延迟；要限制重复查询、次数和总用时。', '排障、搜索与探索性查询'),
    3: ('关键事件：执行途中，用户把预算从 300 元降到 200 元', '谁处理下一步？规划器根据新要求修订剩余步骤。', '要求变化时可重规划，复用已查天气、名单和价格。', '改计划与再次验收增加步骤；重规划不能改变客观价格。', '有依赖、执行中可能改要求的任务'),
    4: ('关键事件：天气角色选自然馆，费用角色选公园', '谁处理下一步？主管分派，必要结果齐备后汇总。', '各角色独立负责，主管能对照不同证据作完整判断。', '局部建议不能直接交付；消息等待和合并增加协调成本。', '需要独立职责、上下文或权限的任务'),
    5: ('关键事件：用户从“安排出游”改成“只算费用”', '谁处理下一步？Router 选技能，技能规定执行流程。', '需求变了就切换处理流程，费用技能省去天气查询。', '模糊、多意图与冲突需要处理；路由和技能版本都要维护。', '多类请求共用入口、标准流程可复用'),
    6: ('关键事件：费用角色先等待，场馆名单写入后才开始', '谁处理下一步？调度器检查黑板上的就绪条件。', '资料共享；名单发布后自动触发费用，减少逐条分派。', '缺资料会等待；还要管理版本、重复触发和并发冲突。', '角色围绕共享证据逐步补齐结果'),
    7: ('关键事件：现有场馆都不符合，沿预设无解分支结束', '谁处理下一步？预先定义的边和条件代码。', '没有合适方案也有明确出口，路径可追踪、可测试。', '未预设的情况需改流程；恢复还需检查点、幂等与持久化。', '流程明确、需要审计和稳定出口的任务'),
}


def walkthrough_tradeoffs(number):
    _, _, advantage, limitation, use = WALKTHROUGH_COPY[number]
    return ('<aside class="walk-tradeoffs" aria-label="框架优势、局限与适用场景">'
            f'<div class="walk-advantage"><b>优势</b><p>{escape(advantage)}</p></div>'
            f'<div class="walk-limitation"><b>局限</b><p>{escape(limitation)}</p></div>'
            f'<div class="walk-use"><b>适用场景</b><p>{escape(use)}</p></div></aside>')
