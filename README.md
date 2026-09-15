# N5Share · Agent 推理与协作培训

32 页中文 HTML 演示稿，配套讲师讲稿、Python 双角色协作 Demo 与练习，建议培训时长 90 分钟。

## 培训内容

- **ReAct（重点）**：Thought–Action–Observation 循环、工具调用、运行轨迹、错误处理与终止。
- **Plan-and-Execute + Reflexion**：任务规划、失败反馈、反思记忆与计划修订。
- **多 Agent 协作**：Supervisor、层次化、Swarm、消息协议与共享状态。
- **框架选型**：AutoGen / MetaGPT / LangGraph。
- **现场 Demo**：规划与执行角色协作分析订单 CSV，演示失败、修订和结果验收。

## 使用入口

- [HTML 演示稿](agent-training/index.html)：下载后用浏览器打开，支持离线使用、翻页、全屏、目录与讲师备注。
- [讲师讲稿](agent-training/speaker-notes.md)
- [运行说明与练习](agent-training/README.md)
- [参考资料](agent-training/sources.md)
- [完整培训包 ZIP](Agent-Training-HTML-Demo.zip)

GitHub 文件页面显示 HTML 源码；下载到本地或启动下面的服务即可查看演示效果。

## 启动现场 Demo

需要 Python 3.10+，默认模式仅使用标准库。

```bash
git clone https://github.com/WooYu/N5Share.git
cd N5Share/agent-training
python demo/server.py
```

浏览器打开 http://127.0.0.1:8765，跳到第 29 页运行 Demo。

```bash
# 命令行演示失败修正
python demo/agents.py --inject-failure

# 运行测试
python -m unittest discover -s demo -v

# 修改 content.py 或 template.html 后重新构建演示稿
python build.py
```

默认模式使用规则模拟规划与执行决策，真实执行 CSV 读取、计算、错误反馈和独立校验。可选 Ollama 模式需要自行配置本地模型；交付时没有完成真实模型端到端验证。详见运行说明。

教学数据为合成样本。框架资料核对日期为 2026-09-10；AutoGen 维护状态等信息请在培训前再次查看官方来源。
