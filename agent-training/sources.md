# 来源、版本与事实边界

核对日期：2026-09-21。来源用于支持机制和产品背景；教学架构、仿真资料、待复核假设与练习由本课程编写。离线 HTML 不依赖外部链接。业务背景仅采用道通远程专家官方中文页，机制论文与框架文档用于解释技术，不用于推断产品内部实现。

## 推理与协作机制

- [Building effective agents · Anthropic](https://www.anthropic.com/engineering/building-effective-agents)：预定义工作流与模型动态决策的区分，parallelization、orchestrator-workers、evaluator-optimizer。本文也提醒工具生态已变化；本课程采用模式解释，不把文中的旧工具清单作为当下选型结论。
- [How we built our multi-agent research system · Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)：主管与并行研究子 Agent 的公开产品实践。研究任务的收益不直接推广到车辆诊断；不复述未经本课程验证的性能数字。
- [ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)：行动与观察交错，为单 Agent 闭环提供概念来源。界面仅展示决策摘要，不声称是模型完整内部思维。
- [Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)：语言反馈、经验与后续尝试。课堂评审修订是工程简化示例，不是论文复现，不涉及更新模型权重。
- [Plan-and-Execute · LangChain](https://blog.langchain.com/planning-agents/)：规划与执行分工、重新规划。是否节省时延或调用成本依赖具体任务。

## 开发框架：核对结果与取舍

| 框架 | 本次查到的事实 | 课程处理 |
| --- | --- | --- |
| [AutoGen](https://github.com/microsoft/autogen) | README 明确标注 Maintenance Mode；不增加新特性或增强，后续由社区维护；新用户推荐 Microsoft Agent Framework | 保留其 AgentChat、消息和委派思路的教学价值；新项目评估后继框架，不当作默认首选 |
| [MetaGPT](https://github.com/FoundationAgents/MetaGPT) | README 强调角色、软件团队与 SOP；安装指导要求 Python >=3.9、<3.12，并有 Node/pnpm 前置要求 | 展示 Role / Action / Team 概念与结构映射；本课程不安装或运行 MetaGPT，不将其要求误套到主 Demo |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | 官方文档定位为有状态的底层编排运行时，可混合确定性代码和模型决策；支持持久化、流式与人工介入 | 主案例实际使用 StateGraph；默认节点决策采用规则模拟。框架能力不等于课堂 Demo 已配置全部能力 |

补充：
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)：State、Node、Edge、reducer、并行与条件路由。
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：正式人工介入和恢复的进一步阅读。课堂报告窗口只交付审核材料，不宣称已实现生产级审批或持久化恢复。
- [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)：子 Agent、路由、技能与交接的相关设计。
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)：AutoGen 官方推荐的新项目及迁移方向，仅作维护状态补充。
- [Ollama Chat API](https://docs.ollama.com/api/chat)：扩展真实模型时的接口阅读资料；本版不包含模型调用适配器。

本次读取的是各项目当前公开文档，不固定或承诺 AutoGen、MetaGPT 最新发行版号，也不凭 README 的存在判断发布活跃度。开课或生产选型前应再次检查 Releases、兼容矩阵和迁移说明。实际安装测试的 LangGraph 版本见 requirements.txt。

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

## 前半程：周末出游的七阶段演示

第 7 页开始按 LLM、RAG、Tool Calling、ReAct、Plan-and-Execute、Reflexion、Multi-Agent 展示能力演进。出游资料、天气和费用均为本地固定样例；晴天/雨天与 300/200/100 元预算由学员选择。演示不调用真实模型、实时天气或预订服务，也不代表真实模型的推理过程或效果评测。ReAct、规划与反思等概念可参阅前列资料；课堂交互是简化说明，不是论文复现。

七阶段演示与后半程诊断运行台分开。诊断运行台继续保留五模式×五情景、25 份预录轨迹及原有合成工具行为；本次业务调整只修改任务语境。

## 仿真与验证边界

- 工单、车辆、检测数据和知识条目均为合成资料；不对应真实客户或真实车辆。
- “主管、分析、评审”是课程设计角色；默认通过规则模拟决策，实际执行 LangGraph 图和仿真只读工具。
- 模式与情景切换不会切换成真实产品接口，不执行刷写、清码、支付或车辆控制。
- verified 表示教学证据契约通过；completed 表示报告生成，均不表示真实诊断成立或已获人工批准。
- 回放中耗时是录制时本机的一次测量；现场耗时是本次执行测量。两者都不能推导真实模型费用、诊断准确率或生产性能排名。
- 框架对比和工具白名单、预算、消息契约等建议属于教学与工程取舍，不构成某个框架效果优于其他框架的实验结论。
