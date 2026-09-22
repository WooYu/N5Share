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
