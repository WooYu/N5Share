"""Demo tradeoffs and reference slide renderers."""
from html import escape
from architecture_reference import architecture_overview, architecture_details

OUTING_FRAMEWORKS = {
    1: ('① 单 Agent', '对应第 3 页①：同一角色组合模型、检索和工具，完成一次建议。'),
    2: ('② ReAct', '对应第 3 页②：310 元超额后，根据观察决定再查哪一个候选。'),
    3: ('③ Plan & Execute', '对应第 3 页③：先计划再执行；失败反馈经 Reflexion 修订为计划 v2。'),
    4: ('④ 多 Agent', '对应第 3 页④：主管分派、专业角色独立交付、统一汇总。'),
    5: ('⑤ Router + Skill', '对应第 4 页⑤：输入意图 → 选择技能 → 加载流程与 Reference → 执行。'),
    6: ('⑥ Blackboard', '对应第 4 页⑥：角色读写黑板；状态变化触发就绪角色。'),
    7: ('⑦ Graph / Workflow', '对应第 4 页⑦：显式节点、条件边和结束节点决定执行顺序。'),
}

FRAMEWORK_LINKS = {
    '后半程：把能力组织成多 Agent 系统': ('④ 分工 + ⑥ 共享状态 + ⑦ 图编排', '沿用前面的架构地图：角色交付产物，状态记录进展，图决定下一步。'),
    '控制流与数据流': ('④ 多 Agent + ⑦ Graph / Workflow', '分派与交接表达控制权；证据与消息表达数据传递。'),
    '第七步：设计共享状态': ('⑥ Blackboard 的共享工作区 + ⑦ 显式图', '借鉴黑板的状态协作；本课由图触发节点，未实现状态驱动的黑板调度器。'),
    '协作模型：五种控制关系': ('④ 多 Agent 的组织方式', 'Supervisor、Parallel、Swarm、Review、Hierarchical 可组合，由⑦表达执行关系。'),
    'Supervisor：集中分派与汇总': ('④ 多 Agent · Supervisor', '对应第 3 页 Orchestrator：控制权回到主管，由它统一分派和汇总。'),
    'Parallel：独立执行与统一汇合': ('④ 多 Agent + ⑦ Graph / Workflow', '并行是执行方式：两个独立分支完成后汇合，状态按规则合并。'),
    'Handoff、Swarm 与层次化': ('④ 多 Agent · 交接与分层', '回看出游多角色演示：比较谁持有控制权，以及交接时保留哪些证据。'),
    'Review：独立评审与有限修订': ('④ 独立审查 + ③ 反馈机制', '延续出游 Reflexion 的失败反馈；本例由独立角色审查，仍需补证据与再验收。'),
    '从协作模型到开发框架': ('架构④ / ⑦ → 开发框架', '第 2–4 页讲系统如何组织；LangGraph、AutoGen、MetaGPT 讲用什么实现。'),
    'LangGraph：把设计映射为状态图': ('⑦ Graph / Workflow · 本课实现', 'Node 承载角色或程序，State 保存共享记录，Edge 表达分派、汇合与回路。'),
    '案例起点：固定工作流基线': ('⑦ Graph / Workflow · 固定基线', '回到第 4 页图编排：已知缺失条件用预设分支处理，先建立可验证的基线。'),
    '案例演示 ①：Supervisor 重新分派': ('④ 主管分工 + ③ 计划修订 + ⑦ 编排', '从出游天气 / 费用分工迁移到证据 / 知识分工，观察反馈如何触发 v2 分派。'),
    '案例演示 ②：Parallel 冲突合并': ('④ 独立分工 + ⑥ 共享状态 + ⑦ 并行', '延续出游两份结果取交集；冲突读数必须保留来源、时间和合并理由。'),
    '案例演示 ③：Review 退回修订': ('④ 专业审查 + ③ 反馈回路 + ⑦ 编排', '延续出游失败后再验收；这里缺的是电压证据，改措辞不能修复缺失。'),
    '案例复盘：从运行轨迹回看设计': ('回看架构④ / ⑥ / ⑦', '在同一轨迹中分别指出角色分工、共享工作区与图控制；评估新增协作是否值得。'),
}


def framework_html(label, connection):
    return ('<aside class="framework-link" aria-label="与第2到4页架构的对应关系">'
            f'<strong>架构对应 · {escape(label)}</strong><span>{escape(connection)}</span></aside>')


OUTING_TRADEOFFS = {
    '1': dict(label='LLM · 单 Agent 的模型基础', advantage='一次生成，交互简单、调用少。', limitation='没有当前天气和费用，建议缺乏事实依据。', observe='公园建议尚未核实；本页仅做生成。'),
    '2': dict(label='RAG · 可组合的检索能力', advantage='引入资料引用，规则与依据可核对。', limitation='依赖检索质量；文档不等于实时数据。', observe='D01 / D02 给出规则，尚未查询天气。'),
    '3': dict(label='① 单 Agent · RAG + Tool', advantage='检索规则与工具结果共同支持回答。', limitation='规则不等于当前事实；工具可能失败。', observe='先检索 D01 / D02，再执行天气、场馆和完整费用工具。'),
    '4': dict(label='② ReAct', advantage='每轮观察推动下一步，适合探索查询。', limitation='调用与延迟增加；必须限制无进展循环。', observe='一次一个工具；观察后选择下一步；雨天200元应停止。'),
    '5': dict(label='③ Plan & Execute', advantage='先明确依赖，步骤与验收路径清楚。', limitation='初始计划会出错；变化时需重新规划。', observe='先有天气与场馆名单，再筛选和算价。'),
    '6': dict(label='③ 规划执行 + Reflexion 反馈回路', advantage='把失败转成具体修订，复用有效证据。', limitation='多一轮调用；反思仍需外部事实验收。', observe='补齐餐费与天气后生成计划 v2，并重新验收。'),
    '7': dict(label='④ Multi-Agent · Supervisor', advantage='天气与费用分工，独立产物可核对。', limitation='多次调用与协调开销；共同偏差仍存在。', observe='合并两份摘要取交集，保留各自引用。'),
    'hierarchical': dict(label='④ Multi-Agent · 层次化团队', advantage='组长管理专业子任务，职责分层清楚。', limitation='层级增加调用；转述可能丢失约束与证据。', observe='检查组长交付是否保留预算与来源。'),
    'swarm': dict(label='④ Multi-Agent · Swarm', advantage='当前角色按专长交接，路径更灵活。', limitation='容易交接循环或丢失目标，需限定交接次数。', observe='核对交接对象、证据与结束条件。'),
}

# Page architecture numbers are separate from the existing real-model API stages.
ARCHITECTURE_TRADEOFFS = {
    1: dict(label='① 单 Agent · LLM + RAG + Tool', advantage='一个角色结合文档规则与工具结果。', limitation='文档规则不等于当前事实；工具可能失败。', observe='RAG 命中 D01 / D02；Tool 返回天气和三项费用。'),
    2: OUTING_TRADEOFFS['4'],
    3: OUTING_TRADEOFFS['6'],
    4: OUTING_TRADEOFFS['7'],
    5: dict(label='⑤ Router + Skill', advantage='按意图加载流程与资料，技能可以复用。', limitation='意图可能模糊或冲突；路由与技能均需维护。', observe='切换用户需求：费用技能不查天气；模糊输入先澄清。'),
    6: dict(label='⑥ Blackboard', advantage='角色共享证据，按状态就绪条件协作。', limitation='需管理调度、版本和冲突，避免重复触发。', observe='场馆名单发布后触发费用角色；三项证据齐备才触发汇总。'),
    7: dict(label='⑦ Graph / Workflow', advantage='执行顺序与分支明确，路径可追踪。', limitation='新增路径要改图；恢复须另配持久化与幂等。', observe='雨天走 indoor_filter；超预算走 no_solution → END。'),
}

DIAGNOSIS_TRADEOFFS = {
    'workflow': dict(label='⑦ Graph / Workflow · 固定基线', advantage='固定条件可测试，低协调成本，出口明确。', limitation='新条件须改代码；不适合难枚举的探索路径。', observe='补读是预设分支，不是 Agent 重规划。'),
    'supervisor': dict(label='④ Multi-Agent + ⑦ Graph · 主管委派', advantage='集中分派与汇总，责任和计划版本明确。', limitation='协调者是瓶颈；委派增加消息与等待。', observe='缺电压后重新 Dispatch，计划升级 v2。'),
    'parallel': dict(label='④ Multi-Agent + ⑦ Graph · 并行分析', advantage='独立分支同时执行，缩短可并行部分的等待。', limitation='需等待汇合并处理冲突；总调用量未必减少。', observe='保留 11.7 V / 12.6 V 两份来源和取舍。'),
    'review': dict(label='④ Multi-Agent + ⑦ Graph · 提案与评审', advantage='独立检查引用，反馈推动具体修订。', limitation='审查与重写增加延迟；审查者也可能出错。', observe='指出 E-VOLTAGE 缺失，补证据后再审。'),
    'integrated': dict(label='④ Multi-Agent + ⑦ Graph · 综合流程', advantage='统一状态串起分派、并行、补查和审查。', limitation='编排更复杂；需处理版本、冲突与预算。', observe='共享状态借鉴⑥；当前仍是显式图调度。'),
}


def tradeoff_html(item):
    return ('<aside class="tradeoffs" aria-label="当前演示的优势与局限">'
            f'<strong class="tradeoff-label">{escape(item["label"])}</strong>'
            '<div class="tradeoff-columns">' + ''.join(
                f'<div class="tradeoff-{key}"><b>{title}</b><span>{escape(item[key])}</span></div>'
                for key, title in [('advantage', '优势'), ('limitation', '局限'), ('observe', '本例观察')]) + '</div></aside>')
