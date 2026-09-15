# Agent 推理与协作 · 讲师讲稿

90 分钟，32 页。备注中的时间为建议，可按听众调整。

演讲前：运行 `python demo/server.py`，打开浏览器到本地 8765 端口。默认规则模拟决策，真实 CSV 工具。离线回放明确标记为历史轨迹。

## 01 · Agent 推理与协作

【开场，1 分钟】今天研究 Agent 怎样决定下一步、怎样从工具拿到证据，以及多个角色如何接力完成任务。重点是 ReAct。请学员带着一个问题听：如果某一步失败，我怎样判断问题出在模型决策、工具还是编排？培训默认大家了解 Python 函数与基本 LLM 调用，但不要求使用过任何 Agent 框架。说明课程以同一份合成订单数据贯穿，不把演示样本当作真实业务结论。

## 02 · 本次培训的学习路径

【2 分钟】先预告学习结果：能画出 Thought–Action–Observation，能区分局部动作和全局计划，能设计失败修正，能解释三类协作架构，最后能跑通双 Agent 的任务。ReAct 占最多时间，因为它既能独立运行，也可以放进规划执行体系的执行器中。介绍 90 分钟分配；若只有 60 分钟，合并 6–8 页、简讲 14 和 23–24 页，保留完整 Demo。

## 03 · 贯穿案例：订单分析助手

【2 分钟】先让学员说出任务里容易遗漏的条件：取消订单是否计入？退款如何处理？净销售额是不是利润？把这些转成可检验的成功标准，而不是只要求生成一段漂亮中文。告知数据有 8 行，但先不公布正确答案；后面用真实工具算出来。强调工具与校验器负责数值，模型可以负责选择动作和解释结果。

## 04 · Agent 与预定义工作流

【2 分钟】先澄清词义：函数叫 Agent 并不自动产生智能；关键在于是否有依据状态作决策的机制。固定的 CSV 计算本身用程序更直接，选它做案例是为了让证据可核对。生产系统经常混合二者，例如先固定鉴权，再让模型选查询工具，最后由确定性规则验收。提问：如果只需要每晚固定汇总订单，真的需要多 Agent 吗？预期回答是不一定。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 05 · Thought–Action–Observation 循环

【4 分钟，重点】逐次点击按钮。第一次显示决策摘要：不知道字段，先检查；第二次是 inspect({})；第三次得到真实字段列表。再点一次，说明新的 Thought 必须利用 Observation，而不是机械重复最初请求。ReAct 原始论文强调推理与行动交错，行动能访问外部环境，证据反过来修订计划。图中环不是无限循环：右侧必须有成功出口与受控停止出口。可请学员复述三步分别由模型还是运行时负责。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 06 · Thought：形成下一步决策

【2 分钟】Thought 的价值是把目标与动作联系起来，不是要求模型输出越长越好的思维文本。现代应用往往只记录可审计的简短说明、动作和证据，不需要暴露完整内部推理。这里的引用是人为编写的教学摘要。区分“应该检查字段”与“字段一定叫 sales”：前者是合理行动意图，后者是还未验证的假设。请学员说出此时已知和未知的内容。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 07 · Action：模型请求，程序执行

【3 分钟】逐项解释工具名、字段和过滤条件。模型只提出请求，宿主程序负责真正执行。一个完整工具定义不仅有名称，还应包含参数 schema、用途与返回值。本例只允许 inspect、aggregate、report，不接收文件路径，也不执行模型生成的任意代码。问学员：模型回复“我已经读取了 CSV”算不算成功？答案要看实际工具返回与日志。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 08 · Observation：把环境事实带回循环

【3 分钟】这两个 JSON 是精简示意，实际日志可以包含更多字段。成功返回让模型知道能用什么；错误告诉模型当前策略哪里不成立。错误应保留具体原因和恢复所需的信息。外部网页或文档即使写着“忽略规则”，仍然只是待分析数据。Observation 也可能过时、为空或不完整，因此需要来源、时间与状态，而不是把任何工具文本都当作真理。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 09 · 一次完整的 ReAct 轨迹

【3 分钟】从上往下讲，明确不是一次 prompt 就凭空生成三个动作。每个动作后都把 Observation 加入状态。公布样本结果：办公 1450，数码 1200，总共 2650。最后一行 Finish 在实现中由确定性校验器批准；模型说“完成”还不够。这里的 report 是确定性工具生成文本，便于核对；真实应用可以让模型写解释，但数值和引用仍应校验。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 10 · 最小控制循环

【3 分钟】用代码把前三页连接起来。agent.decide 是决策边界，validate_tool_call 是执行边界，observations 是反馈通道。伪代码没有展开异常处理；实际 Demo 捕获工具错误并进入重规划。让学员指出如果忘记 append 会发生什么：模型可能重复相同动作，因为它没有得到新证据。再问，如果去掉 MAX_STEPS，坏模型输出或重复错误可能导致无限消耗。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 11 · 常见失败与停止策略

【3 分钟】字段错误通常是策略问题，原样重试没有意义；网络瞬断可能适合退避重试，二者不能混为一谈。对有副作用的工具，重试还需要幂等键或结果核对。演示中的 --max-steps 1 会停止且返回非零退出码，不会生成成功报告。可以把最多工具步数、最多模型调用、总时间与费用都纳入预算。强调这些是工程设计建议，不是 ReAct 论文中自动赠送的功能。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 12 · 判断题：下一步应该做什么？

【2 分钟】先让学员举手或投票，再点选。B 是本例的合理选择，但还需要确认 gross 的业务含义，不能只靠名字相似就换字段。A 没有利用新证据；C 没有计算依据。追问：如果工具只返回“发生错误”呢？恢复会更困难，因此好的工具错误信息是 Agent 能力的一部分。用这页过渡到计划修订：局部动作修正还可以进入更高层的任务计划。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 13 · Plan-and-Execute：先形成全局计划

【3 分钟】ReAct 可以边执行边调整局部行动；Plan-and-Execute 把全局拆解显式提出来。不是任何任务都需要预先写十条计划，一步可完成的事情通常不值得增加规划调用。规划者可以较少调用，执行者可以使用较便宜的模型或确定性工具，但是否更省钱要实测，不能保证。我们的执行 Agent 仍可以采用 ReAct，因此两者不是互斥方案。

来源：[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)

## 14 · 计划需要可执行的结构

【2 分钟】“分析数据”过于含糊，需要可验证的输出契约。说明 S2 为什么依赖 S1：没有实际字段就容易猜错。S3 为什么依赖 S2：不能先写报告再找数字。表中 depends_on 是生产设计示意，最小 Demo 使用固定顺序和已完成步骤列表实现同样的前置关系。并发任务可用 DAG，但这里保持串行有助于课堂观察。

来源：[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)

## 15 · 什么时候重新规划？

【2 分钟】此页是故障场景的简化表示。强调不必全部从头再来：已检查的字段可以继续使用，但如果数据源发生变化就要重新检查。计划修订要更新版本，保留失败原因，避免执行器仍按旧计划执行。不要每完成一次工具调用就重规划，否则可能比单 Agent 更昂贵；根据依赖、风险和反馈选择检查点。

来源：[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)

## 16 · Reflexion：把反馈变成可用经验

【3 分钟】按原论文介绍 Actor、评价与自我反思之间的分工。Reflexion 的关键是反思文本被保留，并实际影响下一次尝试；不是在同一段回答后附加“我会更努力”。语言反馈可来自外部，也可以内部模拟，但可靠的外部校验通常更容易审计。我们把反思职责放在规划 Agent，把评价放在确定性工具，仍然只有两个 Agent 角色。Demo 是简化教学实现，不是完整复现论文实验。

来源：[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 17 · 有用的反思必须改变下一次行动

【3 分钟】让学员比较两段反思。第二段明确错误发生在哪里，引用了哪一条证据，下一次行动怎样改变。反思也可能错误，因此不能把所有自我总结永久写进全局记忆；应标注任务范围、时间、证据与验证状态。这里的 memory 只属于一次运行，避免把一个数据集的字段映射当成所有数据集的规则。课后练习可以让学员写一条退款重复扣除的反思。

来源：[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 18 · 三种机制可以嵌套组合

【2 分钟】用嵌套图收束三个概念。问学员：能否只用 ReAct？可以。能否让计划执行器是普通程序？可以。反思是否总能提高效果？不保证，错误反思会强化坏策略，仍需实验与校验。强调这是一种组合方案，不是必须同时使用全部机制的标准答案。接下来把规划与执行职责拆给两个角色，就自然进入多 Agent。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)；[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)；[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 19 · 什么时候值得拆成多个 Agent？

【2 分钟】拆角色不是给相同 prompt 改几个名字。可以举客服检索与退款执行具有不同权限、研究与审稿具有不同上下文的例子。两名 Agent 可以使用同一个底层模型，差别来自指令、工具和状态；也可以使用不同模型。额外角色能改善任务隔离，但会增加 token、延迟和错误面。这里的选择建议是工程判断，不是保证性能提升的结论。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 20 · Supervisor：集中分派与汇总

【3 分钟】监督者知道有哪些专家，将任务路由给合适角色。专家可以作为工具被调用，也可以经消息队列返回结果。图中所有叶子都回到 Supervisor，强调控制权集中。用订单例子说：规划者分派计算，执行者返回数据，规划者再决定是否结束。询问如果监督者失效如何恢复：持久化任务状态和检查点比只存一段聊天记录更可靠。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 21 · 层次化：把团队作为协作单元

【3 分钟】层次化可以看作监督模式的递归组合，不需要把它当成完全独立的神秘架构。优点是隔离上下文与复杂度，代价是多层摘要可能丢失约束。每层都需要明确输入、输出和失败上报机制。让学员思考为什么“总经理、经理、主管、员工”四层模型链未必比两层好：层次必须对应实际任务边界。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 22 · Swarm：通过交接转移控制权

【2 分钟】Swarm 在业界的用法并不完全统一，此处聚焦去中心化的交接模式。和 Supervisor 每次回中央不同，当前 Agent 可以决定把控制权交给下一位。举例接待者识别是退款问题后交给退款角色。强调交接对象、任务摘要、证据引用与返回条件必须明确；“大家互相聊天”不等于能完成任务。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 23 · Agent 间通信：用消息契约接力

【2 分钟】这是通用消息契约示意，不是某个框架的固定 API。run_id 把整次运行关联起来，task_id 关联步骤，plan_version 避免过期结果覆盖新计划。跨进程时还要考虑重复消息、ack、幂等和超时；同一进程也应该保留清楚的接口。Demo 的 events 用 run_id、step_id 和 plan_version 表达同类关系，actor 字段记录来源。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 24 · 共享状态：先定义谁能写什么

【3 分钟】指出 Demo 是串行执行，不声称展示了分布式一致性。表格说的是逻辑归属：模型提出内容，宿主程序验证后真正写入。LangGraph 可用 reducer 定义状态更新，但 reducer 不是万能锁，外部数据库副作用仍要自己设计一致性。举例两个 Agent 同时生成报告路径，若简单覆盖就会丢失结果；用 task_id 到产物的映射比一个共享字符串更稳妥。

来源：[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 25 · AutoGen / MetaGPT / LangGraph

【4 分钟】逐列讲抽象，不做没有实测的速度和质量排名。AutoGen 的 Core 提供消息和运行时，AgentChat 提供更高层的团队 API；不要混用老版 0.2 示例与新 AgentChat 写法。MetaGPT 以软件团队角色和 SOP 著称，也有其他用例，不是只能写软件。LangGraph 是较低层的有状态编排基础设施，可独立于 LangChain 使用。当前 AutoGen 仓库的维护模式信息会影响新项目选择，因此必须现场说明，并建议开课前再次核对。

来源：[AutoGen · 官方仓库](https://github.com/microsoft/autogen)；[MetaGPT · 官方仓库](https://github.com/FoundationAgents/MetaGPT)；[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)

## 26 · 按照项目约束做选择

【3 分钟】这页是工程建议，不是框架官方保证。先问项目是否需要暂停恢复，再问业务是否已存在稳定 SOP，再看已有代码和团队能力。AutoGen 仍值得理解，但不应忽略维护现状。避免因为演示用了两个角色就要求整个生产系统都上多 Agent。我们现场 Demo 用标准库显式编排，目的在于看清机制；迁移到框架时，先映射状态、节点、边与检查点。

来源：[AutoGen · 官方仓库](https://github.com/microsoft/autogen)；[MetaGPT · 官方仓库](https://github.com/FoundationAgents/MetaGPT)；[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)

## 27 · 落地前的五个检查点

【3 分钟】把框架特性翻译成团队需要验收的行为。给出一个对照：有日志不代表日志可关联，有 checkpointer 不代表外部写入可安全重复，有多个 Agent 不代表有独立验证。Demo 将前四项做成可观察的最小行为，第五项讨论设计并保留轨迹回放，但不宣称具备生产级断点续跑。课后作业可以补充持久化状态和恢复操作。

## 28 · 双 Agent：规划与执行的职责边界

【4 分钟，开始 Demo】先向观众明确模式，不能把规则模拟说成真实 LLM 调用。默认模式让工具、状态与失败路径稳定可复现；规划和执行决策由规则产生。若预先安装了 Ollama 模型，可用 README 中的真实模式命令，两个角色使用不同指令和上下文。浏览器现场运行调用本地 Python，同一份代码也可以在终端执行。先展示 orders.csv，再指出 PlannerAgent、ExecutorAgent、ToolBox 与 run 四个边界。

## 29 · 现场运行：观察一次失败与修正

【8 分钟】点击运行，说明页面会在 Python 完成后显示完整轨迹，逐步播放是回放，不是实时 token 流。先读 Plan v1，再点 Thought、Action 和 Observation。到 Fault 事件时暂停：这是人为注入的 sales 字段错误，不是声称模型自然犯了错。继续到 Reflexion，看失败点与修正，然后 Plan v2；S1 已完成，所以只剩 S2、S3。最后看 Finish 的 verified=true。取消注入再运行，对比正常路径没有反思。若服务不可用，点击教学回放，页面会明显标注为已录制轨迹。不要把回放当作刚刚运行。

## 30 · 结果验收与代码定位

【3 分钟】独立复算办公：500 + (600−150) + 500 = 1450；数码：(800−100) + 400 + (200−100) = 1200。取消订单 900 和 200 不计入。强调净销售额不是利润，没有成本就不能谈利润，没有对比期就不能说增长。打开输出 JSON，查看 plan_version、memory、events 和 verified。最后执行预算耗尽命令，说明正常停止和成功不是一回事。

## 31 · 把机制迁移到你的任务

【3 分钟】给出 15–20 分钟的课后动手题，不要求课堂全部完成。增加 region 字段后，按地区汇总净额；故意请求不存在的 area 字段，要求错误指向具体参数。验收应该断言地区合计仍等于 2650，并核对订单证据。参考答案不是“再加一个 Agent”，而是先扩展工具、计划和校验。讨论评价器若只检查文本是否包含数字，就可能放过错误的统计口径。

## 32 · 继续阅读与复习

【2 分钟】最后请学员用三句话复述：ReAct 用环境证据推动下一步；规划把任务与验收显式化；反思让失败经验影响后续尝试。多 Agent 是组织方式，框架是实现工具。引导先读 ReAct 和 Reflexion 摘要，再读官方框架概览。提醒框架维护状态会变化，上课前再次核对 AutoGen 仓库。交付目录中的 sources.md 提供完整链接，speaker-notes.md 可作为备课讲稿。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)；[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)；[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)；[AutoGen · 官方仓库](https://github.com/microsoft/autogen)；[MetaGPT · 官方仓库](https://github.com/FoundationAgents/MetaGPT)；[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)
