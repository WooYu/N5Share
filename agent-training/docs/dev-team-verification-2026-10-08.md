# MetaGPT Review Agent 实战验证记录

验证日期：2026-10-08（Asia/Shanghai）。课程为 39 页 / 90 分 07 秒，实战在第 25–32 页，共十五分钟。运行入口与课堂操作见 [演示手卡](dev-team-demo-guide.md)。

## 真实模型闭环

本机运行目录：`demo/output/dev-team/verification-20261008-buggy`。教学 PR 由讲师提供；需求与设计整理、评审和修复调用真实模型。使用 MetaGPT 0.8.2 的 Role / Action / Team 消息环境，评审为本项目自定义 `ReviewCode`，实际模型请求通过已有网关完成。

实际供应商为 CCSwitch `1008`，模型为 `gpt-6.1-sol`，传输为官方 `codex-cli`，`state.json` 记录 `using_backup=true`。共七次模型请求，一轮修复；不能把这份记录描述为 DeepSeek 实测。

| 阶段 | 结果 | 证据 |
| --- | --- | --- |
| 初次评审 | `request_changes`，一条 medium 阻断问题 | `review-0.json`：`board.py` 第 29 行 UPDATE 前缺少状态校验 |
| 初次固定验收 | 五项测试中非法状态测试失败 | `tests-0.json`：`deleted` 未抛出 ValueError，原记录被修改 |
| 模型修复 | 恢复更新前的状态集合校验 | `candidate/board.py`：只允许 todo / doing / done |
| 新版本复审 | `pass`，无问题 | `review-1.json` 与 `context-1.json` |
| 新版本固定验收 | 五项全部通过 | `tests-1.json`：退出码 0，`Ran 5 tests` / `OK` |
| 最终状态 | `waiting_approval` | `state.json`：无人工决定，未批准、合并或发布 |

续接时重新计算的候选与验收材料摘要为：

```text
7df7c9d668d73124a32614a698c4a9b39e6add18fa3db1a87c96cbf4e11133d8
```

它与当前评审及测试 revision 一致，是内容摘要而非 Git commit。课堂审批仍应重新读取当次状态，入口会重新核对当前文件并执行固定测试。本次修复源码恢复 baseline，所以复审 diff 为空；这是本次实际输出。

## 续接时完成的验收

批准、拒绝和看板操作均使用真实运行的测试副本，原运行的 `state.json` 与候选摘要保持不变。固定验收仍读取仓库 `fixtures` 中的讲师测试与需求，未复制或改写为模型测试。

| 检查 | 实际结果 |
| --- | --- |
| 独立进程 approve | 重新执行五项验收，通过后状态为 `completed`，退出码 0 |
| 独立进程 reject | 重新执行五项验收，状态为 `rejected`，退出码 0 |
| 重复 approve / reject | 两个副本均拒绝跨阶段决定，退出码 2 |
| Chrome 桌面操作 | 新增、列表、todo → doing → done 均成功，页面刷新后仍为 done |
| 非法状态请求 | PATCH `deleted` 返回 400，原记录保持 done |
| 重启 HTTP 服务 | SQLite 记录保留，页面重新加载仍为 done |
| 手机页面 | 390×844 无横向溢出，状态正确；桌面为 1280×720 |
| 页面错误 | 未出现 JavaScript 页面异常 |
| 核心合同回归 | `test_dev_review.py` 六项通过，覆盖定位、缺上下文、版本与人工门禁、真实测试、HTTP 和迟到结果 |

本机证据在 `test-results/dev-team-continuation-20261008/`：

- `decisions-summary.json`、`approve.log`、`reject.log` 及两个重复决定日志。
- `board-summary.json`、`board-server.log`、`board-desktop.png`、`board-phone.png`；`verify_board.py` 为本次浏览器验收脚本。
- `core-contracts.log`；`metagpt-installed-versions.txt` 记录当前 181 个已安装发行包的版本。
- `delivery-summary.json`：39 页 / 90 分 07 秒、实战第 25–32 页、源码与编译课件标题一致、两个 VS Code 实战启动项指向独立环境。

看板验收的临时服务已停止。批准与拒绝只改变本机副本状态，不会写入外部平台。

Git 文件范围检查通过，128 份源码、文档和参考文件；运行产物、测试副本、依赖环境与本机工作记录保持忽略。续接时补充演示文档和验证记录，未修改课件内容；提交前另做全量回归与源码重建检查。

## 提交前检查

- Python 主回归：99 项，`OK (skipped=3)`，日志 `test-results/dev-team-continuation-20261008/pre-commit-python.log`。
- 独立 MetaGPT 环境集成：3 项全部通过，日志 `pre-commit-metagpt.log`。
- JavaScript / Chrome 全量回归：39 项中 38 项通过、1 项跳过、0 失败，日志 `pre-commit-node-final.log`。旧出游真实窗口测试已按架构标识定位，避免新增大纲页后仍使用旧页码；八项窗口隔离与配置测试全部通过。
- 空目录源码重建：128 份允许提交的文件可重建课件并运行协作 CLI 帮助入口，日志 `source-checkout.log`。
- 暂存内容通过文件范围、凭据字面量与 Git 空白检查，未纳入本机凭据、模型运行产物或依赖环境。

## 已有验证与边界

续接前同日已通过主课程 Python 回归（99 项，跳过 3 项）、真正 MetaGPT 框架集成（3 项），以及八页桌面 / 手机布局检查；日志分别为 `test-results/dev-team-python-regression.log`、`dev-team-metagpt-integration.log`、`dev-team-ui.log`。这些既有结果与本次续接验收分别记录，没有重新发起七次模型调用。

`clean`、`incomplete` 和禁止修复的异常出口已有受控模型框架测试。`incomplete` 尚未做真实模型验证，本次不重复收费调用来证明已由合同和框架覆盖的出口。若课堂运行该情景，以当次实际状态为准。

本机使用独立 Python 3.11.17。MetaGPT 完整依赖中的旧 `lancedb==0.4.0` 不支持当前安装方式；本例安装 MetaGPT 本体和自定义 Role / Action / Team 实际需要的依赖，不代表全部 MetaGPT 功能可用。关键已验证版本包括 `pydantic==2.7.4`、`openai==1.39.0`、`playwright==1.50.0`、`volcengine-python-sdk==1.0.94` 和 `semantic-kernel==0.4.3.dev0`。完整安装快照为本机记录，准备环境继续使用 `requirements-core.txt` 和安装助手。

评审字段与原文定位校验不能证明问题语义必然正确；本例以固定验收和人工判断共同把关。审批入口保存材料并校验当前版本，不提供完整团队恢复、生产身份鉴权、并发审批锁、大型仓库检索或 CI 评论发布。课堂仍需明确批准当次版本。
