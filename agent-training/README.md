# 高级推理框架与多 Agent 协作 · 培训包

首次从 Git 克隆后，安装 requirements.txt 并运行 `python build.py` 生成课件。打开 [index.html](index.html) 讲课；用 VS Code 打开当前目录，按 F5 运行真实协作代码。文件位置见 [目录说明](docs/directory-guide.md)，提交范围见 [Git 文件管理](docs/git-management.md)。

| 目录 | 内容 |
| --- | --- |
| `demo/` | 可运行演示与模型连接；主线在 `collaboration_live/`，旧规则源码在 `reference/` |
| `course/` | 课程内容、图形、分页与讲稿生成源码 |
| `web/` | HTML 模板、样式、浏览器脚本 |
| `docs/` | 大纲、讲师讲稿、演示指南、来源与设计说明 |
| `tests/` | Python、JavaScript 与浏览器回归检查 |
| `tools/` | 打包及交付验证工具 |
| `assets/` | 导入资料、参考图与 PDF |
| `config/` | 可提交的配置模板 |
| `dist/` | 可分发演示包 |
| `archive/` | 可提交的历史输入快照；本机工作记录与旧生成示例另行忽略 |
| `test-results/` | 本机检查日志与截图 |

课程共 39 页、90 分 07 秒，面向 Java 后端、前端和客户端开发者。第 2 页是大纲；第 3 至 12 页用出游案例比较七种架构；第 13 至 21 页介绍五种协作模式，并在 VS Code 中运行；第 22 至 24 页介绍 MAF、LangGraph、MetaGPT；第 25 至 32 页实现 Review Agent，运行评审、修复和复审；第 33 至 39 页讨论 A2A / MCP、安全和工程问题。诊断案例作为课后参考。

## 第 25 至 32 页：MetaGPT 开发团队与 Review Agent

**新产品实战入口**：使用 `demo/run_dev_team.py --requirements <需求.json>`，由需求驱动 PRD、设计与多文件实现，在 Docker 中运行，执行外部 HTTP 与浏览器业务验收，失败修复后等待当前版本批准。两个不同领域输入、恢复、正式启动及独立 ZIP 交付见 [新产品开发指南](docs/product-development-guide.md)。下述固定看板继续作为 Review 子练习，历史测试记录不代表新产品验收。

用十五分钟运行一次任务看板的评审与修复。首轮 PR 由讲师提供，包含可复现的缺陷；Reviewer 调用模型评审，开发角色根据意见和实际测试失败修复代码，再重新评审、测试并等待人工批准。看板包含前端、HTTP 接口、SQLite 和固定测试。讲解时对照角色产物、输入契约和工具结果。

VS Code 选择“开发团队 · Review 与修复”按 F5。使用独立 `.venv-metagpt` Python 3.11 和 MetaGPT 0.8.2 环境；模型沿用现有网关。重试限制、版本失效与人工审批由代码保证。完整准备、断点、运行、审批和看板命令见 [实战演示手卡](docs/dev-team-demo-guide.md)，设计见 [开发设计](docs/dev-team-design.md)。

已用真实模型跑通 Review → 修复 → 复审，原产物保留待人工批准；独立进程审批与浏览器看板也已在副本上验证。实际模型、产物和验证范围见 [实战验证记录](docs/dev-team-verification-2026-10-08.md)。

框架介绍共 18 分钟，包含官方指南与示例的讲解时间。各章详细时间见 [大纲](docs/outline.md)，总计 90 分 07 秒。

## 第 22 至 24 页：三种框架介绍

三页分别介绍 Microsoft Agent Framework、LangGraph、MetaGPT 的能力、适用场景和官方示例。图片保存在本地，可离线查看原图；来源见 [来源说明](assets/frameworks/SOURCES.md)。集成指南和使用示例链接到官方资料，本地 LangGraph 五模式代码也可直接运行。备课见 [框架演示手卡](docs/framework-demo-guide.md)。第 25 页开始开发团队实战。

历史内容见[迁移前课件](archive/2026-10-07-before-collaboration-import/index.html)和[移出页数据](archive/2026-10-07-before-collaboration-import/removed-slides.json)。导入资料的本地副本在 [assets/imported/multi-agent-source.html](assets/imported/multi-agent-source.html#sec02)，构建可直接读取。分页、样式和交互分别维护在 course/collaboration_import.py、web/collaboration-import.css、web/collaboration-import.js。跨页代码支持复制完整原示例，工程问题可用鼠标或键盘展开；原文中的 FAQ 留在资料副本中。

第 13 页用五组矢量图比较协作模式，图形维护在 course/collaboration_visuals.py，文案修订在 course/collaboration_corrections.py。图中 Swarm 按需交接，Network 的全连接只是一个例子，顺序链的外层固定顺序与节点内部重试分别说明。模式可以组合，调用开销和容错需结合实际配置判断。页脚参考链接维护在 course/collaboration_references.py。

入口：[演示稿](index.html) · [大纲](docs/outline.md) · [讲师讲稿](docs/speaker-notes.md) · [选型与设计卡](docs/design-card.md) · [来源](docs/sources.md)。

协议内容位于第 33 至 34 页：第 33 页为 A2A / MCP 总览，第 34 页并列展示 A2A 核心概念、MCP 三种能力及总结。

## 第 14 至 21 页：五种协作模式 VS Code 真实演示

第 14 页定义共同任务，第 15 页对照五种模式，第 16 页介绍 AG2 Playground，第 17 至 21 页依次讲顺序链、主管、层次化、Swarm 与 Network 的代码示例。培训时打开 VS Code 展示完整源码并运行，终端逐节点显示真实模型请求、工具结果、控制权转移、状态和验收结果。

五种模式由 LangGraph 调度，模型参与角色判断与动态路由：固定边、主管动态调度、编译后的团队子图、角色 handoff、对等节点路由。投影页由 course/collaboration_vscode.py 生成，源码节选来自 demo/collaboration_live；场馆资料是固定课堂数据。原规则回放保留为历史参考，不作为本章演示入口。

DeepSeek 为主配置，连接异常时明确切换现有 OpenAI/Codex 备用，并保留证据。normal / missing 分别展示完整资料和首次漏餐费。每次执行保存 JSON 轨迹和 Markdown 报告，可据此查看模型实际选择的路径。

将 [独立演示包](dist/collaboration-demo.zip) 解压后安装 requirements.txt、配置模型，再用 VS Code 打开整个文件夹，选“真实协作”配置按 F5。Windows 启动脚本使用本地虚拟环境。详细准备、断点和课堂节奏见 [演示指南](docs/collaboration-demo-guide.md)。当前目录可运行：

```powershell
.\.venv\Scripts\python.exe demo/run_collaboration.py --pattern supervisor --scenario missing --step
```

输出在 demo/output/collaboration-live。AG2 Playground 可选用 3 至 5 分钟对照一种机制，无需重复五种模式。维护后执行 `python tools/package_collaboration.py` 更新独立 ZIP；`python tools/verify_collaboration_package.py` 验证解压后的真实图与工具（测试替换外部模型响应，不收费）。

## 离线演示

直接用 Chrome 或 Edge 打开 index.html，无需前端依赖或 CDN。支持翻页、目录、讲师备注和七种架构互动示意；五种协作模式切到 VS Code 真实执行。HTML 内没有 API Key。

| 操作 | 快捷键 |
| --- | --- |
| 上一页 / 下一页 | ← / →、PageUp / PageDown、空格 |
| 第一页 / 最后一页 | Home / End |
| 目录 / 讲师备注 | O / N |
| 全屏 / 帮助 | F / ? |
| 关闭弹窗 | Esc |
| 打印讲义 | Ctrl+P，横向，开启背景图形 |

页面保持 16:9 投影布局；窄屏整体缩放，推荐桌面演示。讲师备注弹窗与投影共屏，私有备课请在另一设备打开 docs/speaker-notes.md。

讲师备注已为 39 页提供可直接照讲的现场讲稿，并附可展开的概念解释、生活类比、业务实例、常见误区和互动提示。现场时长包含演示与停顿，扩展内容按学员基础选讲；全部讲解时请额外安排时间。

按 **N** 或点击“讲师备注”，展开“术语发音与释义”，可查看本页英文术语的音标、中文含义和解释。点击“听发音”按正常语速朗读，点击“慢速”放慢；也可勾选“全课词库”搜索其他术语。切换术语会停止上一段，关闭备注或切换页面也会停止。

发音使用浏览器与系统的英语语音，不需要配置模型或 API Key；有本机英语语音时可离线使用，部分浏览器语音需要联网。不支持朗读或未安装英语语音时会显示提示，音标与讲稿仍可阅读。Markdown 讲稿保留相同的讲解与术语，听发音请打开网页。

讲稿维护在 course/speaker_notes.py，统一术语在 course/glossary.py；修改后运行 `python build.py` 同步生成网页与 docs/speaker-notes.md。音标以常见美式读法为主，品牌和缩写采用课堂读法。

## 七种架构的出游演示

第 3 至 5 页介绍七种架构，第 6 至 12 页按①至⑦演示。①包含模型、检索和工具，③加入反馈修订，⑤按需求选择技能，⑥等待共享资料齐备，⑦沿节点和条件边执行。这些方式可以组合。点击“开始演示 / 下一步”查看节点和信息流，“上一步”回看，“重播”恢复起点；底部列出优势、局限和适用场景。“更多”中可改天气、预算、需求，也可查看记录或打开真实模型入口。

架构文案、图形、演示图分别维护在 course/architecture_reference.py、course/architecture_diagrams.py、course/architecture_visuals.py，讲稿在 course/outing_content.py，步骤映射在 web/outing.js。图形内嵌到 HTML，离线可用。三页 PDF 见 [架构信息图](assets/figures/architecture-infographics.pdf)。

出游演示页与真实模型窗口均展示优势、局限和本例观察点；真实模型窗口切换 Supervisor、层次化或 Swarm 时同步更新。说明用于评估机制取舍，不把规则仿真的耗时当成真实模型性能结论。

| 页面与架构 | 出游任务中的观察重点 |
| --- | --- |
| 06 · ① 单 Agent | 先想到公园；查到下雨后，同一个 Agent 用规则与事实修正建议 |
| 07 · ② ReAct | 自然馆 310 元超预算；根据这次观察，改查博物馆 210 元 |
| 08 · ③ Plan & Execute | 执行中预算 300 → 200 元；复用资料，修订剩余计划并重新验收 |
| 09 · ④ 多 Agent | 天气角色建议自然馆，费用角色建议公园；主管核对两份局部判断 |
| 10 · ⑤ Router + Skill | 用户从安排出游改成只算费用；切换费用技能，跳过天气查询 |
| 11 · ⑥ Blackboard | 费用角色先等待；场馆名单发布后才触发，资料齐备再汇总 |
| 12 · ⑦ Graph / Workflow | 默认雨天 200 元，室内候选均超预算；走预设无解边到 END |

“下一步演示”是浏览器本地确定性教学样例。第 06 至 12 页均有真实模型入口，沿用本地服务的模型连接与备用配置。⑤保持关键词 Router，按需加载技能和 Reference，模型提出流程内的工具请求并交付结果；⑥按黑板就绪条件触发独立角色调用模型，实际发布证据与版本；⑦保持显式节点与条件边，由程序查工具、筛选和核算，模型在结果节点生成回答。两种方式都使用合成天气和场馆，不预订行程。离线决策来自预设逻辑，不能作为模型能力实验结果；真实模式的措辞与探索顺序可能变化，仍要遵守同样的证据和验收条件。课后参考保留五模式、五情景的 25 份诊断轨迹，诊断共享状态仍由 LangGraph 显式调度。中英术语见[设计卡的术语速查](docs/design-card.md#ai-术语速查)。

七页各设不同关键事件，顶部说明当前演示重点，步骤描述谁做什么、发现了什么、为什么继续。第 12 页初始为雨天 200 元，其余页为雨天 300 元；手动修改天气或预算仍会同步各页。第 8 页从 300 降到 200 元，低于或等于 200 元时改为再次确认上限；第 10 页“安排出游”默认演示途中改口，“只核算费用”和“帮我看看”可单独观察费用和澄清分支。回退、重播同步恢复页面上的预算与需求说明。

途中改预算、改需求和局部意见由离线教学脚本设置。真实模型入口使用“更多”中的初始参数，③仍使用明确标注的漏餐费草稿反馈示例，⑤处理当前初始需求，不自动注入这些离线事件。七页图中的黄色「!」在鼠标悬浮时显示局限提示，相关节点和箭头随演示高亮；并发冲突与断点恢复属于尚未演示的边界。

“下一步依赖证据”不构成 Agent 的充分条件。条件与工具映射可穷举时，普通代码或工作流即可；难以预设查询路径、需要解释非结构化信息并选择工具时才评估单 Agent。仅做文本提取的模型节点仍可属于工作流。

三层地图分别说明：推理策略回答“怎样决策”，协作架构回答“怎样分工”，开发框架回答“用什么实现”。先按任务选择方式，再选择实现框架。

| 开发约束 | 候选及理由 | 仍须实现或核对 |
| --- | --- | --- |
| 显式对比固定流、分支、并行与回路 | 本课选 LangGraph：State / Node / Edge 可观察 | 领域工具、路由、reducer、证据校验、预算与日志 |
| Python / .NET 团队需要 Agent、工具与协作工作流 | MAF：Agent、工具与 Workflow | SDK、模型兼容性、执行与恢复配置 |
| 专业角色按 SOP 交付独立产物 | MetaGPT：Role / Action / Team | 业务 SOP、验收与依赖适配 |
| Java / 前端 / 客户端接入 | 先定 HTTP 和状态 DTO，再选框架 | 按版本核对语言 SDK；不假设各语言功能对等 |

AutoGen 官方资料核对于 2026-09-21：Maintenance Mode，无新功能或增强，由社区维护；官方建议新用户评估 Microsoft Agent Framework。MetaGPT README 标明 Python ≥3.9 且 <3.12，需再核对具体 release 与依赖。LangGraph 不自动提供业务规则、持久恢复或上传接口；检查点、线程标识、恢复和幂等需要配置与实现。

## 课后参考：接单前资料初审与专家辅助

以下诊断案例已随原第 41 至 48 页移出主课件；源代码、预录轨迹和设计说明保留为课后参考。运行台界面见[迁移前课件](archive/2026-10-07-before-collaboration-import/index.html)。

唯一业务背景来源为[道通远程专家官方中文页](https://www.auteltech.cn/cloud/3942.jhtml)。官网将其介绍为集合在线专家和客户的远程汽车维修综合服务平台，服务包括远程诊断、编程、防盗、ADAS 和咨询；页面介绍了 VIN 信息、导入报告、发布订单、AI 智能匹配专家、语音/文字/视频/电话沟通，以及实时服务状态和连接状态。这些是产品业务能力；页面未披露 LLM 或多 Agent 内部实现。

课堂任务：门店报告通信故障 U0121，希望远程专家提供咨询。接单前先汇总上传资料中的电压、故障码、网关记录及相关知识；缺失则补充，读数冲突则核对事件时刻和采集时间，保留来源与取舍理由；形成供专家复核的资料报告。AI 初审、补充资料流程和角色分工由课程设计，官网未说明内部实现。演示只读取合成记录，不操作真实车辆。

U0121 是与 ABS 控制模块失去通信的故障码，不等于模块损坏；voltage 是供电电压；gateway 是通信网关。远程网络链路中断不能证明车辆故障，网关可达也不证明车辆正常。

原始三字段任务用 `workflow` 足够，无需多 Agent。协作部分新增敏感日志与资料的独立上下文、不同工具权限或独立专业审查责任，才讨论角色拆分；这些是设计约束，生产权限系统需要另行实现。课后参考保留诊断后端、固定数据、工具和轨迹，包含五种模式、五种情景。

## 本地 LangGraph 实际运行

需要 Python 3.10+。主 Demo 使用 requirements.txt 固定的 LangGraph 版本。MetaGPT 的 Python 版本限制属于另一个框架，不与主案例混装。

从仓库根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r agent-training/requirements.txt
.\.venv\Scripts\python.exe agent-training/demo/server.py
```

如果已经在 agent-training 目录内创建虚拟环境，使用该目录的 .venv/Scripts/python.exe 即可。macOS/Linux 对应使用 .venv/bin/python。

打开 http://127.0.0.1:8765 可使用主课件的真实模型入口。诊断案例通过以下 CLI 命令运行；主课件已移除诊断运行台。不要用普通静态 HTTP 服务替代：它没有 /api/run。端口占用时加 --port 8766，并访问对应地址。

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

能力演进已支持真实模型调用，入口、供应商限制、三种多 Agent 组织方式和课堂提示词见[大模型演示指南](docs/model-demo-guide.md)。诊断示例采用规则模拟，--mode 仅接受 simulation。若要使用模型决策，需要替换角色决策函数；出游演示的真实入口不适用于诊断示例。

verified 只表示报告引用和证据契约通过。completed 只表示课堂报告生成，不表示车辆已修复、诊断已确认或人工已批准。诊断运行台无模型费用统计。出游真实模式显示 token 用量，不估算费用。无生产持久化恢复，无真实车辆连接。

培训真实模型统一优先使用 DeepSeek `deepseek-flash`；连接、认证、限流或超时失败后，显式切换现有 OpenAI/Codex 备用并保留证据。Windows 密钥位于仓库外的用户 DPAPI 加密存储，也可从 `DEEPSEEK_API_KEY` 读取。取消与模型输出校验失败不触发供应商切换。详见[模型配置说明](docs/model-demo-guide.md#deepseek-主配置与-openai-备用)。

## 服务接口与各端职责

能力演进真实模式接口：`GET /api/outing/config` 返回不含密钥的模型元数据；`POST /api/outing/start` 接受 stage(1 至 10)、weather、budget、pattern，以及 Router 使用的 intent；`GET /api/outing/runs/{id}` 轮询过程；`POST /api/outing/cancel` 接受 `{ "id": "运行ID" }`。单个真实运行最多 12 次模型请求、20 次工具调用、8 分钟；可导出记录，服务重启清空历史。

GET /api/health 返回 schema_version、engine、依赖版本、支持的模式/情景和就绪状态。

POST /api/run 接受：

```json
{"pattern":"integrated","scenario":"conflict","max_steps":30}
```

max_steps 可省略，范围 1 至 30，计数单位为实际执行的图节点。响应为完整轨迹：

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

课后练习：“电压资料无法从工具取得，等待门店通过客户端上传，再恢复任务。”提交暂停/恢复图、上传消息和验收条件。当前 Demo 没有客户端上传接口、持久暂停或恢复功能，`read_supplemental` 读取合成记录不等于等待用户上传。参考答案见下文与设计卡。

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

在 `agent-training` 目录执行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_*.py
.\.venv\Scripts\python.exe tools/check_git_files.py
node --test tests/architecture_traces.test.cjs
node --test tests/architecture_visuals.test.cjs
node --test tests/walkthrough_ui.test.cjs
node --test tests/outing_live_ui.test.cjs
node --test tests/collaboration_import_ui.test.cjs
node --test tests/speaker_notes_ui.test.cjs
.\.venv\Scripts\python.exe build.py
```

浏览器回归需要可用的 Playwright 与 Chrome；若 Playwright 安装在其他目录，可用 `PLAYWRIGHT_MODULE` 指定模块路径。它使用受控接口响应，不调用收费模型。七种架构的机制、优缺点、验证范围及真实窗口隔离说明见 [演示检查记录](docs/demo-audit.md)。需要打包时给构建命令追加 `--package`。

course/content.py 是课程结构与时间安排源，course/outing_content.py 定义七种架构的演示文案和讲稿，web/outing.js 执行离线轨迹；course/concepts.py 保留旧能力机制参考。web/template.html 保留视觉模板，web/player.js 管理诊断与翻页。web/outing-live.js 将前四种架构映射到已有真实模型 API 阶段，demo/model_gateway.py 负责 CCSwitch 与官方客户端，demo/outing_live.py 保留原七种能力调用协议。web/lab.html 是运行台；build.py 内联内容，生成 index.html、docs/outline.md、docs/speaker-notes.md；仅含诊断运行台时生成 sample-output 轨迹和样本报告。--package 输出到 dist/，不包含虚拟环境、缓存、工作记录或私人运行输出。

维护课程时修改内容源后重新构建，不直接编辑生成的演示稿或讲稿。架构概览与演示优缺点定义在 course/architectures.py。核心检查覆盖课程大纲、七种架构、五种协作模式、框架介绍和八页 MetaGPT 实战，页码与时长以生成的大纲为准。核对总览页与源文档五张说明卡一致，验证目录及桌面 / 手机布局。实战额外检查证据原文、内容版本、固定验收、真实 MetaGPT 消息触发、修复复审和人工门禁。诊断运行台仍检查五模式×五情景、基线无计划修订、独立证据校验、图节点预算、真实并行、HTTP 契约，以及浏览器中的翻页、回放、本地运行和导入导出。
