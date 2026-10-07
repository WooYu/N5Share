# 来源、版本与事实边界

核对日期：2026-09-21。来源用于支持机制和产品背景；教学架构、仿真资料、待复核假设与练习由本课程编写。离线 HTML 不依赖外部链接。业务背景仅采用道通远程专家官方中文页，机制论文与框架文档用于解释技术，不用于推断产品内部实现。

## 导入的多 Agent 协作文档

2026-10-07 内容迁移与核对。用户提供的 `../multi-agent-training/sources/04_HTML演示文档.html` 是第 12 至 40 页的直接内容来源；迁入范围从 sec02“五种协作模式总览”开始，包含 sec03–sec12 和末尾 FAQ。原第 12、13 页合并为第 12 页，以五幅图保留 sec02 五张说明卡的名称、定义和适用场景，补上分类重叠、按需交接与全连接示例的边界。详解修正维护在 course/collaboration_corrections.py，原文快照不改动；跨页代码复制使用修正后的完整示例。

完整原文副本见 [本地导入文档](../assets/imported/multi-agent-source.html#sec02)。原第 12 至 34 页及迁移前讲稿、大纲保存在 [归档目录](../archive/2026-10-07-before-collaboration-import/README.md)。旧开发框架和诊断案例已移出主课件；新增第 27 至 33 页框架选型与上手后，现为 47 页、85 分钟。

2026-10-08 培训形式改版：第 13 至 26 页引导讲师进入 VS Code 展示完整程序、运行并检查过程与结果。course/collaboration_vscode.py 生成结构、真实源码节选与运行命令；demo/collaboration_live 使用实际 LangGraph 图、团队子图和真实模型角色/路由。DeepSeek 主用，现有 OpenAI/Codex 连接备用；资料为固定课堂数据，工具与验收由 Python 执行。旧规则回放保留作历史参考。AG2 Playground 的 Sequential Chat、Nested Chat、Auto Pattern 与 LLM Condition 已核对公开页面，可选作短时间机制对照；不声称网站完整覆盖本课五种模式，也不将 Auto Pattern 等同 Swarm。详见五模式演示指南。

## 导入内容与框架章节的页脚参考对应

2026-10-07 核对官方页面。页脚用于概念延伸阅读；讲稿同步采用这些链接。五模式是本课程沿用的教学分类，可组合且有重叠，官方文档的分类名称可能不同。Swarm 是当前角色按需交接，AutoGen 对应 Swarm / handoffs，SelectorGroupChat 属于集中选择。Network 示例在各角色节点内部决定下一跳；全连接是本课示例。顺序链外层固定顺序不排除阶段内部重试。开销与容错不作为未经测量的固定等级。

| 页码 | 概念 | 官方参考 |
| --- | --- | --- |
| 12 | 五模式图示总览 | [LangChain 多 Agent](https://docs.langchain.com/oss/python/langchain/multi-agent)、[Anthropic Agent 模式](https://www.anthropic.com/engineering/building-effective-agents)。 |
| 13 | 共同任务 | 多 Agent 总览、Anthropic Agent 模式；出游数据与角色为本课程编写。 |
| 14 至 15 | Sequential Chain | [顺序工作流](https://docs.langchain.com/oss/python/langgraph/workflows-agents#prompt-chaining)、[Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)。 |
| 16 至 17 | Supervisor | [主管与子 Agent](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)、多 Agent 总览。 |
| 18 至 19 | Hierarchical | 主管与子 Agent、[LangGraph 子图](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)。 |
| 20 至 21 | Swarm | [Agent 交接](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)、[AutoGen Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html)。 |
| 22 至 23 | Network | Agent 交接、Graph API；代码页补充 [结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output)。 |
| 24 至 26 | 对比、练习与模型接入 | 多 Agent 总览、Anthropic Agent 模式；练习与接入位置为本课程编写。 |
| 27 至 33 | 框架选型与上手 | MAF 官方仓库与完整示例、LangGraph Graph API / Persistence、MetaGPT 官方仓库；课件为概念图与观察提示，完整源码在 VS Code 展示。 |
| 34 至 36 | 开发团队、审批与恢复 | 主管与子 Agent、[人工审批](https://docs.langchain.com/oss/python/langgraph/interrupts)、[状态持久化](https://docs.langchain.com/oss/python/langgraph/persistence)。 |
| 37 至 38 | A2A、MCP | [A2A 规范](https://a2a-protocol.org/latest/specification/)、[MCP 架构](https://modelcontextprotocol.io/docs/learn/architecture)、[MCP 服务端能力](https://modelcontextprotocol.io/docs/learn/server-concepts)。 |
| 39 至 41 | 安全 | [LangChain Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails)、[MCP 安全实践](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices)。 |
| 42 至 44 | 工程挑战、决策、性能 | [容错](https://docs.langchain.com/oss/python/langgraph/fault-tolerance)、持久化；决策页为多 Agent 总览与 Anthropic 模式，性能页为多 Agent 文档的调用次数和 Token 比较。 |
| 45 至 46 | 小结与选型、成本、协议 FAQ | 多 Agent 总览、A2A 规范、MCP 架构。 |
| 47 | 流水线、安全、路由 FAQ | 顺序工作流、Guardrails、结构化输出。 |

这些参考用于理解机制，不代表官方文档逐字支持导入文档中的全部代码版本、性能数字或安全建议。

## 架构章节的页脚参考

资料核对于 2026-10-07，页码按当前课件排列。页脚链接用于机制说明与进一步阅读；七种架构地图、出游数据和交互由课程编写。

| 页码 | 页面主题 | 参考与对应范围 |
| --- | --- | --- |
| 01 | 课程封面 | 无外部链接，底部为章节说明。 |
| 02 | 课程大纲 | 无外部链接，列出五部分课程安排。 |
| 03 | 七种架构总览 | Anthropic 模式文章、LangChain 多 Agent、LangGraph 概览：组合能力、角色组织与图编排的通用参考。七种架构是本课整理的分类。 |
| 04 | 单 Agent / ReAct / 规划执行 / 多 Agent | ReAct 原论文、LangChain 规划文章、多 Agent 文档：对应决策循环、规划与执行、角色协作。 |
| 05 | Router + Skill / Blackboard / Graph | LangChain Skills：按需加载能力和资源；Blackboard：共享工作区、知识源与控制器；LangGraph Graph API：节点、状态、条件边。 |
| 06 | 单 Agent 组合 RAG 与工具 | Anthropic 模式文章的 augmented LLM：检索、工具与记忆。 |
| 07 | ReAct | ReAct 原论文：决策与行动交错，根据观察继续。 |
| 08 | Plan & Execute + Reflexion | LangChain 规划文章与 Reflexion 原论文：规划执行、反馈与后续尝试。 |
| 09 | 多 Agent | LangChain 多 Agent 文档：独立上下文、子角色、交接及汇总。 |
| 10 | Router + Skill | Anthropic 的 Routing 段落与 LangChain Skills：意图分流和按需加载技能 / Reference。 |
| 11 | Blackboard | [Blackboard system](https://en.wikipedia.org/wiki/Blackboard_system)：状态匹配触发专业知识源、共享黑板和控制器。图调度与黑板就绪调度需要分别设计。 |
| 12 | Graph / Workflow | LangGraph 概览与 Graph API：节点、边与条件路由。出游图由浏览器 / 本地代码执行。 |

[LangChain Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills) 描述渐进加载、组合和脚本 / 模板等资源引用；[Blackboard system](https://en.wikipedia.org/wiki/Blackboard_system) 说明共享知识库、专业知识源与控制器，对应第 11 页的就绪条件调度。

## 推理与协作机制

- [Building effective agents · Anthropic](https://www.anthropic.com/engineering/building-effective-agents)：预定义工作流与模型动态决策的区分，parallelization、orchestrator-workers、evaluator-optimizer。本文也提醒工具生态已变化；本课程采用模式解释，不把文中的旧工具清单作为当下选型结论。
- [How we built our multi-agent research system · Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)：主管与并行研究子 Agent 的公开产品实践。研究任务的收益不直接推广到车辆诊断；不复述未经本课程验证的性能数字。
- [ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)：行动与观察交错，为单 Agent 的行动与反馈过程提供概念来源。界面仅展示决策摘要，不声称是模型完整内部思维。
- [Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)：语言反馈、经验与后续尝试。课堂评审修订是工程简化示例，不是论文复现，不涉及更新模型权重。
- [Plan-and-Execute · LangChain](https://blog.langchain.com/planning-agents/)：规划与执行分工、重新规划。是否节省时延或调用成本依赖具体任务。

## 开发框架：核对结果与取舍

| 框架 | 资料中的说明 | 课程处理 |
| --- | --- | --- |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) | 官方仓库提供 Python / .NET Agent、工具、图工作流，以及检查点、流式、人工介入与可观测性相关能力 | 第 22 页介绍能力和官方 DevUI 图片，附官方指南与示例；没有本地 MAF 程序 |
| [AutoGen](https://github.com/microsoft/autogen) | README 明确标注 Maintenance Mode；新用户推荐 Microsoft Agent Framework | 仅说明维护与迁移关系，新项目框架介绍直接使用 MAF |
| [MetaGPT](https://github.com/FoundationAgents/MetaGPT) | README 强调角色、软件团队与 SOP；安装指导要求 Python >=3.9、<3.12，并有 Node/pnpm 前置要求 | 第 24 页介绍 Role / Action / Team；第 25 至 32 页运行本地 Review Agent，使用独立 Python 3.11 环境 |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | 官方定位为有状态的底层编排运行时；支持混合确定性代码与模型步骤、持久化和人工介入 | 第 23 页介绍状态图与恢复；第 17 至 21 页运行本地五模式源码，恢复能力需另行配置和验证 |

补充：
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)：State、Node、Edge、reducer、并行与条件路由。
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：正式人工介入和恢复的进一步阅读。课堂报告窗口只交付审核材料，不宣称已实现生产级审批或持久化恢复。
- [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)：子 Agent、路由、技能与交接的相关设计。
- [Microsoft Agent Framework samples](https://github.com/microsoft/agent-framework/tree/main/python/samples)：第 22 页官方示例的入口，具体示例与依赖由讲师课前验证。
- [Ollama Chat API](https://docs.ollama.com/api/chat)：扩展真实模型时的接口阅读资料；本版不包含模型调用适配器。

框架介绍资料于 2026-10-08 核对官方仓库与文档，不固定或承诺最新发行版号，也不凭 README 的存在判断发布活跃度。第 27 至 33 页选型结论是工程建议，不是效果评测。开课或生产选型前应再次检查 Releases、兼容矩阵和迁移说明。实际安装测试的 LangGraph 版本见 requirements.txt。

## 业务背景：道通远程专家

唯一业务来源：[道通远程专家官方中文页](https://www.auteltech.cn/cloud/3942.jhtml)。以下事实依据该页面正文整理。

| 官方页面信息 | 可支持的课程表述 |
| --- | --- |
| 集合在线专家和客户的远程汽车维修综合服务平台 | 门店与远程专家协作的业务背景 |
| 远程诊断、编程、防盗、ADAS、咨询 | 平台服务范围；课堂只选咨询前的资料整理 |
| VIN 信息、导入报告、发布订单 | 客户可围绕车辆信息与报告发起服务需求 |
| AI 智能匹配专家 | 页面披露了匹配能力，但没有披露其算法或模型架构 |
| 语音、文字、视频、电话 | 客户与专家可通过多种方式沟通 |
| 实时服务状态、连接状态 | 用户可以了解服务进展与连接情况；连接状态不是车辆故障结论 |

该页面未披露 LLM、推理策略或多 Agent 内部实现，不能把“AI 智能匹配”解释成本课的主管、并行或评审架构，也不能据此宣称厂商已实现本课 AI 初审流程。

实战“接单前资料初审与专家辅助”为教学改编：门店报告通信故障 U0121 并请求远程专家咨询；接单前汇总电压、故障码、网关记录与知识资料，补充缺失项，核对冲突记录的事件时刻和采集时间，最后交专家人工复核。任务、角色、数据与知识规则均为合成教学设定，不是官方维修规范，也不是已披露的产品内部工作流。

## 前半程：周末出游的七种架构演示

第 6 至 12 页按与第 3 至 5 页相同的顺序展示单 Agent、ReAct、Plan & Execute、多 Agent、Router + Skill、Blackboard、Graph / Workflow。LLM、RAG 和工具合并到①，Reflexion 合并到③。天气、场馆、费用均为合成样本；晴雨与 300/200/100 元预算由学员选择。离线演示不调用模型；七页均另有真实模型入口，工具仍只读合成资料。第 10 至 12 页分别保持关键词路由、最小状态就绪调度和显式图的控制机制，在技能执行、专业角色或结果节点调用真实模型，不宣称完整语义路由或生产级黑板实现。课后诊断的共享状态仍由 LangGraph 调度。课堂交互为简化机制说明，不是论文复现或模型效果评测。

七种架构的出游演示保留在主课件中。诊断运行台已随原第 41 至 48 页删除，五模式×五情景的 25 份预录轨迹及合成工具源代码保留为课后参考。

## 仿真与验证边界

- 工单、车辆、检测数据和知识条目均为合成资料；不对应真实客户或真实车辆。
- “主管、分析、评审”是课程设计角色；默认通过规则模拟决策，实际执行 LangGraph 图和仿真只读工具。
- 模式与情景切换不会切换成真实产品接口，不执行刷写、清码、支付或车辆控制。
- verified 表示教学证据契约通过；completed 表示报告生成，均不表示真实诊断成立或已获人工批准。
- 回放中耗时是录制时本机的一次测量；现场耗时是本次执行测量。两者都不能推导真实模型费用、诊断准确率或生产性能排名。
- 框架对比和工具白名单、预算、消息契约等建议属于教学与工程取舍，不构成某个框架效果优于其他框架的实验结论。
