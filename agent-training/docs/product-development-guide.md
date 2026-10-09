# 从新需求生成并交付产品

本入口接收业务需求及外部验收契约，模型生成 PRD、设计和完整多文件应用。支持 Python 标准库、SQLite 与原生 HTML/CSS/JS。原有 `--scenario buggy` 看板保留为 Review 练习；新产品使用 `--requirements`，不复制业务 fixture。

## 准备与运行

使用 `.venv-metagpt`、已配置的课程模型网关、Docker Linux 引擎、Python 3.11 镜像和 Playwright Chromium。模型使用情况以每次 `state.json` 中的 metadata 为准。候选运行器只使用本机已有镜像，不隐式拉取、不安装模型提出的依赖。首次准备：

```powershell
docker pull python:3.11-slim
.\.venv-metagpt\Scripts\python.exe -m playwright install chromium
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --requirements demo/product_team/examples/inventory.json --check
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --requirements demo/product_team/examples/inventory.json --output demo/output/inventory --max-model-calls 20 --max-seconds 1800
```

另一领域：将需求换成 `demo/product_team/examples/booking.json`，输出换成新目录。编排器没有库存或预约业务分支；只有输入文档及验收不同。VS Code 提供“开发团队 · 新产品生成”配置。

需求 JSON 包含 `name`、`requirements`、空数组 `unresolved`、HTTP `acceptance`、`browser`。需求必须先由人确认；非空 `unresolved`、零项业务验收或缺少浏览器断言会拒绝运行。示例展示返回字段、类型、无权限、非法输入、重复请求、并发、重启、页面提交和刷新。要改变业务规则，应同时修改需求及独立验收，然后新建运行目录。

`acceptance` 是声明式数据，不能执行脚本。支持请求、JSON字段/类型/长度/值断言、保存响应变量、并发状态码集合以及进程重启。`browser` 只支持 fill、select、click、text/contains、reload；没有任意 JavaScript 执行入口。模型提交自己的测试不能替换这两套验收。

## 实际流程和失败出口

MetaGPT 的 PM → Architect → Developer → Reviewer → Tester 按消息订阅执行。Developer 消费原始需求、真实 PRD 和设计，提交完整文件树：`app.py`、领域模块、前端、`README.md`、`requirements.lock`。完整 bundle 校验路径、文件数、体积、Python语法和无第三方依赖约束后才替换工作区，并记录旧文件以生成差异。

Reviewer 请求 diff、完整上下文和外部验收，返回带文件、行号、原文证据的结构化问题。Tester 使用本轮同一不可变版本的宿主验收结果；修改版本会重新执行。`request_changes`、业务失败进入修复；缺上下文进入 `needs_context`；修复次数耗尽进入 `needs_human`；异常进入 `failed`。只有评审通过且所有规定用例实际通过才进入 `waiting_approval`。

通过编译、容器退出码、标准输出出现 `Ran 5 tests`、模型声称测试成功都不能代替验收。零用例或少跑规定用例一律失败。

## 隔离与证据

候选仅在 Linux Docker 容器内运行：非 root、只读根和源码、无网络、去掉全部 capabilities、no-new-privileges、CPU/内存/进程限制。写入范围为独立 `/data` 和有大小限制的 `/tmp`。不挂载仓库、凭据或 Docker socket，不继承宿主环境变量。Docker 不可用时直接失败，没有宿主执行降级。

验收断言在宿主可信代码中；HTTP 传输进程使用与候选不同的 UID，禁止候选修改或冒充传输进程。浏览器经回环代理访问容器，拦截外部请求并开启 Chromium 沙箱。保存请求响应、每项结果、运行命令、日志和浏览器截图。验收数据库每轮新建，并测试进程重启；正式数据目录与验收目录分开。

这是本地单机开发实战：Docker 与宿主管理员、需求/验收作者属于可信边界。示例 Bearer 角色是演练身份，不是生产账户认证。接入真实用户前须替换认证与业务验收；数据磁盘配额、集中身份授权、远程部署和生产备份服务不在此运行器中。

## 恢复、批准和交付

运行目录保存 PRD、设计、候选、diff、review、tests、状态和事件。所有写入使用进程锁，进程退出释放锁。`--resume` 复用已写入的文档与源码，从评审/验收继续；不会假装恢复任意 MetaGPT 内部消息位置。调用数和修复次数持久化；追加预算须显式提供更大的 `--max-model-calls`。

```powershell
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --resume --output demo/output/inventory --max-model-calls 20 --max-seconds 1800
```

先阅读当前目录的 `state.json`、源码、评审和验收证据，再针对实际 `review.revision` 作决定。没有自动批准未来版本的 `--approve`。

```powershell
$run = 'demo/output/inventory'
$revision = (Get-Content "$run/state.json" -Raw | ConvertFrom-Json).review.revision
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --decision approve --run-dir $run --revision $revision
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --serve --run-dir $run --port 8766
```

批准会重新在干净容器验收，记录 OS 用户身份、时间、24小时有效期、源码/需求/验收器摘要、镜像 ID 与证据摘要，生成 `delivery-<revision>.zip`。拒绝使用 `--decision reject`。源码、验收、审批、已批准快照任一变化都会拒绝正式启动；不加载未批准源码。批准过期后用 `--resume` 重新评审验收，再明确批准。

在没有原始工程的目录解压 ZIP，安装 Docker Linux 和相同镜像，执行 `python serve.py`。通过 `docker save`/`docker load` 携带镜像，版本以 ZIP 中的不可变 sha256 ID 为准。运行器无 pip 依赖；再次执行浏览器验收需 Playwright。`DELIVERY.md` 和生成的 README 包含配置、数据初始化、备份与回滚说明。升级和回滚均先停止服务，选用单独批准的快照及对应数据库备份。

## 新讲义入口

`multi-agent-training` 的 Node/Python devteam 都调用同一个 MetaGPT 产品入口，使用相邻 `agent-training/.venv-metagpt`，也可通过 `TRAINING_PRODUCT_PYTHON` 指定解释器。其他协作模式继续使用各自原框架。

```powershell
node run.mjs --mode devteam --requirements ../agent-training/demo/product_team/examples/booking.json --output ./outputs/booking
.\.venv\Scripts\python.exe python/labs.py --lab devteam --requirements ../agent-training/demo/product_team/examples/inventory.json --output ./outputs/inventory
```

相对需求和输出路径应从当前调用目录解析。只有报告或测试计划的旧 devteam 产物不满足当前交付门禁。
