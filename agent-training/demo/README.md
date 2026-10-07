# 演示代码入口

五种协作模式的主线源码在 [collaboration_live/](collaboration_live/)，入口为 [run_collaboration.py](run_collaboration.py)。用 VS Code 打开项目根目录，按 F5 选择“真实协作”配置。

```powershell
.\.venv\Scripts\python.exe demo/run_collaboration.py --pattern supervisor --scenario missing --step
```

model_backup.py 与 model_gateway.py 负责 DeepSeek 主配置和现有 OpenAI/Codex 备用。server.py 与 outing_live.py 用于前七种架构的真实演示。agents.py 与 fixtures.json 是保留的诊断仿真服务。

旧五模式规则示例在 reference/，用于历史教学和回归检查。历史生成轨迹保留在 archive/generated-examples/，不提交 Git；本次真实运行记录写入 demo/output/。

详见 [运行指南](../docs/collaboration-demo-guide.md) 与 [Git 文件管理](../docs/git-management.md)。
