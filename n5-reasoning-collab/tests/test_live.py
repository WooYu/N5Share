"""All model calls are in-memory mocks. These tests never contact DeepSeek."""
import asyncio
from copy import deepcopy
import unittest
from unittest.mock import patch

from server.deepseek import DeepSeekClient, ENDPOINT, MODEL, ModelError
from server.runtime import Run, RunManager
from server.tools import FINDINGS, REQUIRED_CHANGES, RESOLUTIONS, VENUES


def call(name, **arguments):
    return {"name": name, "arguments": arguments}


class ScriptedModel:
    def __init__(self):
        self.active = 0
        self.peak = 0
        self.contexts = []

    async def complete(self, context):
        self.active += 1
        self.peak = max(self.peak, self.active)
        self.contexts.append(deepcopy(context))
        await asyncio.sleep(0)
        self.active -= 1
        state, stage = context["state"], context["stage"]
        weather, budget = state["constraints"]["weather"], state["constraints"]["budget"]
        candidates = [v for v in VENUES if (weather == "sun" or v["type"] == "indoor") and v["total"] <= budget]
        preferred = next((v for v in candidates if v["id"] == "P03"), candidates[0] if candidates else None)
        action = {"summary": "根据当前证据执行本角色下一步。", "calls": [], "plan": [],
                  "reflection": "", "next_actor": context["expected_next_actor"], "result": None}
        def costs():
            return [call("calculate_cost", venue=preferred["id"]),
                    call("check_budget", venue=preferred["id"], total=preferred["total"])] if preferred else []
        def final():
            checks = state.get("budget_checks", state.get("finance_report", {}).get("budget_checks", {}))
            for v in candidates:
                if checks.get(v["id"], {}).get("within_budget"):
                    return {"status": "completed", "venue": v["id"], "total": v["total"]}
            return {"status": "needs_human"}
        if stage == "react":
            if not state["weather"]:
                action["calls"] = [call("get_weather")]
            elif not state["venues"]:
                action["calls"] = [call("search_venue", type="indoor" if weather == "rain" else "all")]
            elif preferred and not state["budget_checks"]:
                action["calls"] = costs()
            else:
                action["result"] = final()
        elif stage in ("plan_v1", "plan_v2", "delegate_info", "info_plan", "finance_plan"):
            action["plan"] = ["根据阶段执行已声明的角色步骤"]
            if stage == "plan_v2":
                action["reflection"] = "将查天气前移，按天气过滤后重新核对完整费用与预算。"
        elif stage == "execute_v1":
            action["calls"] = [call("search_venue", type="outdoor"), call("calculate_cost", venue="P02"),
                               call("check_budget", venue="P02", total=270), call("get_weather")]
        elif stage == "execute_v2":
            action["calls"] = [call("get_weather"), call("search_venue", type="indoor" if weather == "rain" else "all")] + costs()
        elif stage == "weather":
            action["calls"] = [call("get_weather")]
        elif stage == "venue":
            action["calls"] = [call("search_venue", type="indoor" if weather == "rain" else "all")]
            if context["scenario"] in ("supervisor", "swarm"):
                identifier = ("P04" if weather == "rain" else "P01") if state.get("rejected_venues") else ("P03" if weather == "rain" else "P02")
                action["result"] = {"status": "candidate", "venue": identifier}
        elif stage == "ticket":
            action["calls"] = [call("calculate_cost", venue=preferred["id"])] if preferred else []
        elif stage == "budget":
            action["calls"] = costs()
            if context["scenario"] in ("supervisor", "swarm"):
                selected = next(v for v in VENUES if v["id"] == state["selected_venue"])
                action["calls"] = [call("calculate_cost", venue=selected["id"]),
                                   call("check_budget", venue=selected["id"], total=selected["total"])]
            if context["scenario"] == "hierarchical":
                action["calls"] = action["calls"][1:]
        elif stage == "final":
            action["result"] = final()
        elif stage in ("review_0", "review_1"):
            revision = int(stage[-1])
            action["calls"] = [call("inspect_review", revision=revision)]
            action["result"] = {"status": "report", "revision": revision, "findings": FINDINGS[context["actor"]] if revision == 0 else []}
        elif stage == "arbitrate":
            action["calls"] = [call("get_business_rules")]
            action["result"] = {"status": "arbitrated", "resolutions": RESOLUTIONS}
        elif stage == "revise":
            action["calls"] = [call("apply_revision", changes=sorted(REQUIRED_CHANGES))]
        elif stage == "review_final":
            action["result"] = {"status": "review_passed"}
        return action, {"input_tokens": 20, "output_tokens": 10}


class FixedModel:
    def __init__(self, action):
        self.action = action
    async def complete(self, context):
        return {**self.action, "next_actor": context["expected_next_actor"]}, {}


class BlockingModel:
    def __init__(self):
        self.started = asyncio.Event()
        self.cancelled = False
    async def complete(self, context):
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


class LiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_request_contract_is_json_without_thinking(self):
        action = dict(summary="请求课程工具", calls=[call("get_weather")], plan=[],
                      reflection="", next_actor="", result=None)
        recorded = {}
        class Response:
            status_code = 200
            content = b"small"
            def json(self):
                import json
                return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(action)}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        class HTTPMock:
            def __init__(self, **kwargs):
                recorded["options"] = kwargs
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False
            async def post(self, url, **kwargs):
                recorded.update(url=url, **kwargs)
                return Response()
        with patch("httpx.AsyncClient", HTTPMock):
            actual, usage = await DeepSeekClient("test-only-key").complete({"stage": "test"})
        self.assertEqual(actual, action)
        self.assertEqual(usage, {"input_tokens": 10, "output_tokens": 5})
        self.assertEqual(recorded["url"], ENDPOINT)
        self.assertEqual(recorded["json"]["model"], MODEL)
        self.assertEqual(recorded["json"]["thinking"], {"type": "disabled"})
        self.assertEqual(recorded["json"]["response_format"], {"type": "json_object"})
        self.assertFalse(recorded["options"]["follow_redirects"])
        self.assertFalse(recorded["options"]["trust_env"])

    async def test_provider_failure_is_explicit_without_exposing_response_or_key(self):
        class Response:
            status_code = 401
        class HTTPMock:
            def __init__(self, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False
            async def post(self, *args, **kwargs):
                return Response()
        with patch("httpx.AsyncClient", HTTPMock):
            with self.assertRaises(ModelError) as error:
                await DeepSeekClient("test-secret-never-public").complete({})
        self.assertIn("401", str(error.exception))
        self.assertNotIn("test-secret", str(error.exception))

    async def test_all_outing_topologies_weather_budget_matrix(self):
        for scenario in ("react", "plan", "supervisor", "hierarchical", "swarm", "dual"):
            for weather in ("sun", "rain"):
                for budget in (300, 200, 100):
                    with self.subTest(scenario=scenario, weather=weather, budget=budget):
                        run = Run(scenario, weather, budget, ScriptedModel())
                        await run.run()
                        needs_human = budget == 100 or (scenario == "plan" and (weather == "rain" or budget < 270))
                        self.assertEqual(run.status, "needs_human" if needs_human else "completed", run.error)
                        self.assertLessEqual(run.metrics["model_calls"], 12)
                        self.assertLessEqual(run.metrics["tool_calls"], 20)
                        if not needs_human:
                            self.assertLessEqual(run.state["itinerary"]["total"], budget)
                        if weather == "rain" and budget == 200 and scenario != "plan":
                            self.assertEqual(run.state["itinerary"]["venue"], "P04")

    async def test_dual_hands_failure_back_to_planner_and_preserves_snapshots(self):
        run = Run("dual", "rain", 300, ScriptedModel())
        await run.run()
        self.assertEqual(run.status, "completed", run.error)
        self.assertTrue(any(e["kind"] == "reflection" for e in run.events))
        handoffs = [e["payload"] for e in run.events if e["kind"] == "dispatch"]
        self.assertEqual([(e["sender"], e["receiver"]) for e in handoffs],
                         [("planner", "executor"), ("executor", "planner"), ("planner", "executor"), ("executor", "planner")])
        self.assertIsNone(run.events[0]["state_after"]["weather"])
        self.assertIsNone(run.events[0]["state_after"]["itinerary"])
        self.assertEqual(run.state["itinerary"]["total"], 210)

    async def test_dual_v2_waits_for_observations_then_continues_before_handoff(self):
        class SplitExecutor(ScriptedModel):
            def __init__(self):
                super().__init__()
                self.v2_turns = 0
            async def complete(self, context):
                action, usage = await super().complete(context)
                if context["stage"] == "execute_v2":
                    self.v2_turns += 1
                    action["calls"] = action["calls"][:2] if self.v2_turns == 1 else action["calls"][2:]
                return action, usage
        model = SplitExecutor()
        run = Run("dual", "rain", 300, model)
        await run.run()
        self.assertEqual(run.status, "completed", run.error)
        self.assertEqual(run.metrics["model_calls"], 6)
        self.assertEqual(run.metrics["tool_calls"], 8)
        self.assertEqual(run.state["itinerary"]["total"], 210)
        continuation = [context for context in model.contexts if context["stage"] == "execute_v2"][1]
        self.assertEqual(continuation["state"]["control_owner"], "executor")
        self.assertEqual(continuation["state"]["weather"], "rain")
        self.assertEqual(continuation["state"]["execution_progress"]["remaining"], ["calculate_cost", "check_budget"])
        self.assertEqual([venue["id"] for venue in continuation["state"]["venues"]], ["P03", "P04"])
        self.assertEqual([context["stage"] for context in model.contexts][-2:], ["execute_v2", "final"])
        no_candidate = Run("dual", "rain", 100, SplitExecutor())
        await no_candidate.run()
        self.assertEqual(no_candidate.status, "needs_human", no_candidate.error)
        self.assertEqual(no_candidate.metrics["model_calls"], 5)

    async def test_review_parallel_arbitration_revision_independent_recheck(self):
        model = ScriptedModel()
        run = Run("review", "rain", 300, model)
        await run.run()
        self.assertEqual(run.status, "completed", run.error)
        self.assertEqual(model.peak, 4)
        self.assertEqual(run.metrics["model_calls"], 11)
        self.assertEqual(run.metrics["tool_calls"], 10)
        self.assertEqual(run.state["resolutions"], RESOLUTIONS)
        self.assertTrue(all(r["revision"] == 1 and not r["findings"] for r in run.state["review_reports"].values()))
        self.assertIn("durable local outbox", run.state["diff"])
        self.assertEqual(run.events[-1]["payload"]["scope"], "synthetic_review_workflow")

    async def test_fabricated_success_without_tools_is_rejected(self):
        action = dict(summary="已完成", calls=[], plan=[], reflection="", result={"status": "completed", "venue": "P03", "total": 210})
        run = Run("react", "rain", 300, FixedModel(action))
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.metrics["tool_calls"], 0)
        self.assertFalse(any(e["payload"].get("status") == "completed" for e in run.events))

    async def test_invalid_handoff_counts_usage_but_executes_no_tools(self):
        class InvalidHandoff(ScriptedModel):
            async def complete(self, context):
                action, usage = await super().complete(context)
                action["next_actor"] = "executor"
                return action, usage
        run = Run("react", "rain", 300, InvalidHandoff())
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertIn("控制权契约", run.error)
        self.assertEqual(run.metrics["input_tokens"], 20)
        self.assertEqual(run.metrics["output_tokens"], 10)
        self.assertEqual(run.metrics["tool_calls"], 0)
        self.assertIsNone(run.state["weather"])

    async def test_nonempty_handoff_is_not_normalized_into_allowed_role(self):
        class InvalidHandoff(ScriptedModel):
            async def complete(self, context):
                action, usage = await super().complete(context)
                action["next_actor"] = "venue "
                return action, usage
        run = Run("swarm", "rain", 300, InvalidHandoff())
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.metrics["input_tokens"], 20)
        self.assertEqual(run.metrics["tool_calls"], 0)

    async def test_invalid_usage_is_rejected_without_tool_execution(self):
        class InvalidUsage(ScriptedModel):
            async def complete(self, context):
                action, _ = await super().complete(context)
                return action, {"input_tokens": -1, "output_tokens": 10}
        run = Run("react", "rain", 300, InvalidUsage())
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.metrics["input_tokens"], 0)
        self.assertEqual(run.metrics["output_tokens"], 0)
        self.assertEqual(run.metrics["tool_calls"], 0)

    async def test_wrong_weather_and_total_cannot_pass(self):
        for venue, total in (("P02", 270), ("P03", 190)):
            action = dict(summary="候选结果", calls=[call("get_weather"), call("search_venue", type="all"),
                call("calculate_cost", venue=venue), call("check_budget", venue=venue, total=total)],
                plan=[], reflection="", result={"status": "completed", "venue": venue, "total": total})
            run = Run("react", "rain", 300, FixedModel(action))
            await run.run()
            self.assertEqual(run.status, "failed")

    async def test_model_and_tool_budgets_stop_explicitly(self):
        endless = dict(summary="继续查天气", calls=[call("get_weather")], plan=[], reflection="", result=None)
        run = Run("react", "rain", 300, FixedModel(endless), model_limit=2)
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.metrics["model_calls"], 2)
        run = Run("react", "rain", 300, ScriptedModel(), tool_limit=2)
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.metrics["tool_calls"], 2)

    async def test_inflight_model_is_cancelled_and_cannot_publish_success(self):
        model = BlockingModel()
        run = Run("react", "rain", 300, model)
        task = asyncio.create_task(run.run())
        await model.started.wait()
        run.stop("cancelled", "cancelled by test")
        task.cancel()
        await task
        self.assertEqual(run.status, "cancelled")
        self.assertTrue(model.cancelled)
        self.assertFalse(any(e["payload"].get("status") == "completed" for e in run.events))

    async def test_wall_clock_timeout_cancels_provider(self):
        model = BlockingModel()
        run = Run("react", "rain", 300, model, seconds=0.02)
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertTrue(model.cancelled)

    async def test_review_cannot_claim_pass_without_inspection(self):
        class ForgingModel(ScriptedModel):
            async def complete(self, context):
                action, usage = await super().complete(context)
                if context["stage"] == "review_1":
                    action["calls"] = []
                return action, usage
        run = Run("review", "rain", 300, ForgingModel())
        await run.run()
        self.assertEqual(run.status, "failed")

    async def test_supervisor_and_swarm_budget_failure_returns_control(self):
        for scenario in ("supervisor", "swarm"):
            run = Run(scenario, "rain", 200, ScriptedModel())
            await run.run()
            self.assertEqual(run.status, "completed", run.error)
            self.assertEqual(run.state["rejected_venues"], ["P03"])
            self.assertEqual(run.state["itinerary"]["venue"], "P04")
            handoffs = [(e["payload"]["sender"], e["payload"]["receiver"])
                        for e in run.events if e["kind"] == "dispatch"]
            if scenario == "swarm":
                self.assertIn(("budget", "venue"), handoffs)
            else:
                self.assertNotIn(("budget", "venue"), handoffs)
                self.assertEqual(handoffs.count(("supervisor", "venue")), 2)
                delegated = [e for e in run.events if e["kind"] == "dispatch" and
                             e["payload"]["sender"] == "supervisor"]
                self.assertTrue(all(e["state_after"]["control_owner"] == "supervisor" for e in delegated))
                self.assertTrue(all(e["state_after"]["execution_actor"] == e["payload"]["receiver"] for e in delegated))

    async def test_plan_v1_stops_at_failure_while_dual_revises(self):
        model = ScriptedModel()
        run = Run("plan", "rain", 300, model)
        await run.run()
        self.assertEqual(run.status, "needs_human", run.error)
        self.assertEqual([c["stage"] for c in model.contexts], ["plan_v1", "execute_v1"])
        self.assertFalse(any(e["kind"] == "reflection" for e in run.events))
        self.assertEqual(run.events[-1]["payload"]["reason"], "plan_v1_failed")
        self.assertIsNone(run.state["itinerary"])
        sunny = Run("plan", "sun", 300, ScriptedModel())
        await sunny.run()
        self.assertEqual(sunny.status, "completed", sunny.error)
        self.assertEqual(sunny.state["itinerary"]["venue"], "P02")

    async def test_initial_writers_and_terminal_state_are_host_owned(self):
        for scenario, weather, budget in (("react", "rain", 300), ("plan", "rain", 300), ("review", "rain", 300)):
            run = Run(scenario, weather, budget, ScriptedModel())
            self.assertEqual(set(run.writers), set(run.state))
            self.assertTrue(all(writer == "host" for writer in run.writers.values()))
            self.assertEqual(run.state["status"], "running")
            await run.run()
            terminal = run.events[-1]
            self.assertEqual(terminal["actor"], "host")
            self.assertEqual(terminal["state_after"]["status"], run.status)
            self.assertIsNone(terminal["state_after"]["control_owner"])
            self.assertIsNone(terminal["state_after"]["execution_actor"])
            self.assertEqual(terminal["writers"]["status"], "host")
        for status in ("cancelled", "failed"):
            run = Run("swarm", "rain", 300, ScriptedModel())
            run.stop(status, "test stop")
            self.assertEqual(run.events[-1]["actor"], "host")
            self.assertEqual(run.events[-1]["state_after"]["status"], status)
            self.assertEqual(run.events[-1]["writers"]["status"], "host")

    async def test_hierarchy_director_sees_only_reports_and_host_writes_facts(self):
        model = ScriptedModel()
        run = Run("hierarchical", "rain", 300, model)
        await run.run()
        self.assertEqual(run.status, "completed", run.error)
        for context in model.contexts:
            if context["actor"] == "director":
                self.assertNotIn("costs", context["state"])
                self.assertNotIn("weather", context["state"])
                self.assertNotIn("venues", context["state"])
        observations = [e for e in run.events if e["kind"] == "observation"]
        self.assertTrue(all(e["actor"] == "host" for e in observations))
        self.assertEqual(run.writers["weather"], "host")

    async def test_illegal_planner_actions_rejected_before_execution(self):
        action = dict(summary="非法先执行", calls=[call("get_weather")],
                      plan=["计划"], reflection="", result=None)
        run = Run("plan", "rain", 300, FixedModel(action))
        await run.run()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.metrics["tool_calls"], 0)
        self.assertIsNone(run.state["weather"])


class ManagerTests(unittest.TestCase):
    def test_concurrency_limit_rejects_excess_and_cancel_interrupts_tasks(self):
        class Blocking:
            async def complete(self, context):
                await asyncio.Event().wait()
        manager = RunManager(Blocking(), max_active=1)
        try:
            run = manager.start("react", "rain", 300)
            with self.assertRaises(ModelError):
                manager.start("react", "rain", 300)
            self.assertEqual(manager.cancel(run.id).status, "cancelled")
        finally:
            manager.close()

    def test_retention_is_bounded_and_cancel_returns_terminal(self):
        manager = RunManager(ScriptedModel(), max_retained=2)
        try:
            for _ in range(4):
                run = manager.start("react", "rain", 300)
                run.task.result(timeout=5)
            self.assertEqual(len(manager.runs), 2)
            cancelled = manager.cancel(run.id)
            self.assertEqual(cancelled.status, "completed")
        finally:
            manager.close()


if __name__ == "__main__":
    unittest.main()
