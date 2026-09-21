# N5Share · 高级推理框架与多 Agent 协作

面向 Java 后端、前端、客户端开发者的 41 页、90 分钟中文培训。先讲 Agent 基础，用“周末出游”理解七个能力阶段，再进入任务选型、协作架构、开发框架和“接单前资料初审与专家辅助”实战。保留离线 HTML 演示形式。

## 查看培训

- [HTML 演示稿](agent-training/index.html)：下载后用浏览器打开，支持翻页、目录、讲师备注、判断题和离线轨迹回放。
- [新版培训大纲](agent-training/outline.md)
- [逐页讲师讲稿](agent-training/speaker-notes.md)
- [运行说明、练习与验收](agent-training/README.md)
- [选型、协作设计与中英术语速查](agent-training/design-card.md)
- [资料来源与框架维护状态](agent-training/sources.md)
- [完整培训包](Agent-Training-HTML-Demo.zip)

## Studio 对比入口

本机启动 `agent-training/start-studio.cmd` 后，打开 [LangSmith Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)。提供 `outing_react` 和 `outing_supervisor` 两个原生 LangGraph 图，与课件共用模型、工具和验收逻辑；支持节点状态查看和汇总前暂停恢复。详细操作见 [Studio 演示指南](agent-training/studio-guide.md)。默认关闭云端追踪，模型凭据留在本地。

## 内容主线

1. 开场与目标 · 2 分 30 秒
2. Agent 基础 · 2 分 30 秒
3. 能力演进 · 10 分 50 秒
4. 按复杂度选择方案 · 10 分钟
5. 多 Agent 协作设计 · 18 分 20 秒
6. 三种框架的工程取舍 · 10 分钟
7. 工作流基线与三个短演示 · 12 分 30 秒
8. 综合实战与落地 · 23 分 20 秒

前 3 页为封面、90 分钟安排与学习路线，第 04 页开始能力演进。原 03、04、06 页已移除，保留的 108 分钟按 5/6 等比例压缩至 90 分钟。七个互动演示依次为 LLM、RAG、Tool Calling、ReAct、Plan-and-Execute、Plan-and-Execute + Reflexion、Multi-Agent，都使用周末出游任务，可选择晴天/雨天和 300/200/100 元预算。“下一步演示”使用本地规则示意；新增“真实模型演示”通过 CCSwitch 当前供应商与官方 Codex CLI 生成行动和答案，工具仍读取合成资料。

能力演进明确讲解 Thought-Action-Observation 循环、先规划再执行与失败后的自我修正，并比较 Supervisor、层次化、Swarm 的控制权及 Agent 间通信与共享状态。真实模型的运行方法、课堂提示词、工具执行要求和演示边界见[大模型演示指南](agent-training/model-demo-guide.md)。

已知条件与工具映射用工作流；“下一步依赖证据”本身不构成 Agent。路径难以穷举、需要解释非结构化信息并选择工具时才评估 Agent；新增独立上下文、权限或专业责任需求时再评估角色拆分。原始固定字段任务用 `workflow` 即可。

后半程唯一业务背景来自[道通远程专家官方中文页](https://www.auteltech.cn/cloud/3942.jhtml)。实战设定为门店报告通信故障 U0121 并请求远程专家咨询：接单前汇总电压、故障码、网关记录和知识资料，补齐缺失、核对冲突记录的采集时间，提交专家人工复核。AI 初审和角色分工是课程设计；官网“AI 智能匹配”不能据此推断其采用 LLM 或多 Agent。

## 运行现场演示

需要 Python 3.10+ 和 LangGraph；离线模式与诊断运行台不需要模型。能力演进的真实模式另需官方 Codex CLI，以及 CCSwitch 当前选中的 Codex 供应商和有效凭据。Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r agent-training/requirements.txt
.\.venv\Scripts\python.exe agent-training/demo/server.py
```

浏览器打开 http://127.0.0.1:8765，从目录进入“诊断运行台”。也可安装后双击 agent-training/start-demo.cmd。

诊断运行台使用规则模拟决策，真实运行 LangGraph 编排与只读仿真工具。能力演进第 04–10 页可点击“真实模型演示”，支持七阶段及 Supervisor / 层次化 / Swarm，显示模型、调用次数、token 和实际过程。当前凭据仅允许官方 Codex 客户端，程序实际调用官方 CLI，不向浏览器提供密钥；每次运行按供应商规则产生用量。工作流基线加四种协作模式，共五种模式、五种情景、25 份预录轨迹。运行台提供中文故事线、角色图、当前已观察证据、修订前后对照、可展开的事件 JSON、最终报告与状态。“基线与三种模式”同情景比较 `workflow / supervisor / parallel / review`，`integrated` 用于综合案例。基线补读是预设分支，计划保持 v1、修订为 0，无 Revision/Dispatch。

能力演进支持 DeepSeek 官方接口 `deepseek-flash` 作为备用，主接口连接失败或超时等异常会显式切换并保留当前状态。凭据保存在本机受保护存储中，不随培训包分发。

离线回放明确标记为预录记录。案例不连接或操作真实车辆，不声称道通内部采用同样架构；网络链路状态不能证明车辆故障。`review / missing` 缺的是电压，演示评审退回、补充电压和重新审查通过。七个出游演示用于讲清能力差异，与这套五模式、五情景的诊断运行台分开。

最后练习设计“等待客户端上传”：暂停、保存、恢复、幂等、过期上传、角色和消息契约。参考答案见[培训说明](agent-training/README.md)与[设计卡](agent-training/design-card.md)；上传接口和持久暂停恢复明确尚未实现。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s agent-training/demo -v
.\.venv\Scripts\python.exe agent-training/build.py --package
```

本课选择 LangGraph 是为了显式展示状态、分支、汇合与回路；领域规则、权限、预算和恢复仍需自己实现。消息团队与对话委派需求可评估 AutoGen，角色 SOP 与独立产物需求可评估 MetaGPT；先确定服务边界，不假设各语言 SDK 能力对等。

官方资料核对于 2026-09-21：AutoGen 已进入维护模式，其官方推荐新项目评估 Microsoft Agent Framework。MetaGPT README 的 Python 范围为 ≥3.9 且 <3.12，采用前另核对依赖，不与主 Demo 混装。
