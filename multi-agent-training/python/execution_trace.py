"""Readable LangGraph execution events and playback of saved message histories."""
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import unicodedata


def field(message, name, default=None):
    return message.get(name, default) if isinstance(message, dict) else getattr(message, name, default)


def redact(text):
    for name in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY"):
        secret = os.getenv(name, "")
        if len(secret) >= 8:
            text = text.replace(secret, "[REDACTED]")
    return re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[REDACTED]", text)


def fit_line(text, width):
    if sum(2 if unicodedata.east_asian_width(character) in ("W", "F") else 1 for character in text) <= width:
        return text
    available = max(0, width - 3)
    size = 0
    for index, character in enumerate(text):
        size += 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1
        if size > available:
            return text[:index] + "..." if width >= 3 else ""
    return text


class ConsoleTrace:
    def __init__(self, output=None, details=True):
        self.output = output if output is not None else sys.stdout
        self.details = details
        self.color = bool(getattr(self.output, "isatty", lambda: False)()) and "NO_COLOR" not in os.environ
        self.active_actor = None
        self.started = time.monotonic()
        self.step = 0
        self.seen = set()
        self.completed_tools = {}
        self.errors = 0

    def emit(self, actor, action, content=""):
        if not self.details:
            self.compact_event(actor, action, content)
            return
        self.step += 1
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False, default=str)
        preview = " ".join(redact(content).split())
        if len(preview) > 280:
            preview = preview[:280] + "..."
        elapsed = time.monotonic() - self.started
        print(f"[{self.step:03d} +{elapsed:6.1f}s] {actor}: {action} {preview}".rstrip(),
              file=self.output, flush=True)

    def compact_line(self, text, color=""):
        width = max(50, min(100, shutil.get_terminal_size(fallback=(100, 24)).columns))
        text = fit_line(" ".join(redact(text).split()), width)
        if self.color and color:
            text = f"\033[{color}m{text}\033[0m"
        print(text, file=self.output, flush=True)

    def compact_event(self, actor, action, content):
        colors = {"supervisor": "1;36", "researcher": "1;34", "analyst": "1;35", "writer": "1;32"}
        if actor not in ("trace", "user", "tool") and actor != self.active_actor:
            self.active_actor = actor
            print(file=self.output, flush=True)
            self.compact_line(f"===== {actor.upper()} =====", colors.get(actor, "1"))
        if action == "SAYS":
            return
        if action == "TOOL SUMMARY":
            print(file=self.output, flush=True)
            self.compact_line("===== RESULTS =====", "1;36")
            for name, count in content["successful_results"].items():
                if not name.startswith("transfer_"):
                    self.compact_line(f"  OK {name}: {count} successful result(s)", "32")
            self.compact_line(f"Tool errors: {content['tool_errors']}", "1;33" if content["tool_errors"] else "32")
            return
        if action == "LIVE":
            preview = "Model + tools | waiting for events"
        elif action == "REPLAY":
            preview = "Recorded events | No model or tool execution"
        elif action.startswith("CALL "):
            name = action[5:]
            if name == "search_tool":
                preview = "query=" + str(content.get("query", ""))
            elif name == "analyze_tool":
                preview = f"input={len(content.get('data', ''))} chars"
            elif name == "write_tool":
                preview = f"report={len(content.get('content', ''))} chars"
            elif name.startswith("transfer_to_"):
                preview = "-> " + name[len("transfer_to_"):]
            else:
                preview = ""
        elif action.startswith("OK "):
            name = action[3:]
            try:
                data = json.loads(content)
            except (ValueError, TypeError):
                data = None
            if name == "search_tool" and isinstance(data, dict):
                preview = f"sources={len(data.get('items', []))} | local corpus"
                if data.get("fallback_to_full_corpus"):
                    preview += " | full-corpus fallback"
            elif name == "analyze_tool" and isinstance(data, dict):
                preview = f"chars={data.get('characters', '?')} | sources={data.get('source_count', '?')}"
            elif name == "write_tool":
                preview = "saved: " + Path(str(content)).name
            elif name.startswith("transfer_"):
                preview = "handoff accepted"
            else:
                preview = str(content)
        elif action.startswith("ERROR ") and "not a valid tool" in str(content):
            preview = "tool unavailable"
        elif action == "UPDATE":
            preview = "updated: " + ", ".join(content)
        else:
            preview = str(content)
        self.step += 1
        elapsed = time.monotonic() - self.started
        color = "1;31" if action.startswith(("ERROR", "INVALID")) else "1;33" if action == "WARN" else ""
        self.compact_line(f"[{self.step:02d} {elapsed:5.1f}s] {action}" + (f" | {preview}" if preview else ""), color)

    def message(self, message, fallback="agent"):
        kind = field(message, "type") or {"user": "human", "assistant": "ai", "tool": "tool"}.get(field(message, "role"))
        calls = field(message, "tool_calls", []) or []
        content = field(message, "content", "")
        # Handoff messages acquire message IDs later; tool call IDs stay stable.
        if kind == "tool":
            identity = (kind, field(message, "tool_call_id"), field(message, "name"), str(content))
        elif calls:
            identity = (kind, tuple(call.get("id") for call in calls), str(content))
        elif kind == "human":
            identity = (kind, str(content))
        else:
            identity = field(message, "id")
        if identity:
            if identity in self.seen:
                return
            self.seen.add(identity)
        actor = field(message, "name") or fallback
        if kind == "tool":
            status = "ERROR" if field(message, "status") == "error" else "OK"
            if status == "ERROR":
                self.errors += 1
            else:
                self.completed_tools[actor] = self.completed_tools.get(actor, 0) + 1
            if self.details or not (field(message, "response_metadata", {}) or {}).get("__is_handoff_back"):
                self.emit("tool", f"{status} {actor}", content)
        elif kind == "ai":
            if not self.details and (field(message, "response_metadata", {}) or {}).get("__is_handoff_back"):
                self.emit(actor, "AUTO RETURN", "-> supervisor")
                return
            if content:
                self.emit(actor, "SAYS", content)
            for call in calls:
                self.emit(actor, f"CALL {call['name']}", call.get("args", {}))
            for call in field(message, "invalid_tool_calls", []) or []:
                self.emit(actor, f"INVALID CALL {call.get('name')}", call.get("error") or call.get("args"))
            if (field(message, "response_metadata", {}) or {}).get("finish_reason") == "length":
                self.emit(actor, "WARN", "Reached the output token limit; content or tool arguments may be incomplete.")
        elif kind == "human":
            self.emit("user", "TASK", content)

    def update(self, updates):
        for node, update in updates.items():
            if not isinstance(update, dict):
                continue
            if "messages" in update:
                messages = update["messages"]
                for message in messages if isinstance(messages, (list, tuple)) else [messages]:
                    self.message(message, fallback=node)
            else:
                self.emit(node, "UPDATE", update)

    def summary(self):
        self.emit("trace", "TOOL SUMMARY", {"successful_results": self.completed_tools,
                                              "tool_errors": self.errors})


def run_with_trace(app, inputs, config, trace):
    trace.emit("trace", "LIVE", "Waiting for graph events; model requests can take several seconds.")
    if inputs and "messages" in inputs:
        for message in inputs["messages"]:
            if field(message, "type") == "human" or field(message, "role") == "user":
                trace.message(message)
    result = None
    # Nested updates expose worker tools; only root values are the final graph state.
    for namespace, mode, data in app.stream(inputs, config=config,
                                             stream_mode=["updates", "values"], subgraphs=True):
        if mode == "updates" and isinstance(data, dict):
            trace.update(data)
        elif mode == "values" and not namespace:
            result = data
    if result is None:
        raise RuntimeError("The graph did not produce a final state")
    trace.summary()
    return result


def replay_trace(recording, trace, delay=0.3):
    result = json.loads(Path(recording).read_text(encoding="utf-8-sig"))
    messages = result.get("messages") if isinstance(result, dict) else None
    if not isinstance(messages, list) or not messages:
        raise ValueError("The recording must contain a nonempty messages list")
    trace.emit("trace", "REPLAY", "Recorded events only. No model or tool execution.")
    for message in messages:
        trace.message(message)
        if delay:
            time.sleep(delay)
    trace.summary()
