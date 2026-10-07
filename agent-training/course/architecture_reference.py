"""Architecture map, course examples and editable vector illustrations."""
from html import escape
from architecture_diagrams import diagram as vector_diagram, tool_marks


COPY = [
    dict(name='单 Agent 架构', english='(Single Agent)',
         subtitle='由一个 Agent 判断下一步并调用工具',
         flow='用户输入 → LLM → 工具调用 → 输出',
         features=['一个角色负责决策', '可调用工具、API 和数据库', '可保存会话状态'],
         strengths=['实现简单', '角色间通信少'],
         problems=['复杂任务会增加推理轮次', '无关信息可能干扰判断', '上下文长度有限'],
         scenes=['Copilot', 'ChatGPT', '简单自动化助手']),
    dict(name='ReAct 架构', english='（推理 + 行动）',
         subtitle='根据工具返回的结果决定下一次行动',
         flow='Thought（思考）→ Action（调用工具）→ Observation（结果）→ 继续思考...',
         features=['判断、行动、观察交替进行', '根据结果选择工具'],
         strengths=['适合反馈驱动的探索'],
         problems=['调用与延迟增加', '可能跑偏或无进展', '需限制轮次并校验结果'],
         scenes=['复杂问答', '多步骤任务', '探索阶段']),
    dict(name='Plan & Execute 架构', english='（规划执行）',
         subtitle='先拆分任务，再按计划执行和检查',
         flow='Planner（规划）→ Executor（执行）；1. 步骤 1；2. 步骤 2；3. 步骤 3；...；执行步骤 1；执行步骤 2；执行步骤 3；...',
         features=['生成计划后逐步执行', '用反馈修订剩余步骤'],
         strengths=['任务依赖清楚', '便于检查执行进度'],
         problems=['初始计划可能有遗漏', '条件变化时需反馈与重规划'],
         scenes=['代码生成', '项目自动化', '长流程任务']),
    dict(name='多 Agent 架构', english='(Multi-Agent)',
         subtitle='多个角色分别处理任务，再交换结果',
         flow='Orchestrator → Agent A / Agent B / Agent C / ...；Planner / Coder / Reviewer / Tool Agent',
         features=['角色使用各自的上下文', '按职责配置工具和产物'],
         strengths=['可单独检查各角色结果', '便于调整角色分工'],
         problems=['成本高', '协调复杂'],
         scenes=['团队协作', '复杂项目', '企业级应用']),
    dict(name='Router + Skill 架构', english='',
         subtitle='先识别意图，再加载适合的技能',
         flow='用户输入 → Intent Router（意图识别）→ Skill A / Skill B / Skill C → 执行 → 输出结果',
         features=['路由规则可单独测试', '按需加载技能', '可缓存常用资料', '可统计路由命中率'],
         problems=['Skill 设计成本高', '命中冲突', '协调复杂'],
         scenes=['Copilot', 'AI Coding', '技能系统'],
         footer='Skill 包含处理步骤、可执行能力与参考资料（Reference）'),
    dict(name='Blackboard 架构', english='（黑板系统）',
         subtitle='多 Agent 共享状态，通过状态驱动执行',
         flow='Blackboard（共享状态）↔ Agent A / Agent B / Agent C',
         features=['角色读取共享状态', '资料齐备后触发相应角色', '需要定义就绪条件'],
         problems=['状态管理复杂', '不易追溯问题'],
         representatives=['LangGraph', '工作流引擎', '分布式系统']),
    dict(name='Graph / Workflow 架构', english='（图与工作流）',
         subtitle='显式编排依赖、分支、并行与反馈回路',
         flow='Node A → Node B → Node C → Node D；条件判断 → Node E / Node F',
         features=['显式定义节点、分支与并行', '可记录和调试执行路径', '重试与恢复需要配置'],
         strengths=['便于测试路径', '可逐节点调试', '可组织长流程'], strength_title='优势',
         scenes=['企业流程', '长流程任务', '生产环境'],
         tools=['LangGraph', 'Temporal (Workflow engine)', 'Airflow (Workflow scheduler)', 'n8n (Workflow automation)', 'Prefect']),
]

PATH_NAMES = ['单 Agent', 'ReAct', 'Plan & Execute', '多 Agent', 'Router + Skill', 'Blackboard', 'Graph / Workflow']
PATH_CAPTIONS = [('少量工具', '单角色处理'), ('逐轮查询', '根据结果调整'),
                 ('任务有依赖', '按计划执行'), ('职责独立', '交换结果'),
                 ('多类请求', '加载相应技能'), ('共享资料', '就绪后执行'), ('流程明确', '按节点执行')]

def bullets(lines):
    return '<ul>' + ''.join(f'<li>{escape(line)}</li>' for line in lines) + '</ul>'


def section(title, lines, css_class):
    return f'<div class="{css_class}"><strong>{title}</strong>{bullets(lines)}</div>'


def tags(title, lines):
    return (f'<div class="architecture-scenes"><strong>{title}</strong><div class="architecture-tags">'
            + ''.join(f'<span>{escape(line)}</span>' for line in lines) + '</div></div>')


def architecture_overview():
    tiles = ''.join(
        f'<article class="architecture-tile architecture-{index}">'
        f'<header><span class="architecture-number">{index}</span><h3>{escape(item["name"])}</h3>'
        + f'</header><p>{escape(item["subtitle"])}</p>{vector_diagram(index, "overview")}</article>'
        for index, item in enumerate(COPY, 1))
    path = ''.join(f'<li class="architecture-{index}"><b>{index}</b><span>{escape(name)}</span>'
                   f'<small>{PATH_CAPTIONS[index - 1][0]}<br>{PATH_CAPTIONS[index - 1][1]}</small></li>'
                   for index, name in enumerate(PATH_NAMES, 1))
    principles = ('<aside class="architecture-keypoints"><strong>怎样看这张图</strong><ul>'
                  '<li>架构没有统一标准，选择取决于场景复杂度与控制要求</li>'
                  '<li>角色组织、决策策略、路由与编排是不同维度，可以组合</li>'
                  '<li>同一任务可以用不同方式实现，先比较所需控制与开销</li></ul></aside>')
    return ('<p class="architecture-intro">用周末出游比较七种机制，远程诊断作为课后参考</p>'
            f'{principles}<div class="architecture-map">{tiles}</div>'
            '<div class="architecture-roadmap"><strong>七种架构并列对照 · 按任务组合，无统一升级顺序</strong>'
            f'<ol class="architecture-path" aria-label="七种架构并列对照">{path}</ol></div>'
            '<p class="architecture-caveat">第 6 至 12 页依次演示①至⑦。课后诊断示例用图编排组合角色分工与共享状态。</p>')


def architecture_details(start, end):
    cards = []
    for index in range(start, end + 1):
        item = COPY[index - 1]
        drawing = vector_diagram(index, 'detail')
        header = (f'<header><span class="architecture-number">{index}</span><div><h3>{escape(item["name"])}</h3>'
                  + (f'<small>{escape(item["english"])}</small>' if item['english'] else '')
                  + '</div></header>')
        features = section('特点', item['features'], 'architecture-facts')
        problems = section('问题', item['problems'], 'architecture-limits') if 'problems' in item else ''
        strengths = section(item.get('strength_title', '优点'), item['strengths'], 'architecture-strengths') if 'strengths' in item else ''
        scenes = tags('适用场景', item['scenes']) if 'scenes' in item else ''
        if index == 5:
            body = (f'<div class="architecture-router-body">{features}{drawing}</div>'
                    f'<div class="architecture-router-bottom">{scenes}{problems}</div>'
                    f'<p class="architecture-skill-footer">{escape(item["footer"])}</p>')
        elif index == 6:
            body = (drawing + f'<div class="architecture-blackboard-facts">{features}{problems}</div>'
                    + tags('代表', item['representatives']))
        elif index == 7:
            body = (drawing + f'<div class="architecture-graph-facts">{features}{strengths}</div>' + scenes
                    + '<div class="architecture-tools"><strong>代表工具 / 框架</strong>'
                    + tool_marks() + '</div>')
        else:
            body = (drawing + features
                    + f'<div class="architecture-tradeoff-pair">{strengths}{problems}</div>' + scenes)
        cards.append(f'<article class="architecture-card architecture-{index}">{header}'
                     f'<p class="architecture-subtitle">{escape(item["subtitle"])}</p>{body}</article>')
    return f'<div class="architecture-cards architecture-columns-{len(cards)}">' + ''.join(cards) + '</div>'
