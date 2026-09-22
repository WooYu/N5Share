# 三框架实操手册

## 先跑同一条发布检查，再比较编排方式

这份手册面向已经会写服务、客户端和测试的开发者。目标是跑起一个最小例子，看见状态、消息和产物如何流转，然后决定项目是否值得引入框架。投影片 P33–35 是关键代码节选，下面的源文件是完整程序。

所有示例默认读取同一份合成资料，不访问真实仓库、数据库、CI 或模型服务，也不需要密钥。LangGraph 使用普通函数节点；AutoGen 使用官方 ReplayChatCompletionClient 回放一次工具调用；MetaGPT 使用自定义确定性 Action。运行框架成功，只证明接口和编排接通，不能证明模型更聪明或缺陷检出率更高。

## 1. 统一输入、输出和验收

```text
head_sha: release-b
删除 totalAmount；线上客户端仍读取它
迁移删列；缺少兼容迁移方案
CI: passed=true，但 head_sha=release-a

预期 status: COMPLETED
预期 decision: BLOCK
findings: API_BREAK、DB_DROP
missing_evidence: release-b 的 CI 证据
```

status 描述检查任务是否执行完；decision 描述业务上是否建议发布。发现阻断项仍是一次正常完成的检查。已有明确阻断项且同时缺证据时，保留 BLOCK 和缺口。只有缺证据则 NEEDS_EVIDENCE；全齐且无阻断才 READY_FOR_MANUAL_REVIEW。模型或框架说“完成”不能越过这个规则函数。

## 2. 在独立环境运行

在课件目录打开终端。运行前两种示例时使用 Python 3.10+；这里的验证环境为 Python 3.13。首次安装需要网络；安装后以下回放不联网、不消耗模型 token。不要把框架依赖装进正在使用的真实演示服务环境。

```powershell
python -m venv .framework-venv
.\.framework-venv\Scripts\python.exe -m pip install -r labs/requirements.txt
.\.framework-venv\Scripts\python.exe labs/common.py
.\.framework-venv\Scripts\python.exe labs/langgraph_release.py blocked
.\.framework-venv\Scripts\python.exe labs/autogen_release.py blocked
```

把最后一个参数改为 missing 或 ready，分别验证“只有旧 CI”和“证据齐备”。程序把轨迹和结果输出到终端；需要留存时在命令末尾添加 > result.txt。直接运行 common.py 得到不用框架的基线。

## 3. LangGraph：把分支写成可观察的状态图

ReleaseState 是输入和运行状态；collect 节点读取三类资料并产出报告；release_route 调用宿主规则，选择 block、missing 或 allow 节点；stream(stream_mode="updates") 输出每一步增量。把 TypedDict 类比 DTO，把 node 类比处理函数，把 edge 类比状态机转移。

## 本次验证记录

Python 3.13 独立环境实测：LangGraph 1.2.12 与 AutoGen AgentChat / Ext 0.7.5 均通过 blocked、missing、ready 三情景，共 6 次框架运行；结果与普通脚本基线一致，伪造空报告被宿主拒绝。MetaGPT 已核对官方 API 并检查语法，本机 Python 3.13 不在其支持范围，未执行。所有样本为确定性回放，真实模型质量、速度与成本均未测。

```text
blocked: collect → block → END
missing: collect → missing → END
ready:   collect → allow → END
```

适合：业务必须明确分支、回路、暂停与状态边界。这个示例没有配置 checkpointer，因此没有证明重启恢复。生产使用时要选存储、设置 thread_id、验证恢复与副作用幂等；普通函数完全能做好的检查，也无需为了框架而调用模型。

### LangGraph 完整程序

文件：labs/langgraph_release.py

```python
"""Run: python labs/langgraph_release.py [blocked|missing|ready]. No LLM calls."""
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from common import collect_reports, evaluate, sample, show


class ReleaseState(TypedDict, total=False):
    source: dict
    reports: list[dict]
    result: dict


def collect_findings(state: ReleaseState):
    return {"reports": collect_reports(state["source"])}


def release_route(state: ReleaseState):
    return evaluate(state["reports"], state["source"])["decision"]


def mark_block(state: ReleaseState):
    return {"result": evaluate(state["reports"], state["source"])}


def mark_allow(state: ReleaseState):
    return {"result": evaluate(state["reports"], state["source"])}


def mark_missing(state: ReleaseState):
    return {"result": evaluate(state["reports"], state["source"])}


def build_graph():
    graph = StateGraph(ReleaseState)
    graph.add_node("collect", collect_findings)
    graph.add_node("block", mark_block)
    graph.add_node("allow", mark_allow)
    graph.add_node("missing", mark_missing)
    graph.add_edge(START, "collect")
    graph.add_conditional_edges("collect", release_route, {
        "BLOCK": "block", "READY_FOR_MANUAL_REVIEW": "allow", "NEEDS_EVIDENCE": "missing"})
    for target in ("block", "allow", "missing"):
        graph.add_edge(target, END)
    return graph.compile()


if __name__ == "__main__":
    source = sample(sys.argv[1] if len(sys.argv) > 1 else "blocked")
    for update in build_graph().stream({"source": source}, stream_mode="updates"):
        show(update)

```

## 4. AutoGen：角色轮流发消息，工具交付证据

make_agent 为每个角色建立独立工具闭包，传入对应职责的 evidence；AssistantAgent 注册 inspect 工具。回放客户端要求调用一次 inspect，由真实 AgentChat 运行时执行工具并发布 ToolCallSummaryMessage。RoundRobinGroupChat 按 compat → db → tests 发言。MaxMessageTermination(4) 包含用户任务加三份最终报告；工具事件默认不计入该消息数。

```text
TextMessage / user
compat: ToolCallRequest → ToolCallExecution → ToolCallSummary
db:     ToolCallRequest → ToolCallExecution → ToolCallSummary
tests:  ToolCallRequest → ToolCallExecution → ToolCallSummary
stop_reason: 达到消息上限
宿主再 evaluate(reports, source) → COMPLETED / BLOCK
```

固定顺序不需要模型选择下一位角色。RoundRobinGroupChat 共享团队对话上下文；它不是隐私或权限隔离边界，真正的工具授权仍由服务检查。停止原因仅说明对话停止，不能直接映射为业务通过。官方仓库现为维护模式，新项目应同时评估 Microsoft Agent Framework；示例用于理解现有 AutoGen 系统。

### AutoGen 完整程序

文件：labs/autogen_release.py

```python
"""Real AgentChat runtime, replay model + synthetic evidence tools. No API key needed."""
import asyncio
import json
import sys
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import FunctionCall
from autogen_core.models import CreateResult, RequestUsage
from autogen_ext.models.replay import ReplayChatCompletionClient
from common import ROLES, evaluate, read_evidence, sample, show


def make_agent(role, source):
    async def inspect() -> str:
        """Read synthetic, versioned evidence for this reviewer's responsibility."""
        return json.dumps(read_evidence(role, source), ensure_ascii=False)

    replay = ReplayChatCompletionClient([CreateResult(
        content=[FunctionCall(id=role + "-1", name="inspect", arguments="{}")],
        finish_reason="function_calls", usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
        cached=False)], model_info={"vision": False, "function_calling": True,
                                    "json_output": False, "family": "unknown",
                                    "structured_output": False})
    agent = AssistantAgent(role, model_client=replay, tools=[inspect],
                           reflect_on_tool_use=False,
                           system_message="调用 inspect 获取本角色报告，不修改工具证据。")
    return agent, replay


async def run(source):
    pairs = [make_agent(role, source) for role in ROLES]
    agents = [pair[0] for pair in pairs]
    # User task + 3 final role messages. Tool events are not counted by default.
    team = RoundRobinGroupChat(agents, termination_condition=MaxMessageTermination(4))
    try:
        result = await team.run(task=json.dumps(source, ensure_ascii=False))
        reports = []
        for message in result.messages:
            print(type(message).__name__ + " / " + message.source)
            if message.source in ROLES and type(message).__name__ == "ToolCallSummaryMessage":
                reports.append(json.loads(message.content))
        print("stop_reason: " + str(result.stop_reason))
        output = evaluate(reports, source)
        show(output)
        return output
    finally:
        for _, client in pairs:
            await client.close()


if __name__ == "__main__":
    asyncio.run(run(sample(sys.argv[1] if len(sys.argv) > 1 else "blocked")))

```

## 5. MetaGPT：用产物触发下一角色

CheckRelease 把输入变成带版本的审查产物；ReleaseReviewer 关注 UserRequirement。ReportWriter 只关注 CheckRelease 产生的消息，调用 PublishReport 验收后发布结果。Message.cause_by 声明产物由哪种 Action 产生，_watch 决定下游是否响应。SOP 是“审查 → 汇总”，不是让有职位名的模型自由聊天。

```text
UserRequirement
  → ReleaseReviewer / CheckRelease
  → Message(cause_by=CheckRelease, source + reports)
  → ReportWriter / PublishReport
  → COMPLETED / BLOCK
```

本机是 Python 3.13；MetaGPT 官方 README 要求 Python ≥3.9 且 <3.12。这段示例核对了官方 Action、Role、Team 接口并做语法检查，但尚未在受支持环境运行。上面的轨迹是预期结果，不能称为实测。采用它前，应在独立 Python 3.11 环境完成依赖安装和下面的三情景回放。

```powershell
# 将第一行路径替换为你已安装的 Python 3.11 路径
C:\Python311\python.exe -m venv .metagpt-venv
.\.metagpt-venv\Scripts\python.exe -m pip install metagpt==0.8.2
.\.metagpt-venv\Scripts\python.exe labs/metagpt_release.py blocked
.\.metagpt-venv\Scripts\python.exe labs/metagpt_release.py missing
.\.metagpt-venv\Scripts\python.exe labs/metagpt_release.py ready
```

MetaGPT 初始化可能读取其自身本机配置；此例 Action 不调用 _aask，不需要真实模型请求。若初始化仍要求模型配置，按官方配置指南设置后再运行，不能凭本例宣称开箱即用。复杂依赖、产物格式校验和失败重审都是选型成本。

### MetaGPT 完整程序（未执行验证）

文件：labs/metagpt_release.py

```python
"""MetaGPT SOP example; use a separate Python 3.11 environment. No LLM calls.

Official Action / Role / Team API checked. Runtime NOT verified on this Python 3.13 host.
"""
import asyncio
import json
import sys
from metagpt.actions import Action, UserRequirement
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from common import collect_reports, evaluate, sample, show


class CheckRelease(Action):
    name: str = "CheckRelease"

    async def run(self, source: dict) -> str:
        return json.dumps({"source": source, "reports": collect_reports(source)}, ensure_ascii=False)


class PublishReport(Action):
    name: str = "PublishReport"

    async def run(self, artifact: str, target: dict) -> str:
        data = json.loads(artifact)
        if data["source"] != target:
            raise ValueError("Artifact cannot replace the original task input")
        return json.dumps(evaluate(data["reports"], target), ensure_ascii=False)


class ReleaseReviewer(Role):
    name: str = "Reviewer"
    profile: str = "ReleaseReviewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckRelease])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        source = json.loads(self.rc.news[-1].content)
        artifact = await self.rc.todo.run(source)
        return Message(content=artifact, role=self.profile, cause_by=type(self.rc.todo))


class ReportWriter(Role):
    name: str = "Writer"
    profile: str = "ReportWriter"
    target: dict

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([PublishReport])
        self._watch([CheckRelease])

    async def _act(self) -> Message:
        result = await self.rc.todo.run(self.rc.news[-1].content, self.target)
        show(json.loads(result))
        return Message(content=result, role=self.profile, cause_by=type(self.rc.todo))


async def main():
    target = sample(sys.argv[1] if len(sys.argv) > 1 else "blocked")
    team = Team()
    team.hire([ReleaseReviewer(), ReportWriter(target=target)])
    team.run_project(json.dumps(target))
    await team.run(n_round=3)


if __name__ == "__main__":
    asyncio.run(main())

```

## 6. 如何换成真实模型

先保留 read_evidence 与 evaluate。LangGraph：把 collect 内一个报告函数换成“读取证据 → 调模型 → 校验 JSON → 返回报告”；控制图和宿主验收不变。AutoGen：把 ReplayChatCompletionClient 换成兼容的 ChatCompletionClient，为 inspect 提供原始证据，要求模型产出结构化 ReviewReport，再由宿主校验。MetaGPT：在 CheckRelease.run 中调用 _aask(prompt)，将响应校验成审查产物，保持 cause_by 与版本字段。不要直接把自然语言报告当作发布许可。

模型连接配置由服务端管理。一次真实尝试至少限制总模型次数、总工具次数和墙钟时长，支持明确取消，完整记录重试成本。这里未对三框架做真实模型质量或速度评测；原课件的 DeepSeek 真实模式是自写运行时，不能当作三框架的测试结果。

## 7. Java、Android、前端怎样接

建议由 Java API 负责会话鉴权、仓库访问校验、冻结目标版本和任务记录，编排服务在内部运行框架。对客户端返回稳定 DTO。以下是发布检查助手的接口设计示例，未加入本课现有 /api/runs 出游接口。

```text
POST /api/release-checks
  {repoId, baseSha, headSha, artifactSha256, variant}
  → 202 {runId, status:"RUNNING"}
GET /api/release-checks/{runId}
  → {runId, status, decision, completedRoles, findings, missingEvidence}
POST /api/release-checks/{runId}/cancel
  → {runId, status:"CANCELLED"} 或已先完成的实际终态
```

前端组件卸载、AbortController.abort()、Android Activity 重建或停止收集 Flow，都只改变客户端观察。需要业务取消时发送 cancel 请求，并读取服务端终态；超时只表示结果未知。保留 runId 以便重新订阅，丢弃旧任务响应；若需要跨进程恢复，必须设计客户端与服务端持久化。Android 同一提交也可能有不同变体或安装包，证据还应绑定 artifactSha256、variant 和约定设备/API 环境。

## 8. 效果怎么评，不凭演示判断

先比较三种方案：固定规则基线、单 Agent、必要分工的多 Agent。固定任务集、模型、资料、token/工具预算与验收规则，每个真实模型情景重复运行并保留失败，别只挑成功截图。框架主要提供组织与运行控制；查得更准依赖模型、工具资料和契约，不能从框架名推导。

```text
固定样本组：可通过、已知阻断、缺CI、错SHA、角色超时、重复报告、取消
质量：命中已知阻断 / 漏报 / 误报；无证据的“通过”次数
可靠性：是否正确终止；取消确认后新工具调用数；重复/旧报告是否被拒绝
代价：总延迟 p50/p95、全部模型/工具次数、输入/输出token、人工复核分钟
公平性：包含主管调度和重试开销；真实模型至少多次重复，报告样本量
结论：质量未改善而代价增加，优先减少角色或回到工作流
```

## 9. 共享工具与宿主验收源码

这份实现专门针对三个固定样本，不是通用风险识别引擎。生产实现还需要严格 schema、身份与任务绑定、消息去重、工具证据来源验证，以及取消和超限的终态保护。

### 共享样本、三角色报告与 evaluate

文件：labs/common.py

```python
"""Shared synthetic release fixture. No model, repository, database or CI is called."""
import json
import sys
from copy import deepcopy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

release_input = {
    "head_sha": "release-b",
    "removed_fields": ["totalAmount"],
    "client_fields": ["totalAmount"],
    "migration": {"drops_column": True, "compatibility_plan": False},
    "ci": {"head_sha": "release-a", "passed": True},
}
ROLES = ("compat", "db", "tests")


def read_evidence(role: str, source: dict) -> dict:
    """Deterministic classroom tool: return a versioned report from fixture facts."""
    findings, missing = [], []
    if role == "compat":
        used = sorted(set(source["removed_fields"]) & set(source["client_fields"]))
        if used:
            findings.append({"id": "API_BREAK", "evidence": "fixture:client_fields",
                             "detail": "仍在使用的字段被删除：" + ",".join(used)})
    elif role == "db":
        if source["migration"]["drops_column"] and not source["migration"]["compatibility_plan"]:
            findings.append({"id": "DB_DROP", "evidence": "fixture:migration",
                             "detail": "删列但未提供兼容迁移方案"})
    elif role == "tests":
        if source["ci"]["head_sha"] != source["head_sha"]:
            missing.append("当前提交的 CI 证据；现有证据属于 " + source["ci"]["head_sha"])
        elif not source["ci"]["passed"]:
            findings.append({"id": "CI_FAILED", "evidence": "fixture:ci", "detail": "当前提交 CI 失败"})
    else:
        raise ValueError("Unknown role")
    return {"role": role, "head_sha": source["head_sha"], "findings": findings,
            "missing_evidence": missing}


def collect_reports(source: dict) -> list[dict]:
    return [read_evidence(role, source) for role in ROLES]


def evaluate(reports: list[dict], source: dict) -> dict:
    """The host owns this gate. Framework termination alone is not acceptance."""
    if not isinstance(reports, list) or any(not isinstance(r, dict) for r in reports):
        raise ValueError("Reports must be structured objects")
    if len(reports) != 3 or {r["role"] for r in reports} != set(ROLES):
        raise ValueError("Three distinct role reports required")
    if any(r["head_sha"] != source["head_sha"] for r in reports):
        raise ValueError("Report does not belong to target commit")
    # This small fixture has exact tool-grounded answers. In production verify
    # evidence references and domain rules instead of trusting model conclusions.
    for report in reports:
        if report != read_evidence(report["role"], source):
            raise ValueError("Report differs from trusted fixture evidence")
    findings = [item for report in reports for item in report["findings"]]
    missing = [item for report in reports for item in report["missing_evidence"]]
    decision = "BLOCK" if findings else "NEEDS_EVIDENCE" if missing else "READY_FOR_MANUAL_REVIEW"
    return {"status": "COMPLETED", "decision": decision, "head_sha": source["head_sha"],
            "findings": findings, "missing_evidence": missing}


def sample(name="blocked") -> dict:
    source = deepcopy(release_input)
    if name in {"ready", "missing"}:
        source["removed_fields"] = []
        source["migration"]["compatibility_plan"] = True
    if name == "ready":
        source["ci"]["head_sha"] = source["head_sha"]
    return source


def show(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    for case in ("blocked", "missing", "ready"):
        source = sample(case)
        show({"case": case, "baseline": evaluate(collect_reports(source), source)})

```

## 10. 官方依据（2026-09-23 核对）

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [AutoGen Teams](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html)
- [AutoGen ReplayChatCompletionClient](https://microsoft.github.io/autogen/stable/reference/python/autogen_ext.models.replay.html)
- [AutoGen 维护声明](https://github.com/microsoft/autogen)
- [MetaGPT Multi Agent 101](https://docs.deepwisdom.ai/main/en/guide/tutorials/multi_agent_101.html)
- [MetaGPT Python 版本要求](https://github.com/FoundationAgents/MetaGPT)
