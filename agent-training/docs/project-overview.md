# 项目说明：高级推理框架与多 Agent 协作培训包

本项目面向 Java 后端、前端和客户端开发者，将 Agent 概念讲解、可交互课件、真实协作代码和需求驱动的产品开发实战放在同一个培训目录中。适合讲师备课、团队培训，以及开发者在本地运行、调试和扩展案例。

项目位于 `N5Share` 仓库的 `agent-training/` 子目录。**本文所有命令均在 `agent-training/` 内执行**；使用 VS Code 时也打开这个文件夹。

## 1. 项目提供什么

| 模块 | 内容与用途 | 入口 |
| --- | --- | --- |
| 培训课件 | 39 页、90 分 07 秒；包含目录、讲师备注、术语音标与朗读 | 构建后的 `index.html` |
| 七种架构互动演示 | 用出游任务比较单 Agent、ReAct、Plan & Execute、多 Agent、Router + Skill、Blackboard、Graph / Workflow | 课件第 3 至 12 页 |
| 五种真实协作模式 | 顺序链、主管、层次化、Swarm、Network；使用 LangGraph 编排、真实模型与本地工具 | `demo/run_collaboration.py` |
| 框架介绍 | Microsoft Agent Framework、LangGraph、MetaGPT 的能力与示例 | 课件第 22 至 24 页 |
| 开发团队实战 | MetaGPT 角色协作、评审、修复、复审、人工批准；支持新需求生成多文件产品 | `demo/run_dev_team.py` |
| 本地模型服务 | 为课件中的真实模型窗口提供 HTTP 接口 | `demo/server.py` |
| 课后参考 | 合成诊断资料、工具、轨迹及旧规则示例 | `demo/agents.py`、`demo/reference/` |

浏览器中的逐步演示采用确定性的教学逻辑；真实协作入口会调用模型，并记录实际路径、工具证据与失败状态。两者均使用合成业务资料。模型调用通常需要联网，并可能产生供应商费用。

## 2. 技术组成与运行条件

| 使用范围 | 环境与依赖 |
| --- | --- |
| 查看已生成课件 | Chrome 或 Edge；页面资源在本地，无需前端构建工具或 CDN |
| 构建课件、运行主 Demo | Python 3.10+，建议新建 Python 3.11 虚拟环境；依赖见 `requirements.txt` |
| 五种协作模式 | LangGraph 1.2.11、httpx 0.28.1；有效的模型配置 |
| 开发团队实战 | 独立 Python 3.11 环境、MetaGPT 0.8.2，以及 `demo/dev_team/requirements-core.txt` |
| 候选产品运行与验收 | Docker Linux 引擎、本机已有的 `python:3.11-slim` 镜像；新产品浏览器验收需要 Playwright Chromium |
| 浏览器回归检查 | Node.js、Playwright 与 Chrome；具体要求见各测试文件 |

主环境 `.venv/` 与开发团队环境 `.venv-metagpt/` 分开安装。MetaGPT 环境使用本例所需的依赖集合，完整官方依赖在 Windows 上存在兼容性限制，安装细节见 [Review 实战手卡](dev-team-demo-guide.md)。

## 3. 目录与源码职责

```text
agent-training/
├─ README.md                     项目入口与课程说明
├─ build.py                      生成课件、大纲与讲师讲稿
├─ requirements.txt              主环境依赖
├─ course/                       课程内容、架构图、讲稿和术语源数据
├─ web/                          页面模板、样式与浏览器交互
├─ demo/
│  ├─ run_collaboration.py        五种协作模式 CLI
│  ├─ collaboration_live/         LangGraph 图、角色、工具和运行时
│  ├─ run_dev_team.py             开发团队、新产品、审批和启动 CLI
│  ├─ dev_team/                   MetaGPT 角色、消息、评审和修复
│  ├─ product_team/               需求、生成、隔离验收与版本交付
│  ├─ model_backup.py             主用模型与备用切换
│  ├─ model_gateway.py            模型连接与调用适配
│  ├─ server.py                   课件本地 HTTP 服务
│  └─ reference/                  旧规则示例
├─ docs/                         使用指南、设计说明与验证记录
├─ config/.env.example           配置变量说明，不含凭据
├─ tests/                        Python、JavaScript 和浏览器回归
├─ tools/                        环境准备、打包与交付验证
├─ assets/                       课件依赖的资料、图片和 PDF
├─ archive/                      历史课件输入与迁移记录
├─ .vscode/                      共用调试配置
├─ dist/                         本地生成的分发包
└─ test-results/                 本地检查日志和截图
```

`index.html`、`docs/outline.md`、`docs/speaker-notes.md` 由构建生成。首次克隆后需要先构建；修改课程应编辑 `course/` 和 `web/`，再重新生成这些文件。

## 4. 快速开始：构建并查看课件

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe build.py
```

已有可用 `.venv` 时跳过创建步骤。macOS/Linux 使用 `python3 -m venv .venv` 创建环境，后续将解释器路径替换为 `.venv/bin/python`。

构建后用浏览器打开 `index.html` 即可讲课，无需模型配置。方向键或空格翻页，`O` 打开目录，`N` 查看讲师备注，`F` 切换全屏，`?` 查看帮助。术语朗读使用浏览器与系统英语语音；没有可用语音时仍可阅读音标和释义。

如果需要页面中的真实模型入口，配置模型后运行：

```powershell
.\.venv\Scripts\python.exe demo/server.py
```

访问 `http://127.0.0.1:8765`。端口占用时增加 `--port 8766`，并使用对应地址。普通静态 HTTP 服务不提供演示所需的 API。

## 5. 配置模型并运行真实协作

DeepSeek 为主用配置，程序读取进程环境中的 `DEEPSEEK_API_KEY`，也支持已有本机配置。`config/.env.example` 仅说明变量名称，程序不会自动加载 `.env` 文件。将自己的密钥配置到当前终端或本机存储，具体方式见 [模型演示指南](model-demo-guide.md)。

备用连接复用本机已有的 CCSwitch 与官方客户端配置。发生连接、认证、额度、限流或超时异常时，运行时会明确记录备用切换；备用也不可用则停止。模型配置与运行证据中显示的实际供应商可能不同，应以本次记录为准。

```powershell
# 仅检查配置能否读取，不发起模型请求
.\.venv\Scripts\python.exe demo/run_collaboration.py --check-model

# 运行主管模式；每个节点完成后按 Enter 继续
.\.venv\Scripts\python.exe demo/run_collaboration.py --pattern supervisor --scenario missing --step

# 比较资料完整时的五种模式
.\.venv\Scripts\python.exe demo/run_collaboration.py --pattern all --scenario normal
```

`--pattern` 支持 `sequential`、`supervisor`、`hierarchical`、`swarm`、`network` 和 `all`。`normal` 提供完整资料；`missing` 首次漏掉餐费等信息，用于观察反馈和补充路径。

每次运行在 `demo/output/collaboration-live/` 下建立独立目录，保存 JSON 轨迹和 Markdown 报告。重点检查实际供应商、调用次数、角色路由、工具证据和验收结果。轨迹用于复盘，不代表支持任意节点的持久恢复。

VS Code 可选择“真实协作”调试配置按 F5；断点与课堂顺序见 [五种协作模式指南](collaboration-demo-guide.md)。

## 6. 从新需求生成产品

产品实战接收需求和外部验收 JSON，由 PM → Architect → Developer → Reviewer → Tester 协作生成 PRD、设计及完整多文件应用。当前支持 Python 标准库、SQLite 和原生 HTML/CSS/JS；库存与会议室预约示例分别位于 `demo/product_team/examples/inventory.json`、`booking.json`。

首次准备独立环境：

```powershell
py -3.11 -m venv .venv-metagpt
.\.venv-metagpt\Scripts\python.exe -m pip install --no-deps metagpt==0.8.2
.\.venv-metagpt\Scripts\python.exe -m pip install -r demo/dev_team/requirements-core.txt
docker pull python:3.11-slim
.\.venv-metagpt\Scripts\python.exe -m playwright install chromium
```

Windows 旧 SDK 安装遇到路径过长时，可在安装好 `uv` 后运行 `powershell -ExecutionPolicy Bypass -File tools/setup_dev_team.ps1` 准备 Python 环境；Docker 镜像和 Chromium 仍按上面的命令准备。

启动 Docker Linux 引擎、配置模型后执行：

```powershell
# 检查需求和 Docker 镜像，不调用模型；不替代完整模型与浏览器验收
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --requirements demo/product_team/examples/inventory.json --check

# 从需求生成产品，输出目录应为本次运行独立使用
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --requirements demo/product_team/examples/inventory.json --output demo/output/inventory --max-model-calls 20 --max-seconds 1800

# 中断后复用该目录的需求、文档和源码，从评审与验收继续
.\.venv-metagpt\Scripts\python.exe demo/run_dev_team.py --resume --output demo/output/inventory --max-model-calls 20 --max-seconds 1800
```

需求 JSON 必须包含已确认的业务规则、空的 `unresolved`、HTTP `acceptance` 和 `browser` 断言。换业务时同时更新需求与独立验收，并使用新的输出目录。

候选应用在受限 Docker 容器内运行，宿主执行外部 HTTP 与浏览器业务验收。评审或测试失败会进入有限修复；材料不足、次数耗尽或运行异常会保留相应失败状态。通过评审和规定验收后先停在 `waiting_approval`。

人工检查本次 `state.json`、源码、评审和验收证据后，才能针对当前 `review.revision` 批准。批准会重新验收并生成 `delivery-<revision>.zip`；正式服务仅启动已批准且校验有效的版本。恢复、批准、启动、独立 ZIP 使用及备份步骤见 [新产品开发指南](product-development-guide.md)。

固定看板练习使用 `demo/run_dev_team.py --scenario buggy --step`，重点是评审与修复已有代码。它与新需求生成共用开发团队入口，课堂操作见 [Review 实战手卡](dev-team-demo-guide.md)。

## 7. 维护、验证与打包

维护课件后重新构建，并运行与变更相关的检查。以下命令不调用真实模型：

```powershell
.\.venv\Scripts\python.exe build.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_collaboration_import.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_collaboration_live.py
.\.venv\Scripts\python.exe tools/verify_local_links.py
.\.venv\Scripts\python.exe tools/check_git_files.py
.\.venv\Scripts\python.exe tools/verify_source_checkout.py
```

`verify_local_links.py` 检查文档和课件的本地链接；如提示缺少 `dist/collaboration-demo.zip`，先运行下面的协作包打包命令。`check_git_files.py` 检查提交候选及已跟踪文件是否符合项目规则；`verify_source_checkout.py` 在临时目录复制允许提交的源码，再验证课件可重建、协作 CLI 可启动。

开发团队回归使用 `.venv-metagpt`，部分测试会实际运行 Docker 和浏览器，需要先准备对应环境。浏览器 UI 回归在 `tests/*.test.cjs`，例如 `node --test tests/speaker_notes_ui.test.cjs`；Playwright 安装在其他目录时可通过 `PLAYWRIGHT_MODULE` 指定。

```powershell
# 生成并验证可独立运行的五模式协作包
.\.venv\Scripts\python.exe tools/package_collaboration.py
.\.venv\Scripts\python.exe tools/verify_collaboration_package.py

# 生成完整培训包
.\.venv\Scripts\python.exe build.py --package
```

培训包和协作包输出到 `dist/`。产品 ZIP 在对应产品运行目录内，由版本审批流程生成。

源码、手写文档、测试、配置模板和必要输入资料提交 Git；虚拟环境、密钥、本机模型配置、生成课件、运行记录、测试结果与分发包保持本地。提交时仅暂存当前项目的相关文件，详见 [Git 文件管理](git-management.md)。

## 8. 使用范围与进一步阅读

本项目交付的是培训材料和本地单机开发实战。Docker、宿主用户、需求与验收作者属于可信边界；示例角色令牌用于演练。集中身份认证、远程部署、生产备份服务和任意框架内部步骤恢复需要另行实现。

已有库存和预约的真实生成、修复与独立交付验证记录，但这些结果仅覆盖对应需求和环境。新任务仍需检查本次证据、明确批准当前版本。

| 需要了解的内容 | 文档 |
| --- | --- |
| 课程安排与逐页讲解 | 构建后的 [大纲](outline.md)、[讲师讲稿](speaker-notes.md) |
| 目录定位 | [目录说明](directory-guide.md) |
| 模型配置与本地运行 | [模型演示指南](model-demo-guide.md) |
| 五种模式源码、断点与课堂节奏 | [协作演示指南](collaboration-demo-guide.md) |
| 框架介绍 | [框架演示手卡](framework-demo-guide.md) |
| 新产品需求、恢复、审批与交付 | [新产品开发指南](product-development-guide.md) |
| 开发团队设计 | [开发设计](dev-team-design.md) |
| 已有产品验证的范围与证据 | [整改与验证记录](product-remediation-verification-2026-10-10.md) |
| 资料来源 | [来源说明](sources.md) |
