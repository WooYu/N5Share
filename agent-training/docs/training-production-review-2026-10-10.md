# 培训案例与新产品开发能力审查

审查日期：2026-10-10。代码基线：`5c08615`。重点范围：主课件第 25–32 页 MetaGPT 开发团队，以及 `multi-agent-training` 讲义第 7 章开发团队和第 12 章综合练习。

后续实现与验收见 [新产品实战整改记录](product-remediation-verification-2026-10-10.md)。本文保留原基线的发现和反例，不将旧回归结果替换为整改结果。

## 结论

**按“实际生产中可以开发新产品”的要求，当前最后实战不通过。**

主课件已经具备真实的 MetaGPT 消息流、模型修复入口、固定测试、重新评审及版本绑定的人工决定，可以作为代码评审与修复教学案例。它的业务实现来自预置任务看板，仅允许修改一个 Python 文件。新讲义中的开发团队则主要完成方案讨论、固定代码示例与语法检查。两套实现都缺少从新的业务需求生成并交付产品的端到端验收。

多数教学边界已在原文档写明。本次采用用户新提出的生产标准评估，不能将原来的教学范围直接当成新产品开发能力。除了范围差距，还复现了测试误判、启动入口绕过审批和失败结果被记为完成等问题。

## 案例覆盖与判定

| 案例 | 实际具备的能力 | 本次检查 | 对新产品开发的意义 |
| --- | --- | --- | --- |
| 主课件五种协作模式 | 用实际 LangGraph 调度，读取固定出游资料，程序核算费用及验证建议 | 9 项受控模型回归通过 | 可以教授控制流、工具与独立验收；未接入真实业务数据 |
| 主课件 MetaGPT 开发团队 | 导入看板 PR → 评审 → 固定测试 → 单文件修复 → 复审 → 人工决定 | 6 项合同测试、3 项实际框架集成通过；另有下述反例 | 是可运行的 Review 实战；尚未实现新产品生成 |
| 新讲义 Sequential / Supervisor / Hierarchical / Swarm / Network | 本地资料、报告生成、工具调用或方案讨论 | 六个 LangGraph 入口均可构图；Network 提前结束反例成立 | 构图证明接口可用，不能证明任务完成质量 |
| 新讲义开发团队 | 六角色顺序讨论；人工放行 Tester；固定示例代码、语法检查 | Node 离线产物检查和真实 LangGraph 受控角色反例 | 不具备可运行应用生成与业务测试能力 |
| 新讲义 AutoGen | Researcher / Critic / Writer 轮询讨论 | 本次 `--check` 构造成功，无 API 请求 | 尚未在本次审查验证真实对话质量或应用交付 |
| 新讲义 MCP | stdio 协议下的本地资料工具、资源与提示模板 | 实际客户端完成初始化、列工具、调用工具、读取资源及提示模板 | 本地协议教学可运行；工具只查询教学资料 |
| 新讲义最终综合练习 | 提交报告、执行轨迹、选型理由及失败演练记录 | 对照第 12 章交付与验收标准 | 没有产品源码、运行环境、接口或发布验收要求 |

本次未重新发起付费模型请求。框架集成及反例中的模型响应由受控替身提供，实际编排、测试子进程、HTTP 服务和门禁代码均执行；这验证确定性行为，不能评估真实模型的生成质量。主案例此前的七次真实请求属于 2026-10-08 的历史证据。

## 优先问题

### P1-1：最后实战缺少新需求到新产品的实现路径

位置：[actions.py](../demo/dev_team/actions.py) 的 `PrepareChange`（第 54 行）与 `RepairCode`（第 119 行）；[tools.py](../demo/dev_team/tools.py) 第 15 行；[run_dev_team.py](../demo/run_dev_team.py) 第 29 行起。

- PM 与 Architect 生成文档后，开发行动没有消费设计内容，而是直接复制 `fixtures/board.py` 和 `fixtures/index.html`。
- 首轮候选依据 `clean / buggy` 决定是否移除状态校验。命令行没有业务需求文件或新项目输入。
- 修复仅允许返回完整 `board.py`，前端、HTTP 服务、数据库结构与验收保持固定。
- PRD 文件被保存，但 Architect 得到的是固定契约与文件名，后续 Developer 不根据设计产物生成应用。

影响：更换成库存、预约或审批业务，现有流程仍只会导入任务看板；模型真正参与的是评审与单文件修复。现有成功记录不能证明从零交付产品。

整改验收：以可替换的需求文件驱动产物契约、实现任务和验收。至少使用两个未写死的业务需求验证：交付的领域模型、接口、前端与业务测试应随需求变化，且能从空业务代码目录构建运行。

### P1-2：固定测试结果可伪造，候选代码在宿主权限下执行

位置：[tools.py](../demo/dev_team/tools.py) 第 60–75 行；[test_board.py](../demo/dev_team/fixtures/test_board.py) 第 7–9 行。

测试子进程直接导入候选代码。`passed` 只检查退出码为 0，且输出包含 `Ran 5 tests`。`python -I` 不提供操作系统级文件、网络或环境变量隔离。

本次反例：在隔离的审查副本中，让候选模块在导入时打印匹配文本并退出。实际执行 0 项测试，`run_tests` 仍返回 `passed=true`。给门禁一个受控的 pass 评审和当前版本批准，门禁返回 `completed`；此评审是探针输入，不是实测模型结论。

同一候选成功读取专用审查环境变量，并在测试临时目录外写入无害标记文件。没有读取真实凭据或修改项目代码，但已证明执行权限未被限制。固定命令和固定测试文件不能限制被导入程序的行为。

影响：测试结果不可信，模型生成代码还可能接触宿主资源。扩展到通用产品生成前必须解决。

整改验收：候选应用在受限容器或虚拟机中运行，使用最小环境、只读输入、限定写目录、网络及资源限制；可信验收进程与候选进程分离。退出码、标准输出、候选可写的 JSON/XML 均不能单独决定通过。上述零测试伪造必须被拒绝，越界读写探针必须失败。

### P1-3：运行入口未落实人工批准与版本绑定

位置：[serve_board.py](../demo/dev_team/serve_board.py) 第 10–14 行及第 72–80 行；审批逻辑在 [run_dev_team.py](../demo/run_dev_team.py) 第 14–25 行。

审批命令本身会核对版本并重新验收，但启动服务直接加载 `candidate/board.py`，没有读取任务状态或批准版本。

两条反例均成立：

1. `state.json` 为 `needs_fix`，直接启动服务成功，`PATCH` 非法状态 `deleted` 返回 200 并写入数据库。
2. 先记录 `completed` 和批准版本，再在副本中移除状态校验使哈希变化，启动服务仍成功，非法状态继续写入。

影响：人工门禁目前控制状态记录，不能保证实际启动的是批准产物。作为生产交付入口时，这会绕过前面的评审与测试条件。

整改验收：明确区分受限预览与正式启动；正式入口在加载候选代码前检查批准记录和不可变产物摘要，只运行经批准的快照。拒绝、未批准、过期与批准后篡改均应阻止正式启动。

### P1-4：新讲义的开发团队失败后仍标记 completed

位置：[labs.py](../../multi-agent-training/python/labs.py) 第 163–181 行、第 271–282 行。

图中所有角色通过固定边依次执行，Reviewer 没有结构化结论或失败条件边。恢复 Tester 后，只要没有待执行节点，就记录 `completed`。

本次用实际 StateGraph 和 `labs.main`、受控角色输出复现：Reviewer 明确返回阻断修改意见，Tester 明确返回业务测试失败，`--approve` 仍得到 `completed`，没有返工或失败出口。

影响：这里的完成仅代表角色顺序走完。作为新产品交付信号时会误判失败产物。

整改验收：增加结构化的评审结论、真实测试结果、产物版本和显式状态；阻断或测试失败必须进入修复/转人工，只有版本一致、验收通过且人工批准才能交付。加入修复次数与失败退出条件。

### P1-5：新讲义工具不能提供产品实现和业务测试

位置：[common.py](../../multi-agent-training/python/common.py) 第 69–82 行；[run.mjs](../../multi-agent-training/run.mjs) 的开发角色定义与 devteam 分支；[培训讲义](../../multi-agent-training/培训讲义.md) 第 305–371 行。

- `code_tool(spec)` 忽略规格内容，始终返回固定 `add_task` 示例；分别输入库存与日历需求得到完全相同的源码。
- `test_tool` 只做 `ast.parse`。将函数写成始终返回空列表，结果仍为 `syntax_valid=true`，同时明确记录 `unit_tests_executed=false`。
- Node 开发团队输入“开发一个有库存扣减与并发校验的新产品”，最终状态为 `completed`，只产生 `devteam.json` 和包含测试计划的 `devteam.md`。

讲义已说明这些教学限制，因此不能直接用这一实现验收产品开发能力。

整改验收：提供受限源码读写、差异审查、依赖安装、构建启动和外部业务验收工具；保存真实文件清单、运行命令、失败输出及接口/浏览器验收证据。

### P2-1：主案例固定验收没有覆盖已声明的返回契约

位置：[test_board.py](../demo/dev_team/fixtures/test_board.py) 第 31–36 行；需求在 [requirements.md](../demo/dev_team/fixtures/requirements.md)。

将 `update_status` 的返回值改成 `None`，其余行为保持不变，五项固定测试仍全部通过。需求明确要求返回任务字典。当前 HTTP 回归也只断言 PATCH 状态码，没有检查成功响应结构。

影响：调用方依赖返回的 `id/title/status` 时会失效，现有验收无法发现。五项测试数量不能作为完整验收的证据。

整改验收：按需求逐条建立映射，至少覆盖返回字段与类型、全部合法状态、非法更新不改变原数据、多任务及顺序、API 响应、刷新和进程重启。新需求必须携带相应的外部验收，不能永久复用“五项通过”门槛。

### P2-2：新讲义 Network 可以未经执行和评审就结束

位置：[labs.py](../../multi-agent-training/python/labs.py) 第 138–160 行。

路由仅通过提示词要求完成后选择 END，执行层没有检查 executor、reviewer 或产物。受控路由模型在 planner 后选择 END，实际图正常结束，`steps=1`，executor 和 reviewer 均未运行。

整改验收：END 分支增加可验证的产物、执行及评审状态门槛。选择 END 但缺失证据时应拒绝完成，并转向补齐步骤或明确失败。

### P2-3：生产恢复、审批身份与运行隔离仍缺失

主案例 `state.json` 支持待审批材料落盘，但不是任意步骤恢复。`Session` 重新初始化状态，同一 output 再次运行会重建候选。新讲义使用 `InMemorySaver`，新进程不能恢复旧审批；`--approve` 在新的一次运行中自动放行未来的暂停点。这些边界已在文档声明。

生产仍需任务 ID、持久化检查点、幂等行动、崩溃恢复、并发控制、批准人身份与权限、可审计决定、不可变交付版本及失败回滚。当前 `completed` 也不等于完成构建打包、部署和运行验证。

### P2-4：培训入口与验证说明过期

[新讲义](../../multi-agent-training/培训讲义.md) 第 51 行仍写 Python 不能启动、框架未验证；[验证报告](../../multi-agent-training/验证报告.md) 保留早期未验证描述；[README](../../multi-agent-training/README.md) 已说明安装完成且 Supervisor 有真实运行。当前六种 LangGraph 图已在本次构建成功。根 README 写 42 页，主课件实际是 39 页。

整改验收：按入口分别列出离线测试、构图、真实模型、业务验收、部署验收的日期和证据，统一讲义、README、验证报告及 Word 文档。不能将本次构图成功更新成“真实模型全部通过”。

## 最后实战应升级为怎样的交付

建议保留现有 Review 闭环作为模块，把最后实战升级为一个可独立运行的业务产品，例如“库存与领用管理”。实现至少包含库存查询、领用申请、权限、库存扣减、持久化与可操作前端；其业务规则应从本次需求文件得到。

| 阶段 | 必须落地的产物/行为 | 验收依据 |
| --- | --- | --- |
| 需求澄清 | 输入业务需求、角色、边界和待确认问题 | 未确认的核心规则阻止实现；生成需求到验收映射 |
| 设计与拆解 | 数据模型、接口契约、前后端任务与依赖 | 每项需求有负责模块和验证方式 |
| 实现 | 写入独立工作区的实际源码、依赖和迁移 | 从空业务代码目录构建；产物随新需求变化 |
| 检查 | 受隔离的运行环境和可信验收执行器 | 非法输入、权限、重复请求、并发库存扣减与持久化可复现 |
| Review 与修复 | 对实际变更评审，保存可定位问题 | 失败会真实改代码，旧版本证据失效，再跑评审和验收 |
| 人工确认 | 针对实际完成的候选版本进行批准 | 身份、版本、决定持久化；换进程可继续；过期批准无效 |
| 交付 | 锁定依赖、构建产物、启动说明、配置模板、迁移/回滚说明 | 在干净环境运行，接口与浏览器验收通过 |
| 新产品适配 | 再提供一个不同领域需求 | 不改编排代码和预置业务 fixture，也能生成相应实现 |

整改顺序：先解决候选执行隔离、可信测试结果和正式启动门禁；再接通需求/设计/源码生成；随后完善业务验收与返工、恢复和交付；最后用真实模型在干净环境执行完整案例并更新文档。只修改提示词、角色名称或增加演示文字不能通过这次生产标准。

## 证据与复现

所有反例仅修改 `test-results/production-readiness-20261010/` 内的副本，原课程源码和本地 `index.html` 未修改。测试 HTTP 服务已关闭。

- [主案例反例脚本](../test-results/production-readiness-20261010/audit_main.py) 与 [结果 JSON](../test-results/production-readiness-20261010/main-results.json)：测试误判、有限权限探针、契约漏测、两种审批绕过。
- [新讲义反例脚本](../test-results/production-readiness-20261010/audit_training.py) 与 [结果 JSON](../test-results/production-readiness-20261010/training-results.json)：失败仍完成、固定代码、语法检查、Network 提前 END、六种图构建。
- [Node 开发团队结果](../test-results/production-readiness-20261010/node-devteam/devteam.json)：库存新需求仅产出方案和测试计划。
- [MCP 本地调用日志](../test-results/production-readiness-20261010/mcp-check.log)：工具、资源、提示模板的实际协议调用。

在 `agent-training` 目录执行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_dev_review.py -v
.\.venv-metagpt\Scripts\python.exe -m unittest discover -s tests -p test_dev_team_integration.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_collaboration_live.py -v
.\.venv\Scripts\python.exe -X utf8 test-results/production-readiness-20261010/audit_main.py
..\multi-agent-training\.venv\Scripts\python.exe -X utf8 test-results/production-readiness-20261010/audit_training.py
```

前述回归共 18 项通过。反例脚本中的断言用于确认当前缺陷仍能复现；脚本成功退出不表示被审实现通过生产验收。`test-results` 为本机证据目录，被 Git 忽略，分享报告时需另附这些证据文件。
