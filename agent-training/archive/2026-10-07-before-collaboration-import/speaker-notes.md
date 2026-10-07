# 高级推理框架与多 Agent 协作 · 讲师讲稿

90 分钟，42 页。面向 Java 后端、前端、客户端开发者，不预设 Agent 开发经验。

备课：安装 requirements.txt 后运行 `python demo/server.py`。默认规则模拟决策，LangGraph 实际编排，工具只读合成资料。离线 HTML 内嵌的是预录轨迹；completed 仅表示报告生成，仍需人工审核。verified 仅表示证据契约通过。

## 01 · 高级推理框架与多 Agent 协作

开场与目标 · 30 秒

【30 秒】今天不要求 Python 熟练，也不要求做过模型微调。Agent 在难以预先枚举的任务路径中解释信息、选择工具；已知条件分支仍是工作流。后面用函数、状态对象和 HTTP 对照大家已有的开发经验。只有两个核心目标：面对复杂度能选择合适的推理与编排方案；能设计一个职责清楚、能够停止的简单多 Agent 系统。所有工单、诊断读数与知识条目均为合成教学样本，不连接真实车辆。最终输出是待人工确认的建议，演示通过也不代表完成维修。

## 02 · Agent 的 7 种主流架构

开场与目标 · 30 秒

【30 秒】先用参考图的七种表述建立地图：单 Agent、ReAct、Plan & Execute、多 Agent、Router + Skill、Blackboard、Graph / Workflow。这七项不是互斥分类：ReAct 和规划可用于单个角色；多角色可共享状态并由图编排；技能路由可以保留一个 Agent。路径是理解复杂度的参考，不是必选升级顺序。第5–11页按相同编号逐页演示七种架构。LLM、RAG、工具收进①，Reflexion收进③；⑤展示意图选择技能，⑥展示状态触发角色，⑦展示节点与边。后半程用LangGraph组合多角色与共享状态。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)

## 03 · 七种架构详解（1/2）

开场与目标 · 30 秒

【30 秒】七种架构按原顺序分两页排版，并未把前四项归为同一类。单Agent与多Agent说明角色组织，ReAct与规划执行说明决策策略；单个角色或多角色内部均可使用这些策略。按简图、特点、优点、问题与适用场景读四列。LLM一次生成只是基础，RAG与工具调用是可组合能力。ReAct 以工具观察推动下一次决策；规划执行先拆任务与依赖；多 Agent 增加独立上下文、产物和协调成本。在出游演示里分别观察超预算后换候选、先天气再筛选、以及天气与费用两份摘要合并。Copilot、ChatGPT 是参考图列举的产品示例，可组合多种架构，不据此推断产品内部实现。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)；[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)；[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 04 · 七种架构详解（2/2）

开场与目标 · 30 秒

【30 秒】本页沿用参考图结构，补上本课对应与实现边界。Router + Skill 先判断意图，再按需加载技能；技能不是单个工具，手选模式也不算意图路由。第9页出游演示用关键词路由选择出游或费用技能，模糊需求先澄清；后半程诊断的意图路由仍为设计对照。Blackboard 由公共工作区和状态变化驱动协作，必须处理调度、并发和版本。第10页出游演示用最小就绪条件调度观察状态触发；后半程诊断有共享状态，但仍由图显式调度。两者不宣称实现生产级完整黑板系统。Graph / Workflow 显式表达节点、边、分支、并行和回路。严格意义的 DAG 不含环；反馈回路由状态图表达。第11页出游图用浏览器规则示意，本课五种诊断模式均由 LangGraph 执行；持久恢复与人工中断仍需配置和实现。Router + Skill 的推荐限于按需复用技能的 AI Coding 场景，不是所有任务的最佳方案。Skill 包含可执行能力与知识说明 Reference。参考实现区列出 LangGraph、Temporal、Airflow、n8n 和 Prefect：它们分别偏向 Agent 状态图、工作流执行、调度与自动化，并非全部都是 Agent 框架。LangGraph 用于黑板协作时仍须设计状态驱动调度。

来源：[LangChain · Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)；[Blackboard · 概念说明](https://en.wikipedia.org/wiki/Blackboard_system)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 05 · 演示 ①：单 Agent · 模型、检索与工具

能力演进 · 3 分 20 秒

【3 分 20 秒】演示操作：先指出图中组件与职责，再按开始演示、下一步逐步高亮节点和信息流；上一步可回看，重播回到结构总览。天气、预算、用户意图、完整记录及七页的真实模型入口在更多中。底部常驻优势、局限与适用场景。谁处理下一步？同一个 Agent。本页优势：同一个角色用规则和事实修正建议，协调成本较低。本页局限：检索质量与工具可靠性影响结果；复杂上下文会集中在一个角色。适用场景：资料问答 + 少量业务工具第5–11页与第2–4页的七种架构对应，架构可以组合，不是升级时间线。七页用同一组场馆，但设置不同关键事件。本页先展示没有事实支持的公园想法，再检索D01天气和D02费用规则，排除无关D03。查询天气发现下雨后，原公园想法不成立；同一个Agent继续读取场馆名单、核算三项完整费用，默认选城市博物馆210元。重点是同一个角色汇合规则和工具事实来修正建议。工具请求与返回分别高亮。优点是协调成本较低；局限是检索和工具出错都会影响它。两大一小、半日出游；公园180元、自然馆310元、博物馆210元。离线生成和关键事件为教学脚本；真实入口使用当前初始参数，不自动重放离线事件。不订票、不付款。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 06 · 演示 ②：ReAct · 观察驱动下一步

能力演进 · 3 分 25 秒

【3 分 25 秒】演示操作：先指出图中组件与职责，再按开始演示、下一步逐步高亮节点和信息流；上一步可回看，重播回到结构总览。天气、预算、用户意图、完整记录及七页的真实模型入口在更多中。底部常驻优势、局限与适用场景。谁处理下一步？Agent 根据最新观察决定。本页优势：查到超预算后再换候选，满足要求就停止查询。本页局限：多轮调用增加延迟；要限制重复查询、次数和总用时。适用场景：排障、搜索与探索性查询默认雨天300元，先查天气与场馆名单，排除公园，再核算自然馆310元。价格超预算是关键事件：结果返回后，Agent才决定改查博物馆，210元符合要求，停止查询。与①的角色数量相同，本页强调每轮观察怎样改变下一次行动。晴天200元时公园180元已够，不再查询其他场馆；雨天200元时两处室内场馆都超预算，停止。优点是能根据新结果调整查询；局限是多轮往返增加耗时，要限制重复查询和调用次数。离线判断为规则，真实模式每轮由模型提出请求，只显示简短决策摘要。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 07 · 演示 ③：Plan & Execute · 规划与反馈

能力演进 · 3 分 25 秒

【3 分 25 秒】演示操作：先指出图中组件与职责，再按开始演示、下一步逐步高亮节点和信息流；上一步可回看，重播回到结构总览。天气、预算、用户意图、完整记录及七页的真实模型入口在更多中。底部常驻优势、局限与适用场景。谁处理下一步？规划器根据新要求修订剩余步骤。本页优势：要求变化时可重规划，复用已查天气、名单和价格。本页局限：改计划与再次验收增加步骤；重规划不能改变客观价格。适用场景：有依赖、执行中可能改要求的任务默认先按300元计划查天气、名单、完整费用，初步选博物馆210元，尚未交付。关键事件发生在执行途中：用户把预算降到200元，旧选择不能通过新预算验收。反馈告诉规划器保留已有天气、名单与价格，只修改预算相关的剩余步骤；执行器按计划v2重新筛选，雨天200元仍无解，停止并请用户调整条件。重规划不能改变客观价格。如果初始预算已是200或100元，事件改为用户再次确认预算上限；晴天200元公园180元仍可通过。优点是要求变化时能修订计划并复用证据，局限是修订与再次验收增加步骤。图中的Reflexion/反馈承载本次变更和检查反馈。真实模型入口仍展示计划v1、明确标注的漏餐费错误草稿、反思和v2的既有示例；它不自动注入离线的途中改预算事件。

来源：[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)；[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 08 · 演示 ④：多 Agent · 分派、消息与汇总

能力演进 · 2 分 40 秒

【2 分 40 秒】演示操作：先指出图中组件与职责，再按开始演示、下一步逐步高亮节点和信息流；上一步可回看，重播回到结构总览。天气、预算、用户意图、完整记录及七页的真实模型入口在更多中。底部常驻优势、局限与适用场景。谁处理下一步？主管分派，必要结果齐备后汇总。本页优势：各角色独立负责，主管能对照不同证据作完整判断。本页局限：局部建议不能直接交付；消息等待和合并增加协调成本。适用场景：需要独立职责、上下文或权限的任务默认雨天300元。天气Agent只看天气，先建议自然馆；费用Agent只比较完整价格，建议最便宜的公园180元。两份局部建议不同是本页关键事件，单份都不能直接交付。主管对照证据：公园便宜但雨天不能去，自然馆室内但310元超预算，城市博物馆室内且210元，才满足两项要求。晴天时两角色可能都建议公园，主管仍需检查预算。优点是独立责任和证据容易核对；局限是等待消息与合并增加成本，共用模型也可能有共同偏差。离线局部建议是教学脚本，不宣称测得真实模型冲突。真实入口保留主管、层次化与Swarm模式，由模型生成各自消息，不保证出现同样意见。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 09 · 演示 ⑤：Router + Skill · 按意图加载

能力演进 · 2 分 40 秒

【2 分 40 秒】演示操作：先指出图中组件与职责，再按开始演示、下一步逐步高亮节点和信息流；上一步可回看，重播回到结构总览。天气、预算、用户意图、完整记录及七页的真实模型入口在更多中。底部常驻优势、局限与适用场景。谁处理下一步？Router 选技能，技能规定执行流程。本页优势：需求变了就切换处理流程，费用技能省去天气查询。本页局限：模糊、多意图与冲突需要处理；路由和技能版本都要维护。适用场景：多类请求共用入口、标准流程可复用默认先输入安排出游，关键词Router选择出游技能并准备D01/D02，尚未执行工具。关键事件是用户改口：先不安排出游，只算费用。Router重新匹配新文本，切换费用技能，只加载D02，查询名单、计算总价，不查天气。费用技能输出180、310、210元及预算内外判断，不能当出游建议。Skill是一套处理流程与资料、工具边界，不等于一个工具。费用工具也可由出游技能调用，不代表必须再调用费用技能。更多里选择只核算费用可直接走费用技能；帮我看看则先澄清。优点是按需切换流程，局限是模糊、多意图和版本维护。离线改口为脚本事件；真实入口只处理当前下拉框的初始需求，不自动改口，保留关键词路由。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[LangChain · Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)

## 10 · 演示 ⑥：Blackboard · 状态触发协作

能力演进 · 2 分 40 秒

【2 分 40 秒】演示操作：先指出图中组件与职责，再按开始演示、下一步逐步高亮节点和信息流；上一步可回看，重播回到结构总览。天气、预算、用户意图、完整记录及七页的真实模型入口在更多中。底部常驻优势、局限与适用场景。谁处理下一步？调度器检查黑板上的就绪条件。本页优势：资料共享；名单发布后自动触发费用，减少逐条分派。本页局限：缺资料会等待；还要管理版本、重复触发和并发冲突。适用场景：角色围绕共享证据逐步补齐结果黑板v0记录天气、名单、费用、结果。先明确显示费用角色想开始，但名单为空，只能等待；等待不写入费用，也不增加版本。天气、场馆角色发布结果后，名单存在且费用缺失，调度器才触发费用角色。费用写入后天气、名单、价格齐备，汇总角色才能工作；每次实际写入增加版本。与④比较：没有主管逐条分派；与⑦比较：按共享资料是否齐备选择角色，不按预设节点边选择下一站。优点是证据共享和按依赖触发，局限是缺资料会等待，还需处理版本、重复触发、并发冲突。本例角色串行执行，不宣称并发冲突处理或生产级完整黑板。真实入口按相同条件触发模型角色并发布证据；后半程诊断仍由LangGraph显式调度。

来源：[Blackboard · 概念说明](https://en.wikipedia.org/wiki/Blackboard_system)

## 11 · 演示 ⑦：Graph / Workflow · 显式节点与边

能力演进 · 2 分 40 秒

【2 分 40 秒】演示操作：先指出图中组件与职责，再按开始演示、下一步逐步高亮节点和信息流；上一步可回看，重播回到结构总览。天气、预算、用户意图、完整记录及七页的真实模型入口在更多中。底部常驻优势、局限与适用场景。谁处理下一步？预先定义的边和条件代码。本页优势：没有合适方案也有明确出口，路径可追踪、可测试。本页局限：未预设的情况需改流程；恢复还需检查点、幂等与持久化。适用场景：流程明确、需要审计和稳定出口的任务本页初始预算单独设为200元，其余页初始为300元；更多里修改天气或预算仍会同步各页。关键事件是默认雨天200元：公园被排除，两处室内场馆310、210元都超预算，验收沿预设no_solution边结束到END。与③比较：本页没有重新规划，失败处理已写在图中；与②比较：没有由模型临时决定再查什么。更多里改为300元可观察recommend成功出口，晴天走all_places分支。优点是无解也有明确出口，路径可追踪可测试；局限是未预设的情况需要改流程。离线图由普通程序执行；真实入口沿相同条件边调度，在结果节点调用模型生成回答。本图无反馈环；恢复还需检查点、幂等、持久化等配置。

来源：[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 12 · 后半程：把能力组织成多 Agent 系统

多 Agent 流程概念 · 1 分 20 秒

【1 分 20 秒】上一页已经展示多 Agent 可以按职责协作。后半程不再重复能力清单，而是把问题收敛到系统怎样运行。先认识一条多 Agent 流程，再把它设计成角色和状态，随后比较协作模型，最后用同一张远程诊断工单验证。四段内容前后承接，案例中的字段会从概念页一直沿用到运行台。
【回看第2–4页】④ 分工 + ⑥ 共享状态 + ⑦ 图编排；沿用前面的架构地图：角色交付产物，状态记录进展，图决定下一步。。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 13 · 多 Agent 系统的六个组成部分

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】从系统视角看，多 Agent 不是多个聊天窗口。任务给出共同目标，角色承担不同职责，工具取得外部事实，状态保存当前进展，编排器决定执行顺序，约束负责限制权限和轮次。下一页把这六个组成部分放进一次完整运行，观察它们在什么时刻发生作用。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 14 · 一次运行的完整生命周期

多 Agent 流程概念 · 2 分 10 秒

【2 分 10 秒】一条运行以 run_id 贯穿。编排器先创建任务，再根据依赖分派角色；角色调用工具后把结果写回状态；必要分支完成后才汇合；审查决定交付、修订或转人工。这个生命周期是后面所有设计页的主线。下一页进一步区分两条同时发生但作用不同的路径：控制流和数据流。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 15 · 控制流与数据流

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】控制流描述执行顺序和控制权，数据流描述任务、证据和反馈怎样传递。两者必须分别设计：角色被调用不代表拿到了完整上下文，结果写回状态也不代表它能决定下一步。下一页用顺序、并行和反馈回路组合这两条路径。
【回看第2–4页】④ 多 Agent + ⑦ Graph / Workflow；分派与交接表达控制权；证据与消息表达数据传递。。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 16 · 顺序、并行与反馈回路

多 Agent 流程概念 · 2 分钟

【2 分钟】顺序、并行和反馈回路是协作模型下面更基础的流程结构。先画依赖再选择结构，不能为了看起来像多 Agent 而强行并发。后面的 Supervisor、Parallel 和 Review 都只是对这些结构分配控制权的不同方式。下一页解释结构中的信息究竟放在哪里。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 17 · 消息、上下文、状态与记忆

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】上一页确定了流程结构，本页确定信息边界。消息是一次交付，上下文是当前角色看到的切片，状态是本次运行的共同记录，记忆才涉及跨步骤或跨运行保留。明确四者后，才能判断并行分支该读什么、写什么。下一页专门处理并行结束后的同步与合并。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 18 · 并行后的同步与合并

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】并行并不只是同时启动两个角色。系统还需要等待屏障和确定的合并规则。证据与知识可以独立读取，但报告必须等待双方；同一字段出现两个值时要保留时间、来源和适用条件。下一页完成生命周期的最后一部分：什么情况下结束，什么情况下交给人。

来源：[Anthropic · Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 19 · 停止、失败与人工介入

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】到这里，一次多 Agent 运行已经从创建走到出口。系统必须区分完成、转人工、受控停止和取消。人工介入表示由人复核或决定，不等于模型自动获得授权。下一章沿用这条生命周期，把抽象流程逐步设计成可实现的协作图。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 20 · 设计方法：从任务到可执行协作图

多 Agent 设计方法 · 1 分 30 秒

【1 分 30 秒】上一章回答系统怎样运行，本章回答怎样把一个业务任务设计成这样的系统。全章使用同一套九步方法：先定义结果，再分析任务依赖，随后划分角色、权限、消息和状态，最后用运行轨迹验证。下一页从第一步开始，先把最终交付和验收写清楚。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 21 · 第一步：定义目标与验收结果

多 Agent 设计方法 · 2 分钟

【2 分钟】先定义结果可以避免角色各自写出看似合理但无法汇合的文本。本案例只生成待专家复核的资料报告，不确认故障原因，也不控制真实车辆。验收标准决定后续需要哪些子任务。下一页把这些子任务画成依赖关系。

来源：[道通 Autel · 远程专家](https://www.auteltech.cn/cloud/3942.jhtml)

## 22 · 第二步：画出任务依赖

多 Agent 设计方法 · 2 分钟

【2 分钟】任务依赖先于角色数量。证据读取和知识检索可以从同一工单独立启动；资料适用性必须同时看到两类结果；报告草稿依赖汇合结果；审查可能产生回边。下一页依据这张依赖图判断哪些边界值得拆成角色。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 23 · 第三步：决定是否拆角色

多 Agent 设计方法 · 1 分 50 秒

【1 分 50 秒】依赖图说明任务怎么拆，角色边界还要看产物、上下文、权限和专业责任。仅仅希望得到不同意见，不足以证明要新增 Agent。角色是逻辑职责，不等于单独模型或服务。下一页把拆出的角色写成清晰接口。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 24 · 第四步：定义角色接口

多 Agent 设计方法 · 2 分钟

【2 分钟】角色接口要求输入、输出和禁止事项同时明确。协调者负责路由但不制造事实；证据角色读取本次记录；知识角色给出条件化资料；审查角色只按标准验收。下一页把这些边界落实到工具和权限。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 25 · 第五步：分配工具与权限

多 Agent 设计方法 · 2 分钟

【2 分钟】上一页的不得做什么必须转成运行时限制。工具适配器校验参数和访问范围，编排器限制角色、步数和预算，状态层限制可写字段。仅在提示词里写不要越权不能形成安全边界。下一页继续定义角色之间怎样交接。

## 26 · 第六步：设计消息契约

多 Agent 设计方法 · 2 分钟

【2 分钟】角色接口确定以后，消息契约负责可靠交接。run_id 和 task_id 解决归属，plan_version 防止旧结果覆盖新计划，status 和 missing 说明完整度，evidence_refs 让依据可查询。下一页把有效消息合并进共享状态。

## 27 · 第七步：设计共享状态

多 Agent 设计方法 · 2 分 10 秒

【2 分 10 秒】消息到达后，接收端按照字段所有权更新共享状态。事实不能被草稿覆盖，审查者不能修改证据，模型角色不能自行写入人工批准。并行写入同一字段时必须使用独立字段或明确 reducer。下一页处理状态更新中最容易出错的冲突、重试和版本。
【回看第2–4页】⑥ Blackboard 的共享工作区 + ⑦ 显式图；借鉴黑板的状态协作；本课由图触发节点，未实现状态驱动的黑板调度器。。

来源：[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 28 · 第八步：处理冲突、重试与版本

多 Agent 设计方法 · 2 分 10 秒

【2 分 10 秒】共享状态需要可重复更新，也需要拒绝不合时宜的更新。去重解决重试，来源和时间解释冲突，计划版本隔离迟到结果，重试上限防止死循环。下一页用可观察轨迹检查前八步是否真的工作。

来源：[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)；[LangGraph · Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

## 29 · 第九步：用轨迹验证设计

多 Agent 设计方法 · 2 分钟

【2 分钟】设计完成后，不以一次成功回答作为验收。轨迹要能证明分派、工具调用、并行汇合、修订和停止都按契约发生。到这里，我们已经有了一张可执行协作图。下一章比较五种协作模型如何分配这张图中的控制权。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[Anthropic · Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

## 30 · 协作模型：五种控制关系

协作模型与实现 · 1 分 40 秒

【1 分 40 秒】上一章已经确定任务依赖和角色接口，本章只改变控制权如何移动。五种协作模型不是互斥产品：Supervisor 可以在内部并行，生成结果可以再进入 Review，层次化系统的某一层也可以使用 Handoff。下一页从最容易建立统一出口的 Supervisor 开始。
【回看第2–4页】④ 多 Agent 的组织方式；Supervisor、Parallel、Swarm、Review、Hierarchical 可组合，由⑦表达执行关系。。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 31 · Supervisor：集中分派与汇总

协作模型与实现 · 2 分 10 秒

【2 分 10 秒】Supervisor 每次收回控制权，根据最新状态选择下一位角色。专家角色不需要知道完整团队历史，只需要完成结构化子任务。协调者可以由规则或模型提出决策，但运行时仍校验白名单和预算。下一页保留同一任务图，把可独立的证据与知识分支改为并行。
【回看第2–4页】④ 多 Agent · Supervisor；对应第 3 页 Orchestrator：控制权回到主管，由它统一分派和汇总。。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 32 · Parallel：独立执行与统一汇合

协作模型与实现 · 2 分钟

【2 分钟】Parallel 把前一页的两个独立子任务同时启动，但仍保留统一汇合和验收。一个分支成功不能掩盖另一个必要分支失败，逐步播放界面也不能证明后端并发。下一页讨论另一种控制方式：不回到中央，而由当前角色直接转交。
【回看第2–4页】④ 多 Agent + ⑦ Graph / Workflow；并行是执行方式：两个独立分支完成后汇合，状态按规则合并。。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[Anthropic · Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

## 33 · Handoff、Swarm 与层次化

协作模型与实现 · 2 分钟

【2 分钟】Handoff 和 Swarm 都让控制权沿角色转移，层次化则增加协调层级。它们比集中式更依赖交接契约和无进展检测。本课综合案例不使用 Swarm 或多层团队，因为四个角色还不需要这种复杂度。下一页回到案例会实际使用的反馈模型 Review。
【回看第2–4页】④ 多 Agent · 交接与分层；回看出游多角色演示：比较谁持有控制权，以及交接时保留哪些证据。。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 34 · Review：独立评审与有限修订

协作模型与实现 · 2 分钟

【2 分钟】Review 不是再生成一遍答案，而是用明确标准检查草稿。反馈必须能触发补证据、删除越界表述或重新核对条件。修订次数受全局预算限制。现在五种控制关系已经建立，下一页把它们映射到开发框架，而不是重新讲一遍协作概念。
【回看第2–4页】④ 独立审查 + ③ 反馈机制；延续出游 Reflexion 的失败反馈；本例由独立角色审查，仍需补证据与再验收。。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 35 · 从协作模型到开发框架

协作模型与实现 · 2 分 10 秒

【2 分 10 秒】框架选择发生在流程和角色设计之后。LangGraph 适合显式状态图；AutoGen 更强调消息和团队交互；MetaGPT 强调角色、动作和 SOP。框架不能替代领域工具、权限、验收或终止设计。本课只深入 LangGraph，其他框架保留为结构映射。下一页把前面的设计元素逐项对应到 StateGraph。
【回看第2–4页】架构④ / ⑦ → 开发框架；第 2–4 页讲系统如何组织；LangGraph、AutoGen、MetaGPT 讲用什么实现。。

来源：[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)；[AutoGen · 官方仓库](https://github.com/microsoft/autogen)；[MetaGPT · 官方仓库](https://github.com/FoundationAgents/MetaGPT)

## 36 · LangGraph：把设计映射为状态图

协作模型与实现 · 2 分钟

【2 分钟】State 对应共享状态，Node 对应角色或确定性处理器，Edge 对应控制流，Reducer 负责并行结果合并，END 对应统一出口。代码片段只展示两个分支等待后进入审查。下一章不再增加新概念，而是沿用这张图进入同一份远程诊断工单。
【回看第2–4页】⑦ Graph / Workflow · 本课实现；Node 承载角色或程序，State 保存共享记录，Edge 表达分派、汇合与回路。。

来源：[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)；[LangGraph · Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

## 37 · 案例起点：固定工作流基线

案例演示与复盘 · 2 分 20 秒

【2 分 20 秒】案例从固定工作流开始，沿用前面定义的输入、状态和验收标准。规则已经知道缺电压时调用 read_supplemental，因此不需要 Agent 决定下一步。先确认基线能够生成待人工复核的报告。后面三页只改变控制关系，证据、工具和验收口径保持不变。
【回看第2–4页】⑦ Graph / Workflow · 固定基线；回到第 4 页图编排：已知缺失条件用预设分支处理，先建立可验证的基线。。

来源：[道通 Autel · 远程专家](https://www.auteltech.cn/cloud/3942.jhtml)

## 38 · 案例演示 ①：Supervisor 重新分派

案例演示与复盘 · 2 分 40 秒

【2 分 40 秒】在同一工单上，Supervisor 把固定补读改成集中协调。先看初次分派，再停在协调者发现缺少 E-VOLTAGE 的事件；随后核对计划版本变为 v2，并把补充读取重新分派给证据角色。下一页仍使用同一工单，但观察两个独立分支怎样并行以及怎样合并冲突。
【回看第2–4页】④ 主管分工 + ③ 计划修订 + ⑦ 编排；从出游天气 / 费用分工迁移到证据 / 知识分工，观察反馈如何触发 v2 分派。。

## 39 · 案例演示 ②：Parallel 冲突合并

案例演示与复盘 · 2 分 40 秒

【2 分 40 秒】本页把案例切换到 conflict 情景，角色和状态字段不变。证据与知识并行完成后，汇合节点看到 11.7 V 和较早缓存的 12.6 V；系统依据事件时间说明取舍，同时保留两份记录。下一页继续沿用缺失电压情景，观察问题在草稿之后才被审查者发现时会怎样回退。
【回看第2–4页】④ 独立分工 + ⑥ 共享状态 + ⑦ 并行；延续出游两份结果取交集；冲突读数必须保留来源、时间和合并理由。。

## 40 · 案例演示 ③：Review 退回修订

案例演示与复盘 · 2 分 40 秒

【2 分 40 秒】与 Supervisor 页不同，这次协调者先形成草稿，审查者再发现缺少电压证据。反馈必须指出 E-VOLTAGE，而不是只给低分。系统补充证据后重写并重新审查，revision_rounds 记录实际修订次数。下一页把集中分派、并行取数和评审回路组合进同一条运行。
【回看第2–4页】④ 专业审查 + ③ 反馈回路 + ⑦ 编排；延续出游失败后再验收；这里缺的是电压证据，改措辞不能修复缺失。。

来源：[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 41 · 综合运行：同一状态串起全部流程

案例演示与复盘 · 5 分 20 秒

【5 分 20 秒】综合运行台使用 integrated 模式和同一张 SYNTH-REMOTE-001 工单，把前面三种模型组合起来。先运行 normal，按时间线指出协调分派、并行证据与知识、汇合、草稿和审查。再运行 missing 或 conflict，观察 plan_version、observations 和 review 怎样连续变化。随后运行 tool_failure，确认系统保留错误和已有证据并进入 needs_human；最后运行 budget，确认 status=stopped 且没有伪造成功报告。界面优先看中文故事线、角色图、当前证据和修订前后对照，再展开事件 JSON 核对消息字段。运行台使用规则模拟角色决策和实际 LangGraph 编排，不连接真实车辆。服务不可用时使用预录轨迹，并明确说明是历史回放。完成演示后不要切换新主题，直接进入下一页，用刚才的同一条轨迹反推设计。

## 42 · 案例复盘：从运行轨迹回看设计

案例演示与复盘 · 3 分 10 秒

【3 分 10 秒】最后一页回到流程概念页的四个问题。请学员从刚才的 integrated 轨迹指出流程、角色、状态、模型和异常出口。练习把缺失电压改成等待客户端上传：保存 run_id、plan_version、observations、剩余预算和恢复节点；上传后检查请求版本与幂等键，再从待补充节点恢复。当前 Demo 没有实现跨进程暂停恢复，这一题只做设计。课程结论是先画清流程，再定义角色和状态，最后选择协作模型与框架。
【回看第2–4页】回看架构④ / ⑥ / ⑦；在同一轨迹中分别指出角色分工、共享工作区与图控制；评估新增协作是否值得。。

来源：[LangGraph · Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)；[LangGraph · Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
