# MetaGPT 智能开发团队：Review Agent 演示手卡

课件第 25 至 32 页，十五分钟。从角色、消息、工具与状态设计出发，在 VS Code 展示输入、真实模型评审、真实测试、模型修复、复审和人工门禁。先选择“开发团队 · Review 与修复”按 F5。

## 任务与教学边界

交付任务看板：新增、列表、修改状态，SQLite 保存；前端调用本地 HTTP 服务。教学 PR 移除 `TaskStore.update_status` 的状态校验，非法状态能写入数据库。首轮代码由讲师提供，明确标识为教学 PR；后续由模型评审并修复。PM 与 Architect 使用模型整理需求与设计，Reviewer 使用真实模型执行评审，开发角色根据问题和实际测试失败修改 `board.py`。

使用 MetaGPT 0.8.2 的 Role、Action、Team 和消息订阅。`ReviewCode` 是本项目的自定义 Action，增加团队自己的输入、工具与证据契约，不是直接运行内置 `WriteCodeReview`。自定义 Action 通过已有 `model_gateway` 调用 DeepSeek，连接不可用时明确切换现有 OpenAI/Codex 备用；MetaGPT 内部客户端不发起模型调用。

## 环境准备

使用独立 Python 3.11 环境，保留课程原有 Python 3.13 环境。

MetaGPT 完整依赖中 `lancedb==0.4.0` 在当前 Windows 不可用。本例不使用 RAG、向量库、Data Interpreter 或默认软件公司的完整生成流程；安装本体与本例实际导入的依赖集合。这套依赖只验证了本例所用功能。官方包初始化仍会导入一些供应商 SDK，因此依赖比本例的业务代码多。

已有 Python 3.11 时，在项目根目录：

```powershell
# 用本机 Python 3.11 的实际路径替换下行
python3.11 -m venv .venv-metagpt
.\.venv-metagpt\Scripts\python.exe -m pip install --no-deps metagpt==0.8.2
.\.venv-metagpt\Scripts\python.exe -m pip install -r demo/dev_team/requirements-core.txt
```

推荐 Windows 使用 uv 安装后运行 `powershell -ExecutionPolicy Bypass -File tools/setup_dev_team.ps1`。脚本使用空闲盘符临时映射项目，缩短旧 SDK 的源码与 wheel 构建路径，在 finally 中移除映射；所有依赖和缓存仍保存在项目中。可先运行 `uv python install 3.11`。本仓库验证记录在 `test-results`。

模型沿用课程已有配置，见 [模型指南](model-demo-guide.md)。密钥不写入课件、源码或运行产物。MetaGPT 导入所需的无凭据配置和框架日志写入本次输出目录的 `metagpt-runtime`，不要求修改用户的 MetaGPT 配置文件。启动日志会打印实际供应商元数据。

## 开发设计怎样对应前面的内容

| 知识 | 本例实现 |
| --- | --- |
| 独立角色与上下文 | 角色只接收本轮 `rc.news`，旧版本意见保留审计，不自动加入新一轮模型上下文 |
| 协作模式 | 正常路径按产物顺序推进；宿主决定失败回退，本例不是模型主管自主调度 |
| 消息与共享状态 | `cause_by` 指明上游 Action；状态记录版本、意见、测试、轮次和预算 |
| 工具调用 | Reviewer 提出三项白名单检查；宿主实际执行并返回 observations |
| 记忆与验收 | 版本变化使旧证据失效；当前评审与固定测试必须对应当前文件内容 |
| 人工介入 | 待审批材料落盘，新进程提交显式决定；不等同恢复整个 MetaGPT 团队 |

角色链：PM → Architect → Developer → Reviewer → Tester。评审或测试失败后，Host 发布 `FixRequested` → RepairDeveloper 修复 → Reviewer → Tester。开发首轮和修复是同一职责的两个单 Action 实例，分别订阅设计消息与修复请求。

## VS Code 源码讲解顺序

1. `demo/dev_team/fixtures/requirements.md`：先看交付与验收，状态集合、持久化和失败行为都明确。
2. `demo/dev_team/team.py`：看 `build_team`、`_watch`、`cause_by`；在 `ArtifactRole._act` 查看当前消息与本轮输入。
3. `demo/dev_team/tools.py`：看 `collect_context` 的 diff、内容摘要、完整文件、原始行号以及缺失/截断标记。
4. `demo/dev_team/actions.py` 的 `ReviewCode.run`：第一次模型请求决定检查工具，真实执行后第二次请求输出评审结论。
5. `demo/dev_team/contracts.py`：看结构化字段、证据定位校验和 `delivery_gate`。JSON 合法不等于意见正确，必须核对契约、测试与人工判断。
6. `RepairCode.run`：模型只返回 `board.py` 完整源码，编译校验后写入；固定测试不允许修改；写入后清空旧评审和测试。
7. `demo/run_dev_team.py`：看预算、运行入口和另一个进程的审批决定。

推荐断点：`ReviewCode.run` 中工具选择后、`validate_review` 中原文证据检查、`RepairCode.run` 中写入前、`delivery_gate` 中版本比较。

## 输入契约与工具

`context-0.json` 包含 base/head 内容 SHA-256、统一 diff、`board.py`、前端调用方、固定需求与固定测试。摘要是文件内容哈希，不是 Git commit ID。本例固定四份材料，尚未实现大型仓库的依赖检索。

Reviewer 只能请求：

| 工具 | 实际行为 |
| --- | --- |
| read_diff | 读取根据真实 baseline/head 生成的统一 diff |
| read_context | 读取原始行号代码、调用方、契约、测试和覆盖清单 |
| run_fixed_tests | 独立进程执行讲师维护的五项 unittest，返回退出码与真实输出 |

工具命令由宿主固定，模型不能指定 shell 命令、测试路径或任意文件路径。本例 unittest 临时目录是独立测试进程，不能当作生产代码执行的安全沙箱。

## 评审输出与校验

每条 finding：`id / severity / file / line / end_line / title / evidence / impact / suggestion / test_name`。`verdict` 为 `pass / request_changes / needs_context`；本课 high/medium 阻断，low 为建议。

原文证据必须出现在声明的文件和行号范围内。上下文缺失或截断时只能进入 needs_context。代码与注释都是待审数据，不能作为评审指令。只指出本次变更引入的具体缺陷，不用无关重构或风格问题阻断。

`revision` 由宿主附加，覆盖候选代码、前端和固定验收材料，模型不能自行决定版本。程序验证定位与字段，不能证明问题语义必然正确；仍需固定测试和人工判断。

## 运行、修复与复审

```powershell
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --scenario buggy --step
```

终端在启动时打印本次目录，随后逐步显示角色行动、模型请求、工具请求与结果、评审、修复和门禁。模型失败如实保留失败状态，不能静默改用规则结果。默认最多两轮修复、十二次模型请求、六百秒；逐步演示的等待计入总时限，迟到的模型或测试结果不能作为通过证据。

把终端打印的本次目录加入 VS Code 工作区。查看：

| 产物 | 要观察什么 |
| --- | --- |
| requirements-generated.md / design-generated.md | 模型整理的需求、设计与固定契约的关系 |
| context-0.json | 真实 diff、材料、缺失标记与版本 |
| review-0.json / tests-0.json | 非法状态问题与失败测试相互印证 |
| candidate/board.py | 模型实际修复；对照原本移除的校验 |
| context-1.json / review-1.json / tests-1.json | 新版本必须重新取得证据，旧结论不能沿用 |
| state.json | 完整事件、模型元数据、预算与 waiting_approval |

成功出口先停在 waiting_approval。不自动批准、合并、发布或部署。

## 已验证运行与课堂回放

2026-10-08 的真实运行已经完成 Review → 修复 → 复审：首轮 `request_changes`，非法状态验收失败；模型修复一次后，复审 `pass`、五项固定验收通过，共七次真实模型请求。实际供应商为 CCSwitch `1008`、模型 `gpt-6.1-sol`、传输 `codex-cli`，状态记录 `using_backup=true`。本次结果不能称为 DeepSeek 实测。详细证据与验证范围见 [实战验证记录](dev-team-verification-2026-10-08.md)。

本机原始目录为 `demo/output/dev-team/verification-20261008-buggy`，保留在 `waiting_approval`。打开 `review-0.json`、`tests-0.json` 与 `review-1.json`、`tests-1.json` 对照；本次模型修复恢复了 baseline，因而 `context-1.json` 的 diff 为空。展示这些文件时说明“这是已完成真实调用的产物回放”，重新 F5 才是一次新的模型运行。

若用这份本机记录练习人工批准和看板，先复制到新目录，再执行下一节的人工决定命令：

```powershell
$devSource = 'demo/output/dev-team/verification-20261008-buggy'
$devRun = 'demo/output/dev-team/classroom-' + [guid]::NewGuid().ToString('N')
Copy-Item -LiteralPath $devSource -Destination $devRun -Recurse
```

原产物和本机测试副本不随 Git 或演示包分发。其他机器需先按运行命令生成自己的产物。`incomplete` 的 `needs_context` 出口已做受控 MetaGPT 框架验证，尚未做真实模型调用；按下一节对应命令运行后再解释当次结果。

## 人工决定与运行看板

在 PowerShell 中把本次路径填入 `$devRun`，读取当前待批准版本：

```powershell
$devRun = 'demo/output/dev-team/这里填本次目录'
$devState = Get-Content -LiteralPath "$devRun/state.json" -Raw -Encoding utf8 | ConvertFrom-Json
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --decision approve --run-dir $devRun --revision $devState.review.revision
.\.venv-metagpt\Scripts\python.exe demo/dev_team/serve_board.py --run-dir $devRun --port 8766
```

打开 `http://127.0.0.1:8766`，新增任务，修改为已完成并刷新。审批决定也可用 `reject`。新进程核对内容版本并重新执行固定验收；任务不在待审批阶段、版本过期或验收失败，都不能批准。该入口仅作课堂人工决定，不含生产身份鉴权或并发审批锁。

## 另外三个课堂分支

```powershell
# 无缺陷变更：检查是否凭空提出阻断意见
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --scenario clean
# 缺少需求上下文：应待补充，不能判通过
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --scenario incomplete
# 禁止自动修复：首次失败后转人工
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --scenario buggy --max-repairs 0
```

真实模型意见不保证每次相同，以本次文件和状态为准。工具选择、错误输出修正和模型请求都计入调用上限。

## 团队接入与校准

先用历史 PR 建立“有缺陷、无缺陷、缺上下文”盲测样本，人工标注真问题，记录漏报、误报、定位准确与可复现比例。意见数量不能说明评审质量。先明确阻断等级，再将 Role / Action 接入固定 PR 版本、代码检索和团队检查工具。

生产接入需要补充大型仓库检索、身份与仓库权限、隔离执行、幂等评论与去重、并发审批和 CI 状态；本例不会向任何平台发布评审意见。

## 验证命令

```powershell
# 不依赖 MetaGPT 或模型：证据、版本、固定测试
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_dev_review.py
# 运行 MetaGPT 消息环境，用受控模型响应验证各种出口
.\.venv-metagpt\Scripts\python.exe -m unittest discover -s tests -p test_dev_team_integration.py
# 八页实战的桌面与手机浏览器检查，需要 Playwright 与 Chrome
node --test tests/dev_team_ui.test.cjs
```
