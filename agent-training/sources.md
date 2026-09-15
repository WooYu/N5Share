# 来源与事实边界

核对日期：2026-09-10。外部链接用于进一步阅读；HTML 核心讲解不需要联网。课程中的教学案例、示意 JSON、统计样本和架构建议由本培训包编写，不伪称来自论文实验。

1. **Yao et al., ReAct: Synergizing Reasoning and Acting in Language Models.** ICLR 2023；[arXiv:2210.03629](https://arxiv.org/abs/2210.03629)。支持推理轨迹与任务行动交错、从环境获取信息、根据反馈更新行动计划的机制。已核对摘要。课程不引用论文基准增益来推断当前模型效果。
2. **Shinn et al., Reflexion: Language Agents with Verbal Reinforcement Learning.** NeurIPS 2023；[arXiv:2303.11366](https://arxiv.org/abs/2303.11366)。支持语言反馈、episodic memory 与后续尝试，不更新模型权重。已核对摘要。Demo 是简化教学实现，不是原论文实验复现。
3. **LangChain, Plan-and-Execute Agents, 2024-02-13.** [官方文章](https://blog.langchain.com/planning-agents/)。支持规划者与执行器分工、结果检查与重新规划。成本、速度和质量依赖任务与实现，本课不保证普遍收益。
4. **AutoGen 官方仓库。** [microsoft/autogen](https://github.com/microsoft/autogen)。核对 main 分支 README：标注 Maintenance Mode，说明不再增加新特性，建议新用户采用 [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)。Core、AgentChat、Extensions 分层与旧版 0.2 迁移提示来自此 README。课程以当前分层概念讨论，不提供混用版本的 AutoGen 执行代码。README 可变，开课前应复核。
5. **MetaGPT 官方仓库。** [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT)。核对 README 的角色与软件团队 SOP 定位，并保留它也有 Data Interpreter 等用例的说明。当前 README 的 Python 范围为 3.9 至小于 3.12；本课程标准库 Demo 的 Python 3.10+ 要求与 MetaGPT 安装要求分开，不在同一环境中混装框架。
6. **LangGraph 官方概览与仓库。** [文档](https://docs.langchain.com/oss/python/langgraph/overview)、[仓库](https://github.com/langchain-ai/langgraph)。核对 README 中有状态、长时运行、持久执行、人工介入与记忆支持；可以独立于 LangChain 使用。演示中的简化编排不声称自动拥有这些生产能力。
7. **LangGraph Graph API。** [官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。用于状态、节点、边、reducer 等术语与进一步学习。
8. **LangChain Multi-agent。** [官方文档](https://docs.langchain.com/oss/python/langchain/multi-agent)。用于监督、子 Agent 和 handoff 等协作设计的进一步阅读。本课 Supervisor / 层次化 / Swarm 是教学分类，不宣称是唯一标准；Swarm 明确指模式而非同名 SDK。
9. **Ollama Generate a chat message。** [官方 API 文档](https://docs.ollama.com/api/chat)。可选适配器使用 `/api/chat`、`messages`、`format: json`、`stream: false`；本次未安装本地模型，不宣称真实推理端到端已验证。

## 课程原创的工程建议

工具白名单、结构化消息契约、状态写入责任、预算、幂等和独立验收属于本课的工程实践建议。它们不因采用某个推理范式而自动具备，需要在宿主运行时实现并测试。

Thought 页面展示的是简短的教学决策摘要，不是模型完整内部思维。故障开关是人为注入，不用来证明模型的自然错误率。角色拆分和框架选型没有进行性能跑分，比较表不包含未经支持的效果排名。
