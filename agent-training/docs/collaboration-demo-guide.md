# 五种协作模式 · VS Code 真实运行指南

第 14 至 21 页配合本项目完整 Python 源码讲解。五种模式由 LangGraph 实际编排，角色、主管与动态路由调用真实模型；DeepSeek 主用，现有 OpenAI/Codex 连接备用。场馆资料是固定课堂数据，费用由 Python 工具计算，模型输出经过程序验收。

## 课前准备

需要 Python 3.10+、VS Code、Python 与 Python Debugger 扩展。在项目根目录执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe demo/run_collaboration.py --check-model
```

本机已有虚拟环境时无需重建。VS Code 选择 `.venv/Scripts/python.exe`。`--check-model` 只检查配置可读取，不发起请求；备课时还应真实运行一次。

DeepSeek 默认调用官方接口的 `deepseek-flash`，读取 `DEEPSEEK_API_KEY` 或本机已有的用户 DPAPI 凭据。当前电脑可直接复用已保存配置。新电脑需自行设置环境变量或配置本机凭据；不要把密钥写进源码、调试配置或培训包。

备用复用 CCSwitch 当前 Codex 配置与官方 `codex exec` 客户端。安装并登录官方 Codex CLI，在 CCSwitch 中选好连接即可；DeepSeek 正常时不需要备用客户端可用。连接、认证、额度、限流、超时异常触发一次明确的备用切换，并保留当前状态。模型输出不合格由原模型有限修正，不触发供应商切换；取消也不切换。备用不可用则明确停止。

## 源码阅读顺序

```text
demo/run_collaboration.py              统一 CLI 入口
demo/collaboration_live/
  state.py                            共享状态与初始输入
  tools.py                            资料读取、费用计算、独立验收
  agents.py                           各角色提示、行动白名单、工具执行
  sequential.py                       固定 add_edge 顺序链
  supervisor.py                       主管模型调度，成员返回主管
  hierarchical.py                     CEO 父图与两个编译后的团队子图
  swarm.py                            当前角色从 HANDOFFS 中选择交接
  network.py                          对等节点内部选择下一跳
  runtime.py                          模型请求、图流、上限、轨迹与报告
demo/model_backup.py                  DeepSeek 优先与备用切换
demo/model_gateway.py                 现有 OpenAI/Codex 连接
```

先看 `state.py` 和 `tools.py`，说明两大一小、雨天、300 元预算；再依次打开五个模式文件，比较“谁决定下一步”。最后进入 `agents.py` 展示模型如何提出行动，以及宿主如何执行工具。课堂无需逐行讲模型网关。

五种模式共用角色和资料，主要区别是图结构与控制权。Swarm 与 Network 的机制可以重叠；本例都是单个活跃角色串行执行，全连接只是 Network 的一个示例。

## 现场运行与断点

按 F5 选择“真实协作 · Sequential Chain / Supervisor / Hierarchical / Swarm / Network”，然后选 `normal` 或 `missing`。每个节点返回后在集成终端按 Enter 继续。也可以从项目根目录执行：

```powershell
.\.venv\Scripts\python.exe demo/run_collaboration.py --pattern supervisor --scenario missing --step
.\.venv\Scripts\python.exe demo/run_collaboration.py --pattern all --scenario normal
.\.venv\Scripts\python.exe demo/run_collaboration.py --pattern all --scenario missing
```

`start-collaboration.cmd --pattern supervisor --scenario missing --step` 使用本地虚拟环境运行同一入口。五个模式文件也可从 `demo` 目录用 `python -m collaboration_live.supervisor` 等命令执行。

| 源码位置 | 断点和观察内容 |
| --- | --- |
| sequential.py 的 build_graph | 固定边；角色自己不能改变外层顺序 |
| supervisor.py 的 supervisor | 状态 → 主管模型选择 → Command；成员返回主管 |
| hierarchical.py 的 ceo / lead | 父图调团队，子图调成员；ESCALATE 返回上层 |
| swarm.py 的 agent_node | 当前角色决定白名单内 handoff，无主管 |
| network.py 的 peer_node | 当前节点选择其他对等节点，没有中央路由器 |
| agents.py 的 work | 请求工具 → 真实执行 → 观察 → 模型返回 |
| runtime.py 的 ask | 实际供应商、行动校验和有限修正 |

终端依次打印模型请求、响应摘要、工具结果、分派/交接/路由、图节点状态及最终结果。`--show-state` 打印完整状态；Hierarchical 的 JSON 中还记录实际子图 namespace。摘要用于说明行动，不展示模型内部思维过程。报告的场馆、费用与无解结论来自已验收的结构化字段和工具证据，模型原始正文保存在轨迹中供对照。

每次运行生成独立目录 `demo/output/collaboration-live/<时间-编号>/`，包含每个模式的 `*-trace.json` 与 `*-report.md`。从本次目录检查真实调用次数、token、模型切换、缺项、建议和验收结果。轨迹 JSON 是执行记录，不是持久暂停恢复功能。

## 课堂安排

第 14 页交代共同任务。第 17 至 21 页用源码节选定位，再切到 VS Code 看完整图定义、设断点并运行。课前跑完整 normal 对比；课上重点跑 missing 的反馈路径，避免全部网络等待占用讲解时间。固定课堂数据正常情况下可得到城市博物馆 240 元（门票120、交通30、餐费90）。

`missing` 首次资料读取不含餐费与引用，再次读取才补齐。固定顺序链没有返回边，因此应保留缺项、等待补充；其他模式可以通过模型选择的反馈路径补齐。运行时核对实际路径：真实模型可能跳过角色、请求非法路由或反复循环，程序会反馈修正或停止，留下记录供分析。

每次最多 32 个模型请求（包括失败与修正），图递归限制40，每种模式最多360秒，每个请求最多45秒；可以用 CLI 参数调整。五种模式全部运行的耗时取决于网络与模型。Ctrl+C 取消本次运行。异常或达到上限时返回非零退出码，并保留失败记录。

第 15 页对照五种控制方式，第 17 至 21 页逐项运行。课后可给顺序链增加条件返回边，验证补齐餐费后是否重新核算和审查；当前示例未包含返回边。

## AG2 Playground 是否一起讲

第 16 页介绍 AG2 Playground，可用约 3 分钟运行一个示例，时间紧时略过操作。完整代码讲解在 VS Code 中进行。

| 网站演示 | 可对照的机制 |
| --- | --- |
| [Sequential Chat](https://playground.ag2.ai/demos/sequential-chat/) | 顺序聊天队列，前一轮摘要传给后一轮 |
| [Nested Chat](https://playground.ag2.ai/demos/nested-chat/) | 外层角色委托内部研究、起草、编辑流程 |
| [Auto Pattern](https://playground.ag2.ai/demos/auto-pattern/) | 管理者用模型选择下一发言者，可对照集中调度 |
| [LLM Condition](https://playground.ag2.ai/demos/llm-condition/) | 条件判定与交接，可对照动态 handoff |

选一个与刚运行的代码对应的演示，比较谁选择下一角色、怎样传递上下文。Auto Pattern 有管理者，不能直接当作无主管 Swarm；Nested Chat 展示嵌套委托，不能据此说网站完整实现本课程的层次化图。网站示例使用它自己的配置，不会自动继承本机 DeepSeek / OpenAI 连接。AG2 的 `ag2.network` 产品名称也不等于本课 Network 拓扑分类。

## 验证与分享

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_collaboration_live.py
```

回归测试只替换外部模型响应，真实执行 LangGraph 图与资料/费用工具，不产生模型费用。`collaboration-demo.zip` 包含完整真实示例、依赖声明和 VS Code 配置，解压后需要安装依赖并配置自己的模型。它不包含密钥、虚拟环境、私人运行输出或旧规则回放。
