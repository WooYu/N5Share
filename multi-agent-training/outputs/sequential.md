# AI Agent协作模式选型

Backend: offline-simulation

[离线模拟 / seo] AI Agent协作模式选型
[离线模拟 / writer] AI Agent协作模式选型
## 建议
步骤明确时先用Sequential Chain；需要动态任务分发时采用Supervisor；需要自主交接时采用Swarm。[source-02][source-04][source-05]

## 工程约束
为子团队设置唯一名称，合并消息时避免重复历史，给路由设置白名单和调用上限。[source-03][source-06]

## 验收
核查输出来源与任务完成情况。人工审批前不继续执行后续测试；本地工具不能冒充互联网搜索。[source-01][source-07]

## 本地依据
[source-01] 多Agent的核心区别：每个真实Agent拥有独立的模型上下文和角色提示词。固定函数分工不等于自主Agent；是否需要多Agent应根据任务复杂度和成本判断。
[source-02] Supervisor：中央调度Agent分配任务，Worker执行后汇报，适用于动态分发和结果整合。中心节点可能形成调度瓶颈。
[source-03] Hierarchical：多层Supervisor管理多个子团队。编译后的子图应具有唯一名称，顶层才能区分不同子团队。
[source-04] Swarm：Agent通过Handoff主动交接控制权，没有统一中央调度。必须设置退出条件与调用上限。轮询式讨论不等于自主交接。
[source-05] Sequential Chain：研究、提纲、草稿、编辑和SEO按照固定顺序执行。步骤确定时可采用工作流，未必需要自主调度。
[source-06] Network：对等Agent可自由路由。路由结果要校验，消息要正确合并，并设置步数或递归限制，防止无限循环。
[source-07] 协议与安全：A2A连接Agent与Agent，MCP连接应用与工具或数据。工具白名单、超时和预算检查需要由执行代码落实；结构化消息不能保证防止提示词注入。

关键词：多Agent、Supervisor、Swarm、顺序流水线、消息状态、人工审批。
