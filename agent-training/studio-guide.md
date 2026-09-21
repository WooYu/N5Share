# LangSmith Studio 对比演示

[打开 Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024) · [打开原课件](http://127.0.0.1:8765/#11)

Studio 使用本机 `127.0.0.1:2024` 的官方 LangGraph Agent Server。它和原课件的 `8765` 服务可以同时运行。云端追踪默认关闭；不需要把模型密钥填入 Studio。

## 启动

本机已安装依赖。以后双击 `start-studio.cmd` 即可启动服务并打开 Studio，保持该窗口运行。

首次在新环境安装时，在仓库根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r agent-training/requirements-studio.txt
```

然后运行 `agent-training/start-studio.cmd`。本机验证环境为 Windows、Python 3.14、LangGraph 1.2.11、CLI 0.4.31 和 Agent Server 0.14.3。使用 `langgraph dev`，不需要 Docker。

如果 Studio 提示未连接，先确认本地服务窗口仍在运行，再检查连接地址是否为 `http://127.0.0.1:2024`。服务接口文档位于 [API Docs](http://127.0.0.1:2024/docs)。

## 两个可直接比较的图

在 Studio 左上角选择：

| 图 | 重点观察 |
| --- | --- |
| `outing_react` | `prepare` 建立任务；`decide` 请求真实模型；`call_tools` 实际执行工具；`verify` 验收结果。证据不足时回到决策节点 |
| `outing_supervisor` | 主管生成分工；天气与费用角色分别调用模型、使用独立上下文；`review_gate` 可暂停检查；`summarize` 汇总；`verify` 程序验收 |

这两个图把执行步骤拆成真正的 LangGraph 节点，便于查看每个节点前后的状态。它们复用原课件的模型适配器、合成工具、角色提示与结果校验。Supervisor 示例按主管选定的先后顺序执行两个专业角色，没有宣称并行运行。

## 推荐输入

在 Input 区点 **View Raw**，输入 JSON，再点 **Submit**：

```json
{
  "weather": "rain",
  "budget": 300,
  "model_source": "configured",
  "max_model_calls": 12,
  "pause_before_summary": false
}
```

- `weather`：`rain` / `sun`，均为合成天气。
- `budget`：`100` / `200` / `300`，包含两大一小的门票、交通和餐费。
- `model_source`：`configured` 与课件一致，优先 CCSwitch，必要时明确切换 DeepSeek 备用。也可以主动选择 `deepseek`，单独比较 DeepSeek 的响应。
- `max_model_calls`：1–12，失败尝试也计数。
- `pause_before_summary`：仅 Supervisor 使用。设为 `true`，两个专业角色完成后暂停；恢复值为 JSON 布尔值 `true` 时继续汇总，为 `false` 时结束。

同一条件下，雨天 300 元应有城市博物馆 210 元这一可行候选；雨天 200 元应判断现有候选无解。模型措辞和调用顺序可以不同。

## 怎么看效果

1. 先运行 `outing_react`，看模型何时查天气、何时核算费用，以及循环如何结束。
2. 点击运行步骤查看 `trace.shared_state.observations`、`trace.metrics` 和 `trace.events`，核对工具结果和模型调用次数。
3. 换到 `outing_supervisor`，将 `pause_before_summary` 设为 `true`。暂停后查看 `trace.shared_state.messages`，比较天气和费用角色各自交付的内容。
4. 用 `true` 恢复后，确认从汇总节点继续，已完成的角色不会重新调用。
5. 将预算改为 200 元，用 **New Thread** 新建一次运行，对比可行与无解两条路径。

| 原课件 | Studio |
| --- | --- |
| 中文讲解、按教学顺序展示每一步 | 展示实际图结构与节点执行 |
| 适合投影、解释机制 | 适合开发者查看状态、断点与恢复 |
| 导出单次轨迹 JSON | 在本地线程中保留节点检查点，查看历史状态 |

## 本地记录和模型用量

执行和检查点保存在本机，`LANGSMITH_TRACING=false`，未开启 LangSmith 云端追踪。Studio 的页面由 LangSmith 提供，浏览器直接连接本地 Agent Server。顶部缺少 LangSmith API Key 的提示意味着云端运行追踪未启用，不妨碍本地 Graph / Interact 功能；Trace、云端实验或数据集等功能不属于本次演示。

每次提交仍会真实调用模型并产生供应商用量。凭据沿用 CCSwitch 和 Windows DPAPI 本地存储，不进入图状态、检查点、Git 或培训包。本地 `.langgraph_api` 目录也排除在版本库和培训包之外。演示没有部署到云端，结束时可关闭 Studio 服务窗口。

参考：[Studio 本地接入](https://docs.langchain.com/langsmith/quick-start-studio)、[Agent Server 本地开发](https://docs.langchain.com/langsmith/local-dev-testing)。
