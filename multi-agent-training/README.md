# 多Agent协同：可运行实训版

基于 `sources/01_标准化文档.md` 和 `sources/04_HTML演示文档.html` 整理。

先阅读 `培训讲义.md`。本版包含两条路线：

| 路线 | 入口 | 条件 | 验证状态 |
|---|---|---|---|
| 离线演练 | 双击 `一键离线演练.cmd`，或 `node run.mjs --mode sequential` | Node.js 22+，不需要额外包和账号 | 本机已实测 |
| Node.js 真模型 | `node run.mjs --mode supervisor --live` | 环境变量 `DEEPSEEK_API_KEY`，可连接 DeepSeek API | 尚未真实调用 |
| Python 原框架 | `python/labs.py` | Python 3.12+、依赖和 DeepSeek Key | 本机 Python 3.13 已安装依赖，Supervisor 已完成真实模型调用；其他实验待验证 |
| MCP 本地连接 | `python/mcp_client.py` | Python 和 MCP SDK，不需要模型账号 | 待 Python 环境验证 |

离线演练是固定规则模拟，用于观察控制流，**不代表真实大模型推理，也没有执行互联网搜索**。Python 路线使用 LangGraph、Supervisor、Swarm 和 AutoGen；Node.js 路线是便于课堂启动的辅助演练，不使用这些框架。

## 立即运行

在本文件所在目录打开 PowerShell：

```powershell
node --version
node run.mjs --mode sequential
node run.mjs --mode supervisor
node run.mjs --mode hierarchical
node run.mjs --mode swarm
node run.mjs --mode network
node run.mjs --mode devteam
node run.mjs --mode security
node --test tests.mjs
```

结果保存在 `outputs`。`devteam` 默认停在评审后，尚未运行 tester。

```powershell
node run.mjs --mode devteam --approve
```

Node.js 的 `--approve` 会重新运行本次流程并允许测试角色发言，不读取上一轮检查点。Python 的 `--approve` 会在同一进程中从检查点恢复，详见讲义。

## VS Code 演示 Supervisor

用 VS Code 打开 `supervisor-demo.code-workspace`，选择“终端 > 运行任务”：

- `Supervisor: Check`：仅构图，不调用 API。
- `Supervisor: Live trace`：默认使用紧凑演示视图，分角色显示交接、工具调用、来源数量、字符数和报告文件名。缺少 Key 时在终端隐藏输入，仅供本次进程使用。
- `Supervisor: Detailed trace`：展开角色发言与工具参数摘要，适合排查。
- `Supervisor: Replay`：逐步回放 `outputs/python/supervisor.json`，不调用模型、不执行工具、不修改报告。终端会明确显示 `REPLAY`。

任务入口不需要 Python 扩展。安装工作区推荐的 Python 和 Python Debugger 扩展后，可在“运行和调试”选择 `Supervisor: Live trace (F5)` 并按 F5。在 `python/common.py` 的三个工具函数内打断点，可以检查真实调用参数；回放不会触发这些断点。

也可以在集成终端运行：

```powershell
.\.venv\Scripts\python.exe -u -X utf8 .\python\labs.py --lab supervisor --trace --ask-key
.\.venv\Scripts\python.exe -u -X utf8 .\python\labs.py --replay
```

紧凑视图收起报告正文和完整语料；终端支持时，角色标题和错误会使用不同颜色。`AUTO RETURN` 表示框架自动把控制权交回主管。加上 `--trace-details` 可展开日志，完整结果仍保存在 JSON 和报告文件。`ERROR` 表示实际工具调用失败，即使后续恢复也会保留该事件；进程退出成功不等于每次工具调用成功。不要在共享屏幕上打开含 Key 的 `.env` 文件。

## 文件

| 文件 | 用途 |
|---|---|
| `培训讲义.md` / `培训讲义.docx` | 完整培训文档及 Word 版本 |
| `run.mjs` | 离线 / DeepSeek 实验入口 |
| `tests.mjs` | 10 项离线验收检查 |
| `一键离线演练.cmd` | Windows 双击入口 |
| `data/corpus.json` | 从原材料改写的本地教学资料，无市场数据 |
| `python/common.py` | 模型配置与六个工具 |
| `python/labs.py` | 七个 Python 框架实验 |
| `python/mcp_server.py` / `python/mcp_client.py` | 本地 MCP 服务与客户端 |
| `python/requirements.txt` | 已在本机安装的兼容范围；具体版本记录在本地 `python/requirements.lock.local.txt` |
| `python/execution_trace.py` | 实时图事件日志与历史记录回放 |
| `supervisor-demo.code-workspace` / `.vscode` | VS Code 演示任务与 F5 调试配置 |
| `验证报告.md` | 实测证据与剩余限制 |
| `export-docx.ps1` | 从 Markdown 重新生成 Word 文档 |

真实模型调用会消耗账号额度。Key 只放本机环境变量或 `python/.env`，不写入讲义、日志和压缩包。
