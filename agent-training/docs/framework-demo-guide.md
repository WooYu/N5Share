# 三种框架介绍与官方入口

第 22 至 24 页，一框架一页。总计 18 分钟，包含点击官方指南与示例的讲解时间。

| 页码 | 框架 | 时间 | 图中观察点 |
| --- | --- | --- | --- |
| 22 | Microsoft Agent Framework | 7 分钟（含衔接 1 分钟） | DevUI 中工作流执行状态、天气助手对话与工具调用事件 |
| 23 | LangGraph | 6 分钟 | Studio 图结构、输入区域和提交入口；截图尚无执行轨迹 |
| 24 | MetaGPT | 5 分钟 | 官方番茄钟项目的类与接口设计产物 |

每页先说明能力与适用任务，再对照官方图片，打开指南或示例查看接入步骤。

图片均来自官方资料，不代表本课程序运行结果。点击图片打开离线原图；图片来源与现行工具说明见 [来源记录](../assets/frameworks/SOURCES.md)。LangGraph 的 Studio 截图来自官方发布文章，界面可能与当前版本不同；现行 Studio 属于 LangSmith 工具。

## 官方集成与示例

- MAF：[Quick Start](https://learn.microsoft.com/agent-framework/tutorials/quick-start)、[Python samples](https://github.com/microsoft/agent-framework/tree/main/python/samples)、[.NET samples](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples)。可从工具调用示例开始，再阅读工作流示例。
- LangGraph：[Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)、[人工中断与恢复示例](https://docs.langchain.com/oss/python/langgraph/interrupts)。需要检查点存储和任务标识；已有五模式实现仍可从 [演示指南](collaboration-demo-guide.md) 运行。
- MetaGPT：[安装指南](https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html)、[模型配置](https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html)、[2048 与数据分析示例](https://github.com/FoundationAgents/MetaGPT#usage)、[examples](https://github.com/FoundationAgents/MetaGPT/tree/main/examples)。官方 README 要求 Python ≥3.9 且 <3.12，并列出 Node / pnpm；按版本准备独立环境。

课堂不要求临时安装所有框架。若需运行官方示例，讲师提前锁定版本、配置模型并验证结果；MAF 未新增本地演示程序。MetaGPT 在第 25 至 32 页已有本地开发团队与 Review Agent 实战，使用独立 Python 3.11 环境，准备与运行见 [实战手卡](dev-team-demo-guide.md)。运行后还要按需求与测试检查生成结果。
