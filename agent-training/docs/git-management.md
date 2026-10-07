# Git 文件管理

本项目位于上层 `N5Share` Git 仓库的 `agent-training/` 子目录。以下规则仅覆盖当前项目，其他项目有自己的文件与提交范围。

| 类别 | 位置 | 是否提交 |
| --- | --- | --- |
| 课件生成源码 | course/、web/、build.py | 提交 |
| 真实模型演示与公共服务 | demo/，旧规则源码在 demo/reference/ | 提交 |
| 测试与维护工具 | tests/、tools/ | 提交 |
| 手写培训说明 | docs/，排除生成的大纲与讲稿 | 提交 |
| 输入资料与静态参考 | assets/、archive/2026-10-07-before-collaboration-import/ | 提交，课程构建及迁移检查需要这些文件 |
| 配置模板、依赖、启动脚本 | config/.env.example、requirements.txt、start-*.cmd | 提交 |
| 共用 VS Code 配置 | .vscode/launch.json、extensions.json、settings.json | 提交，使用工作区相对路径 |
| 生成课件、大纲与讲稿 | index.html、docs/outline.md、docs/speaker-notes.md | 不提交，运行 build.py 生成 |
| 运行记录、检查截图、分发包 | demo/output/、test-results/、dist/ | 不提交 |
| 旧生成示例与工作记录 | archive/generated-examples/、archive/work-notes/ | 不提交，本机保留 |
| 本机凭据与环境 | deepseek.config、.env、DPAPI 文件、.venv/、.langgraph_api/ | 不提交 |

仓库中新克隆的副本需安装 requirements.txt，再运行 `python build.py` 生成可打开的课件、大纲与讲稿。演示代码直接在 VS Code 中运行。分发 ZIP 位于 dist/，作为发布附件分享。

配置模板只列变量名称，程序读取进程环境；它不自动加载 .env 文件。实际 DeepSeek 凭据继续使用已有本机存储或环境变量，OpenAI/Codex 备用使用 CCSwitch。

## 提交前检查

在 agent-training 目录执行：

```powershell
.\.venv\Scripts\python.exe tools/check_git_files.py
.\.venv\Scripts\python.exe tools/verify_source_checkout.py
git status --short -- .
git diff -- .
git diff --cached -- .
git ls-files --cached --ignored --exclude-standard -- .
```

最后一条命令应为空。`.gitignore` 只影响未跟踪文件；已跟踪的产物需用 `git rm --cached` 从索引移除，本机文件仍可保留。此操作不会清理此前提交的历史。

verify_source_checkout.py 将允许提交的文件复制到临时空目录，再构建课件并检查真实演示入口，验证生成课件和旧运行记录不进入仓库时仍可复现。该检查不调用真实模型。

核对改动后，只暂存当前项目：

```powershell
git add -A -- .
.\.venv\Scripts\python.exe tools/check_git_files.py
git diff --cached --stat -- .
```

不要在上层仓库根目录直接暂存全部项目。提交说明应围绕实际功能与目录迁移描述；目录移动在暂存后由 Git 根据内容识别重命名。

`.gitattributes` 统一源码为 LF，Windows 启动脚本为 CRLF，图片、PDF 与 ZIP 按二进制处理。它防止启动脚本因换行格式而失效。
