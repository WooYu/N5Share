# 新产品实战整改与验证

日期：2026-10-10。本记录对应 [原审查报告](training-production-review-2026-10-10.md)，原报告作为历史缺陷证据保留。运行方法见 [新产品开发指南](product-development-guide.md)。

## 实现变化

| 原问题 | 当前实现 |
| --- | --- |
| 固定看板冒充新产品生成 | `--requirements` 输入业务与外部验收；PM/Architect 的实际产物进入 Developer；生成完整多文件树，库存与预约共用同一编排器 |
| 零测试输出伪造、宿主权限执行 | 候选只在非 root、只读、断网且资源受限的容器内运行；断言由宿主执行；HTTP 传输独立 UID；严格核对全部规定用例 |
| 未批准或修改后仍可启动 | 正式启动先核对状态、OS 用户批准记录、有效期、证据、镜像、源码/需求/验收器摘要及快照，之后才启动经验证的副本 |
| 阻断评审/失败测试仍 completed | 失败进入修复或 needs_context/needs_human/failed；通过后仅 waiting_approval，审批另用当前版本决定 |
| 固定代码工具、仅语法测试 | 新讲义共用产品实现；源码工具写真实受限文件树，测试工具实际执行 Docker HTTP 与浏览器验收 |
| 看板返回值漏测 | 增加返回字段/类型、全部合法状态、错误后数据不变、多任务顺序、HTTP 和重启验收 |
| Network 提前 END | 必须有本次实际保存的产物、执行证据及同一产物摘要的结构化评审；缺失时补齐或超限失败 |
| 恢复和说明过期 | 持久状态、进程锁、显式恢复、版本快照、独立 ZIP；同步新讲义 Markdown/Word 与运行文档 |

## 证据分层

确定性回归包含原6项Review合同测试、3项实际MetaGPT框架集成，以及14项新增整改回归。新讲义另有10项Node入口回归、3项实际LangGraph Network/工具回归。测试替身只替换模型输出，实际容器、HTTP、门禁或图按对应测试执行；不能据此宣称模型质量。

两份新业务运行调用真实模型。实际网关记录为 CCSwitch 供应商 `1008`、`gpt-6.1-sol`、`codex-cli`。库存与预约都从没有业务源码的目录开始，仅提供需求和验收 JSON，没有改动编排器来选择业务 fixture。

初始尝试真实暴露了生成时限不足、设计的嵌套前端与校验规则不一致、每请求启动 Docker CLI 导致浏览器超时等问题。这些运行被标为 failed/needs_context/stale。整改后使用常驻传输进程，保留失败日志，不将失败尝试计为成功。

版本摘要包括可信验收器源码。因此开发过程中改动验收器会使正在执行的测试/审批进入 stale；最终结论必须使用冻结实现后重新运行的证据。

## 实际结果

| 真实生成产品 | 文件数 | 模型请求数，含失败和复审 | 真实修复轮数 | 外部业务验收 | 原始产物状态 |
| --- | ---: | ---: | ---: | --- | --- |
| 库存与领用 | 11 | 15 | 1 | 7组HTTP + 1组浏览器通过 | waiting_approval |
| 会议室预约 | 9 | 13 | 1 | 6组HTTP + 1组浏览器通过 | waiting_approval |

库存的真实Reviewer退回响应体断流重试问题；预约的Reviewer退回非法Unicode输入问题。开发者均实际修改多文件源码，新的评审、验收绑定新的版本。另由可信外部探针验证库存响应断流后使用相同请求号重试、只扣库一次；预约非法Unicode返回400且未新增记录。模型生成的内部测试源码没有被当作通过证据。

交付审批只在单独的自动化测试副本执行，批准身份明确记录为 `automated-delivery-test`。两份原始产物均未替用户批准。测试副本导出的ZIP在没有原始工程的新目录、独立解释器与新容器中，执行实际正式启动函数、发送HTTP请求，再执行全套业务和浏览器验收。验收使用新数据库，并检查进程重启。

最终源码与验收器版本：

- 库存：`7d399d423bb452d83e1827424bf5372d582cbd4afa7eb8c78e1b75155d7baad4`
- 预约：`992e3134f1c714218ea048f367a17cedc1e90864ffc4825d69385c43d03793c7`

| 验证 | 结果 | 本机日志/证据 |
| --- | --- | --- |
| 原Review合同6项 + 实际MetaGPT3项 + 新整改14项 | 23项通过 | `test-results/product-stable-regression.log` |
| 拒绝新需求的内部legacy标记后重跑整改回归 | 14项通过 | `test-results/product-policy-final.log` |
| Node入口与原协作模式 | 10项通过 | `test-results/product-node-final.log` |
| 新讲义Network与工具反例 | 3项通过 | `test-results/product-lecture-final.log` |
| 主课件结构与源码契约 | 3项通过 | `test-results/product-course-contract.log` |
| 实战桌面/手机布局、讲稿、术语与发音控制 | 9项通过 | `test-results/product-course-ui.log` |
| Node/Python产品入口环境检查 | 均返回environment_ready，0次模型调用 | 本次终端记录 |
| 两份干净交付 | 正式启动与全部业务验收通过 | `test-results/product-remediation/final-delivery-summary.json` |
| 两个真实评审问题的外部回归 | 断流幂等、非法Unicode通过 | `inventory-repair-final.json`、`booking-repair-final.json` |

课件重建为39页 / 90分07秒，新增产品入口和实战说明，保留讲稿与英文发音功能。同步新讲义Markdown与Word；旧看板保留为Review子练习。

真实产品状态、源码、评审、请求响应及截图在 `test-results/product-remediation/inventory-live/` 与 `booking-live/`。最终测试交付包在同级 `inventory-final-delivery/` 与 `booking-final-delivery/`，文件名为 `delivery-7d399d423bb4.zip` 和 `delivery-992e3134f1c7.zip`。本机证据目录不纳入Git，分享审查时需另附这些证据。

这次验收证明两份明确业务需求能驱动实际产品生成、隔离运行、返工、版本门禁及独立交付；不构成对任意需求或生产部署的成功保证。

## 实现范围

已实现的是本地单机、Python标准库/SQLite产品开发与交付实战。Docker、宿主用户及人工提供的需求/验收属于可信边界。演练角色令牌不等于企业用户认证；磁盘配额、集中身份授权、远程部署、生产备份服务和任意步骤的框架内部恢复不在此实现中。干净交付指独立解压目录和新容器，不等于已在另一台物理机器部署。
