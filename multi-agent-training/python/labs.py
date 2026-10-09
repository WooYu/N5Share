"""Complete framework labs adapted from the original training document."""
import argparse
import asyncio
import getpass
import hashlib
import json
import os
import sys
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph_swarm import create_handoff_tool, create_swarm
from pydantic import BaseModel

from common import OUTPUT, analyze_tool, code_tool, design_tool, make_model, search_tool, test_tool, write_tool
from execution_trace import ConsoleTrace, redact, replay_trace, run_with_trace


def worker(model, name, tools, prompt):
    return create_react_agent(model, tools=tools, name=name, prompt=prompt)


def build_sequential(model):
    class ContentState(TypedDict):
        topic: str
        sources: str
        outline: str
        draft: str
        final_content: str
        seo_content: str

    def research(state):
        return {"sources": search_tool.invoke({"query": state["topic"]})}

    def stage(input_key, output_key, instruction):
        def node(state):
            response = model.invoke([HumanMessage(
                content=f"{instruction}\nTopic: {state['topic']}\nInput: {state[input_key]}"
            )])
            return {output_key: response.content}
        return node

    graph = StateGraph(ContentState)
    graph.add_node("research", research)
    graph.add_node("outline", stage("sources", "outline", "Generate an outline; keep source IDs."))
    graph.add_node("draft", stage("outline", "draft", "Write a short Chinese draft based only on the outline."))
    graph.add_node("editor", stage("draft", "final_content", "Edit the draft; do not invent facts."))
    graph.add_node("seo", stage("final_content", "seo_content", "Return the final Chinese report plus keywords."))
    graph.add_edge(START, "research")
    for previous, following in [("research", "outline"), ("outline", "draft"),
                                ("draft", "editor"), ("editor", "seo")]:
        graph.add_edge(previous, following)
    graph.add_edge("seo", END)
    return graph.compile(name="sequential")


def build_supervisor(model):
    agents = [
        worker(model, "researcher", [search_tool], (
            "Your role is research only. Call search_tool, summarize the local findings with source IDs, "
            "then return to the supervisor. Other workers perform analysis and writing. "
            "You cannot transfer to workers or save files; do not attempt those tools."
        )),
        worker(model, "analyst", [analyze_tool], (
            "Your role is analysis only. Call analyze_tool on the research findings in the conversation, "
            "summarize the results with source IDs, then return to the supervisor. "
            "Do not fabricate market statistics, write the final report or transfer to other workers."
        )),
        worker(model, "writer", [write_tool], (
            "Use the research findings and analysis in the conversation to write a short Chinese report "
            "with source IDs. You MUST call write_tool with the report content. "
            "Only after the tool succeeds, return the saved path to the supervisor."
        )),
    ]
    return create_supervisor(agents=agents, model=model, output_mode="full_history", include_agent_name="inline", prompt=(
        "You are the sole coordinator; only you can transfer to other workers. "
        "Complete these steps in order: transfer_to_researcher to search local sources; "
        "after researcher returns, transfer_to_analyst to call analyze_tool on the findings; "
        "after analyst returns, transfer_to_writer to write and save the Chinese report with write_tool. "
        "Check actual tool results, not claims: do not finish until search_tool, analyze_tool and "
        "write_tool have all succeeded. If a worker skipped its tool, delegate back to that worker "
        "to complete its own step. After the report is saved, return the path and finish."
    )).compile(name="supervisor")


def build_hierarchical(model):
    tech = create_supervisor(model=model, agents=[
        worker(model, "frontend", [design_tool], "Discuss frontend design; this graph does not deliver products."),
        worker(model, "backend", [design_tool], "Discuss backend design; this graph does not deliver products."),
    ], prompt="Coordinate frontend and backend, summarize once and return.").compile(name="tech_supervisor")
    design = create_supervisor(model=model, agents=[
        worker(model, "ui", [design_tool], "Discuss UI design with the teaching template."),
        worker(model, "ux", [design_tool], "Discuss UX design with the teaching template."),
    ], prompt="Coordinate UI and UX, summarize once and return.").compile(name="design_supervisor")
    qa = worker(model, "qa", [], "Review the proposed test requirements; this planning graph does not execute product tests.")
    return create_supervisor(model=model, agents=[tech, design, qa], prompt=(
        "Ask tech_supervisor and design_supervisor for plans, then qa for a review. "
        "Return a concise Chinese teaching plan; do not claim a website was built."
    )).compile(name="ceo_supervisor")


def build_swarm(model):
    to_critic = create_handoff_tool(agent_name="Critic", description="Hand off findings to Critic.")
    to_writer = create_handoff_tool(agent_name="Writer", description="Hand off reviewed findings to Writer.")
    to_researcher = create_handoff_tool(agent_name="Researcher", description="Request more local evidence.")
    researcher = worker(model, "Researcher", [search_tool, to_critic],
                        "Read local sources, retain IDs, then hand off to Critic.")
    critic = worker(model, "Critic", [to_researcher, to_writer],
                    "Review findings. Request more evidence only if needed, otherwise hand off to Writer.")
    writer = worker(model, "Writer", [write_tool],
                    "Produce and save the final Chinese report. Finish without another handoff.")
    return create_swarm([researcher, critic, writer], default_active_agent="Researcher").compile(name="swarm")


def build_network(model, max_steps):
    class NetworkState(TypedDict):
        messages: Annotated[list, add_messages]
        next_agent: str
        steps: int
        artifact_sha256: str
        reviewed_sha256: str

    class Route(BaseModel):
        next_agent: Literal["planner", "executor", "reviewer", "END"]

    class Review(BaseModel):
        verdict: Literal['pass', 'request_changes']
        summary: str

    def artifact_hash():
        path = OUTPUT / 'agent_report.md'
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and path.stat().st_size else ''

    agents = {
        "planner": worker(model, "planner", [search_tool], "Plan based on local sources and retain IDs."),
        "executor": worker(model, "executor", [write_tool], "Create and save a Chinese training proposal from the plan."),
        "reviewer": worker(model, "reviewer", [analyze_tool], "Review the proposal and explain whether it is complete."),
    }

    def wrap(name, agent):
        def node(state):
            result = agent.invoke({"messages": state["messages"]}, config={"recursion_limit": 20})
            update = {"messages": result["messages"], "steps": state["steps"] + 1}
            prior = {getattr(message, 'id', None) for message in state['messages']}
            actual_write = any(getattr(m, 'type', None) == 'tool' and getattr(m, 'name', '') == 'write_tool'
                               and getattr(m, 'id', None) not in prior and str(m.content) == str(OUTPUT / 'agent_report.md')
                               for m in result['messages'])
            if name == 'executor' and actual_write:
                update.update(artifact_sha256=artifact_hash(), reviewed_sha256='')
            if name == 'reviewer' and state.get('artifact_sha256') == artifact_hash() and artifact_hash():
                review = model.with_structured_output(Review, method='function_calling').invoke([
                    HumanMessage(content='Review this actual proposal. Return pass only if it fulfills the task.\n' +
                                 (OUTPUT / 'agent_report.md').read_text(encoding='utf-8')), *result['messages']])
                update['reviewed_sha256'] = artifact_hash() if review.verdict == 'pass' else ''
            return update
        return node

    router_model = model.with_structured_output(Route, method="function_calling")

    def router(state):
        current = artifact_hash()
        complete = bool(current and state.get('artifact_sha256') == current and state.get('reviewed_sha256') == current)
        if state["steps"] >= max_steps:
            if complete:
                return {'next_agent': 'END'}
            raise RuntimeError("Network worker budget reached; task was not marked complete")
        choice = router_model.invoke([
            HumanMessage(content="Choose the next worker: planner, executor, reviewer or END. "
                         "Use END only when the proposal has been reviewed and is complete."),
            *state["messages"],
        ])
        next_agent = choice.next_agent
        if next_agent == 'END' and not complete:
            next_agent = 'executor' if not current or state.get('artifact_sha256') != current else 'reviewer'
        return {"next_agent": next_agent}

    graph = StateGraph(NetworkState)
    for name, agent in agents.items():
        graph.add_node(name, wrap(name, agent))
        graph.add_edge(name, "router")
    graph.add_node("router", router)
    graph.add_edge(START, "planner")
    graph.add_conditional_edges("router", lambda state: state["next_agent"],
                                {**{name: name for name in agents}, "END": END})
    return graph.compile(name="network")


async def run_autogen(task, check_only, max_turns):
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.ui import Console
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from common import CORPUS

    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not check_only and (not key or key == "replace-with-your-key"):
        raise ValueError("Set DEEPSEEK_API_KEY before running AutoGen")
    client = OpenAIChatCompletionClient(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        base_url="https://api.deepseek.com", api_key=key or "check-only-no-api-call",
        model_info={"vision": False, "function_calling": True, "json_output": True,
                    "family": "unknown", "structured_output": False},
        max_tokens=600, timeout=45, max_retries=0,
    )
    try:
        agents = [AssistantAgent(name=name, model_client=client, system_message=prompt)
                  for name, prompt in [
                      ("Researcher", "Extract findings from the supplied local corpus, cite source IDs."),
                      ("Critic", "Review the findings and identify risks."),
                      ("Writer", "Write the final concise Chinese report with sources."),
                  ]]
        team = RoundRobinGroupChat(agents, max_turns=max_turns)
        if check_only:
            print("CHECK ONLY: AutoGen team constructed; no API request made")
            return
        result = await Console(team.run_stream(task=f"{task}\nLocal corpus: {json.dumps(CORPUS, ensure_ascii=False)}"))
        save("autogen", {"stop_reason": result.stop_reason,
                         "messages": [message.model_dump(mode="json") for message in result.messages]})
    finally:
        await client.close()


def save(lab, result):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / f"{lab}.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                      default=lambda value: value.model_dump(mode="json")
                                      if hasattr(value, "model_dump") else str(value)), encoding="utf-8")
    print(f"Saved: {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", choices=["sequential", "supervisor", "hierarchical", "swarm", "network", "devteam", "autogen"], default="sequential")
    parser.add_argument("--check", action="store_true", help="Build the graph only; do not invoke an LLM")
    parser.add_argument("--trace", action="store_true", help="Print live role messages, tool calls and results")
    parser.add_argument("--trace-details", action="store_true", help="Expand trace message and tool argument previews")
    parser.add_argument("--ask-key", action="store_true", help="Prompt for a missing API key without displaying or saving it")
    parser.add_argument("--replay", nargs="?", const=str(OUTPUT / "supervisor.json"),
                        help="Replay a saved message history without executing models or tools")
    parser.add_argument("--replay-delay", type=float, default=0.3, help="Seconds between recorded messages")
    parser.add_argument("--approve", action="store_true", help="Removed for product delivery; approve an existing revision instead")
    parser.add_argument("--requirements")
    parser.add_argument("--output")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--decision", choices=['approve', 'reject'])
    parser.add_argument("--run-dir")
    parser.add_argument("--revision")
    parser.add_argument("--topic", default="AI Agent协作模式选型")
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument("--recursion-limit", type=int, default=60)
    args = parser.parse_args()
    if min(args.max_steps, args.max_turns, args.recursion_limit) < 1:
        parser.error("limits must be positive integers")
    if args.replay_delay < 0:
        parser.error("replay delay must not be negative")
    if args.replay:
        replay_trace(args.replay, ConsoleTrace(details=args.trace_details), delay=args.replay_delay)
        return
    if args.lab == 'devteam':
        from product_bridge import run
        raise SystemExit(run(args))
    if sys.version_info < (3, 12):
        parser.error("Python 3.12 or newer is required")
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if args.ask_key and not args.check and (not key or key == "replace-with-your-key"):
        os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("DeepSeek API key (hidden, this run only): ").strip()
    if args.lab == "autogen":
        asyncio.run(run_autogen(args.topic, args.check, args.max_turns))
        return
    model = make_model(args.check)
    builders = {"sequential": build_sequential, "supervisor": build_supervisor,
                "hierarchical": build_hierarchical, "swarm": build_swarm}
    app = build_network(model, args.max_steps) if args.lab == "network" else builders[args.lab](model)
    if args.check:
        print(f"CHECK ONLY: {args.lab} compiled; no API request made")
        return
    config = {"recursion_limit": args.recursion_limit,
              "configurable": {"thread_id": os.getenv("TRAINING_THREAD_ID", "training-1")}}
    inputs = {"topic": args.topic} if args.lab == "sequential" else {
        "messages": [{"role": "user", "content": args.topic}]}
    if args.lab == "network":
        inputs.update(next_agent="planner", steps=0)
    result = run_with_trace(app, inputs, config, ConsoleTrace(details=args.trace_details)) if args.trace else app.invoke(inputs, config=config)
    save(args.lab, result)
    if args.lab == "sequential":
        print(result["seo_content"])


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(redact(f"ERROR: {type(error).__name__}: {error}"), file=sys.stderr)
        sys.exit(1)
