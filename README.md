# N5Share · 高级推理框架与多 Agent 协作

面向 Java 后端、前端、客户端开发者的 44 页、120 分钟中文培训。先讲 Agent 基础，用“周末出游”理解七个能力阶段，再进入任务选型、协作架构、开发框架和“接单前资料初审与专家辅助”实战。保留离线 HTML 演示形式。

## 查看培训

- [HTML 演示稿](agent-training/index.html)：下载后用浏览器打开，支持翻页、目录、讲师备注、判断题和离线轨迹回放。
- [新版培训大纲](agent-training/outline.md)
- [逐页讲师讲稿](agent-training/speaker-notes.md)
- [运行说明、练习与验收](agent-training/README.md)
- [选型、协作设计与中英术语速查](agent-training/design-card.md)
- [资料来源与框架维护状态](agent-training/sources.md)
- [完整培训包](Agent-Training-HTML-Demo.zip)

## 内容主线

1. 培训目标与收益 · 5 分钟
2. Agent 基础、三层地图与工作流基线 · 13 分钟
3. 从模型调用到多 Agent 的能力演进 · 13 分钟
4. 按任务复杂度选择搭建方式 · 12 分钟
5. 主管委派、并行分析、提案与评审 · 22 分钟
6. AutoGen / MetaGPT / LangGraph 选型 · 12 分钟
7. 工作流基线与三种协作方式演示 · 15 分钟
8. 四角色案例、等待客户端上传设计练习和问答 · 28 分钟

前 6 页重写为开场与基础，原第 7–9 页内容合并到相关讲解中，第 7 页开始能力演进；总页数和各章时长不变。七个互动演示依次为 LLM、RAG、Tool Calling、ReAct、Plan-and-Execute、Reflexion、Multi-Agent，都使用周末出游任务，可选择晴天/雨天和 300/200/100 元预算。演示由浏览器本地固定样例驱动，结果可重复，不调用真实模型、实时天气或预订服务。

已知条件与工具映射用工作流；“下一步依赖证据”本身不构成 Agent。路径难以穷举、需要解释非结构化信息并选择工具时才评估 Agent；新增独立上下文、权限或专业责任需求时再评估角色拆分。原始固定字段任务用 `workflow` 即可。

后半程唯一业务背景来自[道通远程专家官方中文页](https://www.auteltech.cn/cloud/3942.jhtml)。实战设定为门店报告通信故障 U0121 并请求远程专家咨询：接单前汇总电压、故障码、网关记录和知识资料，补齐缺失、核对冲突记录的采集时间，提交专家人工复核。AI 初审和角色分工是课程设计；官网“AI 智能匹配”不能据此推断其采用 LLM 或多 Agent。

## 运行现场演示

需要 Python 3.10+ 和 LangGraph；默认不需要模型、API Key 或外部产品账号。Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r agent-training/requirements.txt
.\.venv\Scripts\python.exe agent-training/demo/server.py
```

浏览器打开 http://127.0.0.1:8765，从目录进入“诊断运行台”。也可安装后双击 agent-training/start-demo.cmd。

默认使用规则模拟决策，真实运行 LangGraph 编排与只读仿真工具。工作流基线加四种协作模式，共五种模式、五种情景、25 份预录轨迹。运行台提供中文故事线、角色图、当前已观察证据、修订前后对照、可展开的事件 JSON、最终报告与状态。“基线与三种模式”同情景比较 `workflow / supervisor / parallel / review`，`integrated` 用于综合案例。基线补读是预设分支，计划保持 v1、修订为 0，无 Revision/Dispatch。

离线回放明确标记为预录记录。案例不连接或操作真实车辆，不声称道通内部采用同样架构；网络链路状态不能证明车辆故障。`review / missing` 缺的是电压，演示评审退回、补充电压和重新审查通过。七个出游演示用于讲清能力差异，与这套五模式、五情景的诊断运行台分开。

最后练习设计“等待客户端上传”：暂停、保存、恢复、幂等、过期上传、角色和消息契约。参考答案见[培训说明](agent-training/README.md)与[设计卡](agent-training/design-card.md)；上传接口和持久暂停恢复明确尚未实现。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s agent-training/demo -v
.\.venv\Scripts\python.exe agent-training/build.py --package
```

本课选择 LangGraph 是为了显式展示状态、分支、汇合与回路；领域规则、权限、预算和恢复仍需自己实现。消息团队与对话委派需求可评估 AutoGen，角色 SOP 与独立产物需求可评估 MetaGPT；先确定服务边界，不假设各语言 SDK 能力对等。

官方资料核对于 2026-09-21：AutoGen 已进入维护模式，其官方推荐新项目评估 Microsoft Agent Framework。MetaGPT README 的 Python 范围为 ≥3.9 且 <3.12，采用前另核对依赖，不与主 Demo 混装。
