# 培训目录说明

项目根目录：`E:\Code_Tool\AgentShare\N5Share\agent-training`。VS Code 打开这个文件夹，所有命令从这里执行。

```text
agent-training/
  index.html                   可直接打开的课件
  README.md                    项目入口与导航
  build.py                     构建课件、大纲、讲稿
  requirements.txt             演示依赖
  start-*.cmd                  Windows 启动入口
  deepseek.config              本机模型配置
  .vscode/                     F5 运行配置与扩展建议
  demo/
    run_collaboration.py       五模式真实演示入口
    collaboration_live/        完整 LangGraph 模式、角色与工具
    model_*.py                 DeepSeek 主用、OpenAI/Codex 备用
    server.py                  前七种架构的真实模型服务入口
    reference/                 旧规则示例源码，仅作参考
    output/                    本机真实运行记录
  course/                      课程生成源码
  web/                         模板、CSS、浏览器脚本
  docs/                        培训指南、大纲、讲稿、来源
  config/                      配置模板，不含本机凭据
  tests/                       回归检查与测试导入配置
  tools/                       打包和交付检查
  assets/                      参考资料、图形、PDF
  dist/                        ZIP 分发产物
  archive/                     历史输入快照、工作记录、迁移清单
    generated-examples/        本机旧示例轨迹，不提交
  test-results/                检查日志与截图
```

## 常用入口

- [主课件](../index.html)
- [五种协作模式运行指南](collaboration-demo-guide.md)
- [框架演示手卡](framework-demo-guide.md)
- [讲师讲稿](speaker-notes.md) / [培训大纲](outline.md)
- [真实演示入口](../demo/run_collaboration.py)
- [可分享演示包](../dist/collaboration-demo.zip)
- [Git 文件管理](git-management.md)

## 维护命令

```powershell
.\.venv\Scripts\python.exe build.py
.\.venv\Scripts\python.exe demo/run_collaboration.py --check-model
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_*.py
.\.venv\Scripts\python.exe tools/package_collaboration.py
.\.venv\Scripts\python.exe tools/verify_collaboration_package.py
.\.venv\Scripts\python.exe tools/verify_local_links.py
.\.venv\Scripts\python.exe tools/check_git_files.py
```

修改课件请编辑 `course/` 与 `web/` 后运行 build.py，生成结果为根目录 index.html 和 docs/ 下的大纲、讲稿。真实演示独立维护在 demo/，F5 的入口使用 demo/run_collaboration.py。浏览器检查需要 Playwright 与 Chrome，测试文件位于 tests/。

构建完整培训包用 `python build.py --package`，产物位于 dist/。index.html、docs/outline.md、docs/speaker-notes.md、dist/、test-results/、demo/output/、archive/work-notes/ 与 archive/generated-examples/ 为本机生成或工作目录，不提交 Git。首次克隆后运行构建即可生成课件。旧生成示例移入 archive/generated-examples/，用于构建和测试的历史课件快照继续提交。原始迁移清单见 [文件迁移记录](../archive/2026-10-08-directory-organization.json)。
