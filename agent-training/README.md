# 高级推理框架与多 Agent 协作 · 培训包

48 页、90 分钟，面向 Java 后端、前端、客户端开发者。学习顺序是“学习路线 → 周末出游的七阶段能力演进 → 任务选型 → 协作与框架 → 远程专家辅助实战 → 系统设计”。每个能力阶段新增一页一分钟概念图，再进入对应演示。概念讲解增加的 7 分钟，从任务选型、协作设计说明与框架比较中合计压缩，实战时间不变；逐页和逐章以整秒计算，合计 90 分钟。能力演进从新版第 04 页开始。

八章用时：开场与目标 2 分 30 秒；Agent 基础 2 分 30 秒；能力演进 17 分 50 秒；按复杂度选择方案 8 分钟；多 Agent 协作设计 16 分 20 秒；三种框架的工程取舍 7 分钟；工作流基线与三个短演示 12 分 30 秒；综合实战与落地 23 分 20 秒。

入口：[演示稿](index.html) · [大纲](outline.md) · [讲师讲稿](speaker-notes.md) · [选型与设计卡](design-card.md) · [来源](sources.md)。

## 离线演示

直接用 Chrome 或 Edge 打开 index.html，无需前端依赖或 CDN。支持翻页、目录、讲师备注、七个能力阶段互动演示、三道判断题及诊断运行台的 25 份预录轨迹。HTML 内没有 API Key。

| 操作 | 快捷键 |
| --- | --- |
| 上一页 / 下一页 | ← / →、PageUp / PageDown、空格 |
| 第一页 / 最后一页 | Home / End |
| 目录 / 讲师备注 | O / N |
| 全屏 / 帮助 | F / ? |
| 关闭弹窗 | Esc |
| 打印讲义 | Ctrl+P，横向，开启背景图形 |

页面保持 16:9 投影布局；窄屏整体缩放，推荐桌面演示。讲师备注弹窗与投影共屏，私有备课请在另一设备打开 speaker-notes.md。

## 先理解基础与能力演进

前 3 页建立目标、时间安排与学习路线；第 04–17 页用简单的“周末出游”任务逐步增加能力，按“概念图 → 对应演示”排列。概念页为 04、06、08、10、12、14、16，演示页为紧接的奇数页。七个互动演示共用晴天/雨天与 300/200/100 元预算选项，便于在相同条件下观察每个阶段增加了什么。

| 阶段 | 出游任务中的观察重点 |
| --- | --- |
| LLM · 大语言模型 | 根据需求生成行程建议 |
| RAG · 检索增强生成 | 先检索本地景点资料，再参考资料回答 |
| Tool Calling · 工具调用 | 展示工具请求、参数与固定样例返回值 |
| ReAct · 推理与行动交替 | Thought-Action-Observation 循环，依据观察继续或停止 |
| Plan-and-Execute · 规划与执行 | 先拆分计划，再执行并按反馈调整 |
| Plan-and-Execute + Reflexion | 计划v1执行失败后形成反思，修订计划v2并重新执行与验收 |
| Multi-Agent · 多智能体协作 | Supervisor / 层次化 / Swarm；Agent 间通信与共享状态 |

“下一步演示”是浏览器本地确定性教学样例；新增“真实模型演示”由本地服务调用 CCSwitch 当前供应商，通过官方 Codex CLI 产生真实模型输出。两种方式都使用合成天气和场馆，不预订行程。离线模式的计划调整和角色反馈来自预设逻辑，不能作为模型能力的实验结果。真实模式的计划、反思与角色摘要来自各次模型调用，程序负责执行工具、合并状态和验收。七个阶段用于逐步解释能力，并非所有任务都要依次升级；它们也不替代后半程五模式、五情景的 25 份诊断轨迹。中英术语集中见[设计卡的术语速查](design-card.md#ai-术语速查)。

“下一步依赖证据”不构成 Agent 的充分条件。条件与工具映射可穷举时，普通代码或工作流即可；难以预设查询路径、需要解释非结构化信息并选择工具时才评估单 Agent。仅做文本提取的模型节点仍可属于工作流。

三层地图分别说明：推理策略回答“怎样决策”，协作架构回答“怎样分工”，开发框架回答“用什么实现”。先按任务选择方式，再选择实现框架。

| 开发约束 | 候选及理由 | 仍须实现或核对 |
| --- | --- | --- |
| 显式对比固定流、分支、并行与回路 | 本课选 LangGraph：State / Node / Edge 可观察 | 领域工具、路由、reducer、证据校验、预算与日志 |
| 已有消息团队，以对话和委派为主 | AutoGen：AgentChat 团队与 Core 消息运行时 | 工具、终止、上下文、维护与迁移方案 |
| 专业角色按 SOP 交付独立产物 | MetaGPT：Role / Action / Team | 业务 SOP、验收与依赖适配 |
| Java / 前端 / 客户端接入 | 先定 HTTP 和状态 DTO，再选框架 | 按版本核对语言 SDK；不假设各语言功能对等 |

AutoGen 官方资料核对于 2026-09-21：Maintenance Mode，无新功能或增强，由社区维护；官方建议新用户评估 Microsoft Agent Framework。MetaGPT README 标明 Python ≥3.9 且 <3.12，需再核对具体 release 与依赖。LangGraph 不自动提供业务规则、持久恢复或上传接口；检查点、线程标识、恢复和幂等需要配置与实现。

## LangSmith Studio 对比

双击 `start-studio.cmd` 可启动独立的本地 Agent Server（2024端口）。课件顶部的“Studio 对比”会打开图与节点状态面板。两个图 `outing_react`、`outing_supervisor` 复用出游案例，Supervisor 可在汇总前暂停并恢复。安装与用法见 [Studio 演示指南](studio-guide.md)。依赖单独列在 `requirements-studio.txt`，未开启云端追踪。

## 后半程实战：接单前资料初审与专家辅助

唯一业务背景来源为[道通远程专家官方中文页](https://www.auteltech.cn/cloud/3942.jhtml)。官网将其介绍为集合在线专家和客户的远程汽车维修综合服务平台，服务包括远程诊断、编程、防盗、ADAS 和咨询；页面介绍了 VIN 信息、导入报告、发布订单、AI 智能匹配专家、语音/文字/视频/电话沟通，以及实时服务状态和连接状态。这些是产品业务能力；页面未披露 LLM 或多 Agent 内部实现。

课堂任务：门店报告通信故障 U0121，希望远程专家提供咨询。接单前先汇总上传资料中的电压、故障码、网关记录及相关知识；缺失则补充，读数冲突则核对事件时刻和采集时间，保留来源与取舍理由；形成待专家人工复核的资料报告。AI 初审、补充资料流程和角色分工是课程设计，不是对官网内部流程或算法的复述。演示只读取合成记录，不操作真实车辆。

U0121 是与 ABS 控制模块失去通信的故障码，不等于模块损坏；voltage 是供电电压；gateway 是通信网关。远程网络链路中断不能证明车辆故障，网关可达也不证明车辆正常。

原始三字段任务用 `workflow` 足够，无需多 Agent。协作部分新增敏感日志与资料的独立上下文、不同工具权限或独立专业审查责任，才讨论角色拆分；这些是设计约束，生产权限系统需要另行实现。诊断后端、固定数据、工具行为、轨迹结构和五模式×五情景保持不变，只调整任务的业务描述。

## 本地 LangGraph 实际运行

需要 Python 3.10+。主 Demo 使用 requirements.txt 固定的 LangGraph 版本。MetaGPT 的 Python 版本限制属于另一个框架，不与主案例混装。

从仓库根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r agent-training/requirements.txt
.\.venv\Scripts\python.exe agent-training/demo/server.py
```

如果已经在 agent-training 目录内创建虚拟环境，使用该目录的 .venv/Scripts/python.exe 即可。macOS/Linux 对应使用 .venv/bin/python。

打开 http://127.0.0.1:8765，从目录选择“诊断运行台”。不要用普通静态 HTTP 服务替代：它没有 /api/run。端口占用时加 --port 8766，并访问对应地址。

```powershell
.\.venv\Scripts\python.exe agent-training/demo/agents.py --pattern workflow --scenario missing
.\.venv\Scripts\python.exe agent-training/demo/agents.py --pattern integrated --scenario normal
.\.venv\Scripts\python.exe agent-training/demo/agents.py --pattern supervisor --scenario missing
.\.venv\Scripts\python.exe agent-training/demo/agents.py --pattern parallel --scenario conflict
.\.venv\Scripts\python.exe agent-training/demo/agents.py --pattern review --scenario missing
.\.venv\Scripts\python.exe agent-training/demo/agents.py --scenario tool_failure
.\.venv\Scripts\python.exe agent-training/demo/agents.py --max-steps 1
```

最后两种情况应停止或转人工，不生成成功报告。CLI 在 demo/output 写入本次独立的 trace JSON；成功运行还生成待审核报告。轨迹可以导入页面查看。

## 模式与情景

工作流基线加四种协作模式，共五种模式，复用 fixtures.json、同一组只读工具、同一套证据校验和轨迹 schema；五种情景共 25 份预录轨迹。

| 模式 | 观察重点 |
| --- | --- |
| workflow | 确定性基线；缺失或冲突触发预设补读分支，固定验收与报告 |
| supervisor | 顺序委派；证据不足时修订计划、委派补充读取 |
| parallel | LangGraph 实际 fan-out/fan-in；合并两条分支的观察结果 |
| review | 先提交草稿，评审指出问题，再补充资料与修订 |
| integrated | 协调、并行分析、计划修订与最终评审的组合 |

| 情景 | 预期行为 |
| --- | --- |
| normal | 形成完整证据报告，completed，人工审核仍 pending |
| missing | 缺少电压证据，通过只读补充工具恢复后评审 |
| conflict | 11.7 V 与较早的 12.6 V 缓存冲突；依据事件时间索引选择，保留两份来源和理由 |
| tool_failure | 仿真检测和补充工具持续失败，needs_human，不生成成功报告 |
| budget | 最多执行两个图节点，stopped；并行分支也计入预算 |

12.0 V 阈值和 U0121 组合仅是本课程合成知识规则，不是维修标准。报告只能提出待核实假设，不能确认故障原因。

“基线与三种模式”在本地服务下依次实际执行 `workflow / supervisor / parallel / review`；file:// 离线时比较预录轨迹。`integrated` 留给综合案例。比较保持同一情景、来源、预算与验收口径。

工具调用数包含失败调用；修订轮次按计划修订计数。`workflow` 的补充读取是预写条件分支，计划保持 v1、修订轮次为 0，不产生 Revision 或 Dispatch；补读不能自动算作计划修订。证据覆盖为所需三类字段的可用比例，不等于无冲突或诊断准确率。耗时是本机一次运行，不是性能基准。

运行台先看中文故事线、角色图与当前已观察证据，再看修订前后对照；事件 JSON 可展开核对细节，最终报告与状态用于检查出口。`review / missing` 的实际链路是缺电压 E-VOLTAGE → 草稿评审退回 → 计划 Revision → `read_supplemental` 补充电压 → 重写草稿 → 重新审查通过。缺失的不是采集时间；补充无法取得才转人工，`tool_failure` 展示持续工具失败。

## 展示真实性与人工审核

| 界面标识 | 实际发生的事情 |
| --- | --- |
| 本次本地运行 | 执行真实 LangGraph 图与仿真只读工具；角色决策由规则模拟 |
| 录制教学回放 | 播放构建时的历史轨迹，不执行新的任务 |
| 导入历史轨迹 | 展示文件声明的事件，未重新校验业务内容 |
| 报告 / 人工审核 | 展示待审核报告、证据和检查清单；不修改真实审批状态 |

能力演进已支持真实模型调用，入口、供应商限制、三种多 Agent 组织方式和课堂提示词见[大模型演示指南](model-demo-guide.md)。诊断运行台仍采用规则模拟，--mode 仅接受 simulation，模型参数不会静默退回规则模式。诊断业务案例替换角色决策函数为模型仍是后续扩展点，不能把出游案例的真实模式误认为诊断运行台也已接入模型。

verified 只表示报告引用和证据契约通过。completed 只表示课堂报告生成，不表示车辆已修复、诊断已确认或人工已批准。诊断运行台无模型费用统计。出游真实模式显示 token 用量，不估算费用。无生产持久化恢复，无真实车辆连接。

能力演进另支持 DeepSeek 备用：主模型连接、认证、限流或超时失败后，显式切换至 `deepseek-flash` 并保留已有证据。Windows 密钥位于仓库外的用户 DPAPI 加密存储，也可从 `DEEPSEEK_API_KEY` 读取。取消与模型输出校验失败不触发备用调用，全部请求共享次数和时长限制。详见[备用配置说明](model-demo-guide.md#deepseek-备用模型)。

## 服务接口与各端职责

能力演进真实模式接口：`GET /api/outing/config` 返回不含密钥的模型元数据；`POST /api/outing/start` 接受 stage(1–7)、weather、budget、pattern；`GET /api/outing/runs/{id}` 轮询过程；`POST /api/outing/cancel` 接受 `{ "id": "运行ID" }`。单个真实运行最多 12 次模型请求、20 次工具调用、8 分钟；可导出记录，服务重启清空历史。

GET /api/health 返回 schema_version、engine、依赖版本、支持的模式/情景和就绪状态。

POST /api/run 接受：

```json
{"pattern":"integrated","scenario":"conflict","max_steps":30}
```

max_steps 可省略，范围 1–30，计数单位为实际执行的图节点。响应为完整轨迹：

```text
schema_version: 2
run_id / engine / mode / pattern / scenario
status / verified / report / human_review
events: [{id, actor, kind, payload, plan_version}]
metrics: {tool_calls, revision_rounds, elapsed_ms, evidence_coverage}
shared_state: observations / plan / draft / review / issues / ...
```

接口同步完成后返回，不是实时 token 流。未知模式、额外参数、错误类型等返回 400；跨来源请求拒绝。服务只绑定 127.0.0.1，只提供演示页和明确列出的 API，不暴露目录文件。

系统设计中，客户端收集现场资料，前端展示轨迹与审核材料，Java 后端承担业务鉴权、工单和审批，Agent 服务负责推理与协作。课堂 /api/run 是只传情景选择的本地测试接口；实际接入工单存储、鉴权或审批需要另行实现。

## 课堂练习与参考答案

任务：“电压资料无法从工具取得，等待门店通过客户端上传，再恢复任务。”4 分 10 秒内提交暂停/恢复图、上传消息和验收条件。**这是尚未实现的设计练习**：当前 Demo 没有客户端上传接口、持久暂停或恢复功能，`read_supplemental` 读取合成记录不等于等待用户上传。参考答案也在讲师备注和设计卡中。

参考职责：客户端展示补充要求并上传；Java 业务服务验证登录身份、工单权限和文件；编排器保存、暂停和恢复；证据角色核验内容及采集时间；审查者验收修订后的建议。无需新增“上传 Agent”。

参考流程：发现缺失 → 持久保存并设为 `waiting_client_upload` → 结束本次 HTTP 请求 → 客户端上传 → 业务校验 → 从待补充节点恢复 → 重新审查。保存 `case_id / run_id / plan_version / observations / draft / review / missing`，以及剩余预算、恢复节点、`upload_request_id`、到期时间和已处理消息。保留有效证据，不清空状态重跑。

上传消息示例（拟议契约，当前 `/api/run` 不接受此消息）：

```json
{
  "type": "client_evidence_uploaded",
  "case_id": "SYNTH-REMOTE-001",
  "run_id": "run-demo",
  "upload_request_id": "upload-1",
  "expected_plan_version": 2,
  "message_id": "msg-1",
  "idempotency_key": "upload-1-v1",
  "evidence_refs": ["upload-file-1"]
}
```

身份和角色来自认证会话，不能信任消息自报身份。文件引用应指向经过鉴权的上传记录，证据核验后才进入当前状态。

| 验收路径 | 参考处理 |
| --- | --- |
| 正常上传 / 重启后上传 | 从持久记录恢复待补充节点，保留预算与已有证据，再审查 |
| 重复消息 / 并发回调 | 数据库唯一幂等键加原子状态转换，只恢复一次，返回已处理结果 |
| 过期上传 | 旧请求 ID、旧版本、已结束任务的上传留审计，不覆盖当前证据或唤醒旧任务 |
| 越权 / 格式或证据无效 | 拒绝并说明原因；保留待补充状态，按次数或期限限制重传 |
| 超时 / 取消 / 始终无法补齐 | 超时或无法补齐转人工；取消后不恢复；保留已收集材料 |

普通持久状态机即可实现。使用 LangGraph 时另配 checkpointer、thread_id、interrupt/resume，验证恢复重放与外部副作用幂等；保存轨迹 JSON 不等于实现恢复。练习参考解不计作已实现功能。

## 构建与检查

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s agent-training/demo -v
.\.venv\Scripts\python.exe agent-training/build.py --package
```

content.py 是内容与时间安排源，concepts.py 保存七个概念图和讲解；template.html 保留视觉模板；player.js 管理诊断与翻页交互；outing-live.js 管理真实模型演示窗口，demo/model_gateway.py 负责 CCSwitch 与官方客户端，demo/outing_live.py 负责七阶段执行和验收；lab.html 是运行台；build.py 内联全部内容，生成 index.html、outline.md、speaker-notes.md、25 份 sample-output 轨迹和样本报告。--package 同步更新仓库根目录 ZIP，不包含虚拟环境、缓存或运行输出。

维护课程时修改内容源后重新构建，不直接编辑生成的演示稿或讲稿。核心检查包括总计 48 页、第 04 页进入能力演进、八章秒数 150/150/1070/480/980/420/750/1400、合计 90 分钟，以及七个出游演示在晴天/雨天和 300/200/100 元预算下的交互。诊断运行台仍检查五模式×五情景、基线无计划修订、独立证据校验、图节点预算、真实并行、HTTP 契约，以及浏览器中的翻页/判断题/回放/本地运行/导入导出。
