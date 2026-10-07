"""Framework profiles with capabilities, use cases, official links and images."""
from html import escape

CHAPTER = '框架选型与上手'
FRAMEWORK_SOURCES = {
    'maf': ('Microsoft Agent Framework · 官方仓库', 'https://github.com/microsoft/agent-framework'),
    'maf_samples': ('MAF · 完整示例', 'https://github.com/microsoft/agent-framework/tree/main/python/samples'),
}


def slide(title, body, notes, seconds, sources, theme=''):
    return dict(chapter=CHAPTER, title=title, body=body, notes=notes,
                seconds=seconds, minutes=seconds / 60, sources=sources,
                layout='framework-training-slide ' + theme)


def profile(number, title, lead, capabilities, scenarios, image, alt, caption,
            image_source, guide, example, example_label, notes, seconds, sources, theme):
    features = ''.join(f'<li><b>{escape(name)}</b><span>{escape(detail)}</span></li>'
                       for name, detail in capabilities)
    cases = ''.join(f'<span>{escape(case)}</span>' for case in scenarios)
    body = (
        f'<p class="fw-lead">{escape(lead)}</p><div class="fw-profile"><div class="fw-facts">'
        f'<section class="fw-capabilities"><h3><span>{number:02}</span> 具备哪些能力</h3><ul>{features}</ul></section>'
        f'<section class="fw-usecases"><h3>适用场景</h3><div class="fw-tags">{cases}</div></section></div>'
        '<figure class="fw-preview"><div class="fw-preview-title"><b>效果图</b><span>点击查看原图 ↗</span></div>'
        f'<a class="fw-image-link" href="{image}" target="_blank" rel="noopener" aria-label="查看{escape(title)}效果原图">'
        f'<img src="{image}" alt="{escape(alt)}" width="1400" height="900"></a>'
        f'<figcaption>{escape(caption)} <a href="{image_source}" target="_blank" rel="noopener">官方图片来源 ↗</a></figcaption></figure></div>'
        '<nav class="fw-resources" aria-label="官方集成指南和使用示例">'
        f'<a href="{guide}" target="_blank" rel="noopener"><span>官方集成指南</span><b>安装 · 配置 · 快速开始 ↗</b></a>'
        f'<a href="{example}" target="_blank" rel="noopener"><span>官方使用示例</span><b>{escape(example_label)} ↗</b></a></nav>'
    )
    return slide(title, body, notes, seconds, sources, theme)


def framework_slides():
    # The assembler folds this bridge's minute into the first profile.
    result = [slide('从协作模式到开发框架', '',
                    '【1分钟】前面的五种协作模式用 LangGraph 实现。现在对照三种框架，看看各自提供哪些能力、适合哪些任务。',
                    60, ['maf', 'graph', 'meta'])]
    result.append(profile(
        1, 'Microsoft Agent Framework：构建 Agent 与工作流',
        'Python / .NET 开发框架：连接模型、调用工具、编排协作，并观察执行过程。',
        [('模型与工具接入', '连接不同模型，注册业务函数供 Agent 调用。'),
         ('多 Agent 工作流', '提供顺序、并发、交接等编排方式，支持流式事件。'),
         ('执行控制', '配置工作流检查点、暂停审核与恢复执行。'),
         ('调试与可观测性', 'DevUI 查看事件与工具调用，支持执行追踪。')],
        ['.NET / Python 业务接入', '客服与查询助手', '工作流与执行追踪'],
        'assets/frameworks/maf-devui.png',
        'MAF 官方 DevUI：上方为工作流执行状态，下方为天气助手对话与工具调用事件。',
        '官方 DevUI 示例：上方查看工作流节点，下方查看天气助手与工具调用事件。DevUI 为开发调试工具。',
        'https://github.com/microsoft/agent-framework/tree/main/python/packages/devui',
        'https://learn.microsoft.com/agent-framework/tutorials/quick-start',
        'https://github.com/microsoft/agent-framework/tree/main/python/samples',
        'Agent · 工具 · Workflow 完整源码',
        (
        '【6分钟】图来自官方 DevUI README：上方是邮件处理工作流，下方是 WeatherAgent。点击图片可看离线原图。用图中的节点与工具事件说明模型接入、工作流和执行追踪。\n\n'
        'Quick Start 介绍安装、模型配置与首个 Agent；Python samples 有工具和工作流示例，.NET 团队可看 dotnet/samples。检查点与人工介入需要配置和验证。DevUI 用于开发调试。'
    ),
        360, ['maf', 'maf_samples'], 'fw-maf'))
    result.append(profile(
        2, 'LangGraph：可控制、可恢复的 Agent 执行',
        'Python / JavaScript / TypeScript：用状态图组织执行，适合有分支、暂停与恢复的任务。',
        [('状态与流程编排', '定义共享状态、执行节点、条件路由与并行分支。'),
         ('检查点与持久执行', '配置状态存储，支持长任务的恢复、历史检查与重放。'),
         ('人工介入', '通过 interrupt 暂停，接收人工输入后继续执行。'),
         ('记忆与调试', '会话状态与长期记忆；用 Studio 查看图与运行。')],
        ['工单补资料与审批', '多轮交互与长任务', '状态调试与排错'],
        'assets/frameworks/langgraph-studio.png',
        'LangChain 官方 Studio 界面，展示 Agent 图结构、输入区域与运行入口。',
        '官方 Studio 示例：图结构、输入与运行入口；图中尚未提交任务。Studio 属于 LangSmith 工具。',
        'https://blog.langchain.com/langgraph-studio-the-first-agent-ide/',
        'https://docs.langchain.com/oss/python/langgraph/quickstart',
        'https://docs.langchain.com/oss/python/langgraph/interrupts',
        '人工暂停与恢复 · 完整示例',
        (
        '【6分钟】沿用前面的五模式代码，解释状态、节点、条件边和并行分支。图来自 LangChain 官方 Studio 介绍文章；Studio 属于 LangSmith，可以连接本地 Agent Server，当前界面可能与发布截图不同。\n\n'
        'Quickstart 用于安装与首个图，interrupt 指南展示暂停与恢复。恢复要配置检查点和 thread_id，并验证重放；外部写操作要处理幂等。JS/TS 团队可在官方文档中切换语言。'
    ),
        360, ['graph', 'persistence', 'interrupt'], 'fw-graph'))
    result.append(profile(
        3, 'MetaGPT：按专业角色交付软件产物',
        'Python 多 Agent 框架：把需求转成文档、设计与代码，也支持自定义角色和数据分析任务。',
        [('软件团队与 SOP', '内置产品、架构、项目管理、工程等角色与协作步骤。'),
         ('角色与行动扩展', '通过 Role / Action 定义职责、关注消息和执行动作。'),
         ('文档与代码产物', '围绕需求生成分析、设计、接口和代码等项目文件。'),
         ('数据分析助手', 'Data Interpreter 可编写并执行分析代码、生成图表。')],
        ['软件项目原型', '文档与代码交付', '代码执行与数据分析'],
        'assets/frameworks/metagpt-pomodoro-design.png',
        'MetaGPT 官方番茄钟项目示例生成的类与接口设计图。',
        '官方示例产物：番茄钟项目的类与接口设计图。生成的设计和代码仍需人工验收。',
        'https://github.com/FoundationAgents/MetaGPT/tree/main/docs/resources/workspace/minimalist_pomodoro_timer',
        'https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html',
        'https://github.com/FoundationAgents/MetaGPT#usage',
        '生成 2048 项目 · 数据分析用法',
        (
        '【5分钟】图是官方番茄钟示例的类与接口设计产物。借此说明软件团队 SOP、Role/Action 和生成文件；Data Interpreter 还可执行分析代码。官方 Usage 有 2048 游戏和 Iris 分析用法，examples 目录提供扩展示例。\n\n'
        '按所选 release 准备环境。README 要求 Python >=3.9 且 <3.12，并列出 Node 与 pnpm。本课实战使用独立 Python 3.11、MetaGPT 0.8.2 和已验证的 Role/Action/Team 依赖，准备步骤见 docs/dev-team-demo-guide.md。打开 demo/dev_team/team.py 看消息订阅，运行 Review Agent 后仍要检查需求覆盖与测试。'
    ),
        300, ['meta'], 'fw-meta'))
    assert len(result) == 4
    assert sum(item['seconds'] for item in result) == 18 * 60
    return result
