import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph


class ExecutionTraceTests(unittest.TestCase):
    def test_cli_exposes_live_trace_and_replay(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("labs.py")), "--help"],
            capture_output=True, text=True, encoding="utf-8", check=True,
        )
        for flag in ("--trace", "--ask-key", "--replay"):
            self.assertIn(flag, result.stdout)

    def test_nested_graph_keeps_final_state_and_prints_tools_once(self):
        from execution_trace import ConsoleTrace, run_with_trace

        inner = StateGraph(MessagesState)
        inner.add_node("agent", lambda state: {"messages": [AIMessage(
            content="Searching local sources", name="researcher", id="research",
            tool_calls=[{"name": "search_tool", "args": {"query": "Supervisor"}, "id": "call-1"}],
        )]})
        inner.add_node("tools", lambda state: {"messages": [ToolMessage(
            content='{"source_count": 7}', name="search_tool", tool_call_id="call-1", id="tool-1",
        )]})
        inner.add_edge(START, "agent")
        inner.add_edge("agent", "tools")
        inner.add_edge("tools", END)
        outer = StateGraph(MessagesState)
        outer.add_node("researcher", inner.compile())
        outer.add_node("supervisor", lambda state: {"messages": [AIMessage(
            content="Research returned", name="supervisor", id="final",
        )]})
        outer.add_edge(START, "researcher")
        outer.add_edge("researcher", "supervisor")
        outer.add_edge("supervisor", END)
        app = outer.compile()
        inputs = {"messages": [HumanMessage(content="Research", id="user")]}
        output = io.StringIO()
        actual = run_with_trace(app, inputs, {}, ConsoleTrace(output))
        self.assertEqual(actual, app.invoke(inputs))
        self.assertEqual(output.getvalue().count("CALL search_tool"), 1)
        self.assertEqual(output.getvalue().count("OK search_tool"), 1)
        self.assertIn("researcher", output.getvalue())

    def test_trace_keeps_non_message_graph_state(self):
        from execution_trace import ConsoleTrace, run_with_trace

        graph = StateGraph(dict)
        graph.add_node("draft", lambda state: {"report": "Finished draft"})
        graph.add_edge(START, "draft")
        graph.add_edge("draft", END)
        app = graph.compile()
        output = io.StringIO()
        self.assertEqual(run_with_trace(app, {}, {}, ConsoleTrace(output)), {"report": "Finished draft"})
        self.assertIn("draft", output.getvalue())

    def test_handoff_messages_remain_unique_after_framework_assigns_ids(self):
        from execution_trace import ConsoleTrace

        output = io.StringIO()
        trace = ConsoleTrace(output)
        call = AIMessage(content="Returning", name="researcher", tool_calls=[
            {"name": "transfer_back_to_supervisor", "args": {}, "id": "back-1"},
        ])
        response = ToolMessage(content="Transferred", name="transfer_back_to_supervisor", tool_call_id="back-1")
        for message in (call, response, call.model_copy(update={"id": "assigned-ai"}),
                        response.model_copy(update={"id": "assigned-tool"})):
            trace.message(message)
        self.assertEqual(output.getvalue().count("CALL transfer_back_to_supervisor"), 1)
        self.assertEqual(output.getvalue().count("OK transfer_back_to_supervisor"), 1)

    def test_invalid_and_truncated_model_calls_are_visible(self):
        from execution_trace import ConsoleTrace

        output = io.StringIO()
        ConsoleTrace(output).message(AIMessage(
            content="Saving", name="writer", response_metadata={"finish_reason": "length"},
            invalid_tool_calls=[{"name": "write_tool", "args": '{"content":', "id": "broken", "error": "Incomplete JSON"}],
        ))
        self.assertIn("INVALID CALL write_tool", output.getvalue())
        self.assertIn("output token limit", output.getvalue())

    def test_model_budget_allows_complete_report_tool_arguments(self):
        from common import make_model

        with patch.dict(os.environ, {"DEEPSEEK_MAX_TOKENS": "1600"}):
            self.assertEqual(make_model(check_only=True).max_tokens, 1600)

    def test_graph_exception_is_not_reported_as_completion(self):
        from execution_trace import ConsoleTrace, run_with_trace

        def fail(state):
            raise RuntimeError("Connection failed")

        graph = StateGraph(dict)
        graph.add_node("worker", fail)
        graph.add_edge(START, "worker")
        graph.add_edge("worker", END)
        with self.assertRaisesRegex(RuntimeError, "Connection failed"):
            run_with_trace(graph.compile(), {}, {}, ConsoleTrace(io.StringIO()))

    def test_redaction_and_failed_tool_status(self):
        from execution_trace import ConsoleTrace

        output = io.StringIO()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "custom-secret-value"}):
            trace = ConsoleTrace(output)
            trace.message(AIMessage(content="custom-secret-value sk-abcdefghijklmnop", name="writer"))
            trace.message(ToolMessage(content="Invalid tool", name="missing_tool", tool_call_id="bad", status="error"))
        self.assertNotIn("custom-secret-value", output.getvalue())
        self.assertNotIn("sk-abcdefghijklmnop", output.getvalue())
        self.assertIn("[REDACTED]", output.getvalue())
        self.assertIn("ERROR missing_tool", output.getvalue())

    def test_replay_labels_recording_without_running_tools(self):
        from execution_trace import ConsoleTrace, replay_trace

        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            recording = Path(directory) / "recording.json"
            recording.write_text(json.dumps({"messages": [
                {"type": "ai", "name": "writer", "content": "Save", "tool_calls": [
                    {"name": "write_tool", "args": {"content": "Report"}, "id": "saved"},
                ]},
                {"type": "tool", "name": "write_tool", "content": "agent_report.md", "status": "success"},
            ]}), encoding="utf-8")
            replay_trace(recording, ConsoleTrace(output), delay=0)
        self.assertIn("REPLAY", output.getvalue())
        self.assertIn("No model or tool execution", output.getvalue())
        self.assertIn("CALL write_tool", output.getvalue())
        self.assertIn("OK write_tool", output.getvalue())

    def test_replay_rejects_invalid_recording(self):
        from execution_trace import ConsoleTrace, replay_trace

        with tempfile.TemporaryDirectory() as directory:
            recording = Path(directory) / "recording.json"
            recording.write_text('{"status": "completed"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "messages"):
                replay_trace(recording, ConsoleTrace(io.StringIO()), delay=0)

    def test_compact_trace_highlights_roles_and_metrics_without_report_body(self):
        from execution_trace import ConsoleTrace

        output = io.StringIO()
        trace = ConsoleTrace(output, details=False)
        trace.message(AIMessage(content="LONG REPORT " * 100, name="researcher", tool_calls=[
            {"name": "search_tool", "args": {"query": "Supervisor"}, "id": "search"},
        ]))
        trace.message(ToolMessage(name="search_tool", tool_call_id="search", content=json.dumps({
            "source": "local training corpus", "fallback_to_full_corpus": True,
            "items": [{"id": f"source-{number}", "text": "LONG REPORT " * 100} for number in range(7)],
        })))
        trace.message(AIMessage(content="LONG REPORT " * 100, name="analyst", tool_calls=[
            {"name": "analyze_tool", "args": {"data": "LONG REPORT " * 100}, "id": "analysis"},
        ]))
        trace.message(ToolMessage(name="analyze_tool", tool_call_id="analysis",
                                  content='{"characters": 921, "source_count": 7}'))
        trace.summary()
        rendered = output.getvalue()
        self.assertIn("RESEARCHER", rendered)
        self.assertIn("ANALYST", rendered)
        self.assertIn("sources=7", rendered)
        self.assertIn("chars=921", rendered)
        self.assertIn("RESULTS", rendered)
        self.assertNotIn("LONG REPORT", rendered)
        self.assertTrue(all(len(line) <= 100 for line in rendered.splitlines()))

    def test_compact_trace_distinguishes_automatic_return_and_real_tool_error(self):
        from execution_trace import ConsoleTrace

        output = io.StringIO()
        trace = ConsoleTrace(output, details=False)
        trace.message(AIMessage(content="Return", name="analyst", response_metadata={"__is_handoff_back": True},
                                tool_calls=[{"name": "transfer_back_to_supervisor", "args": {}, "id": "auto"}]))
        trace.message(ToolMessage(content="Returned", name="transfer_back_to_supervisor", tool_call_id="auto",
                                  response_metadata={"__is_handoff_back": True}))
        trace.message(ToolMessage(content="Error: transfer_back_to_supervisor is not a valid tool",
                                  name="transfer_back_to_supervisor", tool_call_id="invalid", status="error"))
        trace.summary()
        self.assertIn("AUTO RETURN", output.getvalue())
        self.assertNotIn("CALL transfer_back_to_supervisor", output.getvalue())
        self.assertIn("ERROR transfer_back_to_supervisor", output.getvalue())
        self.assertIn("Tool errors: 1", output.getvalue())

    def test_details_mode_keeps_message_and_tool_arguments(self):
        from execution_trace import ConsoleTrace

        output = io.StringIO()
        ConsoleTrace(output, details=True).message(AIMessage(content="Detailed explanation", name="writer", tool_calls=[
            {"name": "write_tool", "args": {"content": "Detailed report"}, "id": "write"},
        ]))
        self.assertIn("Detailed explanation", output.getvalue())
        self.assertIn("Detailed report", output.getvalue())

    def test_compact_long_task_keeps_readable_prefix(self):
        from execution_trace import ConsoleTrace

        output = io.StringIO()
        ConsoleTrace(output, details=False).message(HumanMessage(content="Compare collaboration patterns " * 20))
        line = output.getvalue().strip()
        self.assertIn("Compare collaboration patterns", line)
        self.assertTrue(line.endswith("..."))
        self.assertLessEqual(len(line), 100)


if __name__ == "__main__":
    unittest.main()
