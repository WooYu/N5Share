"""Bounded, cancellable orchestration. The model cannot publish observations."""
import asyncio
from copy import deepcopy
import json
import threading
import time
import uuid

from .deepseek import ModelError, validate_action
from .tools import (ToolError, TOOL_SCHEMAS, REVIEWERS, FINDINGS, RESOLUTIONS,
                    REQUIRED_CHANGES, ORIGINAL_DIFF, allowed_tools, execute, accept_outing, feasible_venues)

SCENARIOS = {"react", "plan", "supervisor", "hierarchical", "swarm", "dual", "review"}
TERMINAL = {"completed", "needs_human", "failed", "cancelled", "stopped"}


class Run:
    def __init__(self, scenario, weather, budget, client, *, model_limit=12, tool_limit=20, seconds=480):
        self.id = uuid.uuid4().hex
        self.scenario, self.client = scenario, client
        self.model_limit, self.tool_limit, self.seconds = model_limit, tool_limit, seconds
        self.started = time.monotonic()
        self.status, self.error = "running", None
        self.events = []
        self.state = {"status": "running", "constraints": {"weather": weather, "budget": budget, "people": "两大一小"},
                      "weather": None, "venues": [], "budget_used": None, "itinerary": None,
                      "costs": {}, "budget_checks": {}, "version": 0, "control_owner": None,
                      "execution_actor": None}
        if scenario == "review":
            self.state.update(diff=ORIGINAL_DIFF, revision=0, review_reports={}, conflicts=[], resolutions={})
        self.writers = {key: "host" for key in self.state}
        self.metrics = {"model_calls": 0, "tool_calls": 0, "input_tokens": 0, "output_tokens": 0}
        self.lock = threading.RLock()
        self.task = None
        self.ended = None

    def snapshot(self):
        with self.lock:
            return {"run_id": self.id, "status": self.status, "error": self.error,
                    "events": deepcopy(self.events), "metrics": {**self.metrics,
                    "elapsed_seconds": round((self.ended or time.monotonic()) - self.started, 2)}}

    def guard(self):
        if self.status == "cancelled":
            raise asyncio.CancelledError()
        if self.status != "running":
            raise ModelError("运行已结束。")
        if time.monotonic() - self.started >= self.seconds:
            raise ModelError("已达到墙钟时间预算，运行停止。")

    def emit(self, actor, kind, title, detail="", payload=None, updates=None):
        with self.lock:
            self.guard()
            if len(self.events) >= 180:
                raise ModelError("事件数量达到上限。")
            if updates:
                self.state.update(deepcopy(updates))
                self.state["version"] += 1
                self.writers.update({key: actor for key in updates})
            event = {"id": "e%03d" % (len(self.events) + 1), "actor": actor, "kind": kind,
                     "title": title, "detail": detail, "payload": deepcopy(payload or {}),
                     "state_after": deepcopy(self.state), "highlight": [actor], "writers": deepcopy(self.writers)}
            self.events.append(event)

    def handoff(self, sender, receiver, intention):
        self.emit(sender, "dispatch", sender + " → " + receiver, intention,
                  {"sender": sender, "receiver": receiver, "intent": intention,
                   "correlation_id": self.id, "expected_state_version": self.state["version"]},
                  {"control_owner": receiver, "execution_actor": receiver})

    def delegate(self, sender, receiver, intention):
        self.emit(sender, "dispatch", sender + " 委派 " + receiver, intention,
                  {"sender": sender, "receiver": receiver, "intent": intention,
                   "correlation_id": self.id, "expected_state_version": self.state["version"],
                   "control_owner": sender, "execution_actor": receiver},
                  {"control_owner": sender, "execution_actor": receiver})

    def merge_observation(self, actor, name, observation):
        changes = {}
        if name == "get_weather":
            changes["weather"] = observation["weather"]
        elif name == "search_venue":
            changes.update(venues=observation["venues"], venue_filter=observation["type"])
        elif name == "calculate_cost":
            changes["costs"] = {**self.state["costs"], observation["id"]: observation}
        elif name == "check_budget":
            changes["budget_checks"] = {**self.state["budget_checks"], observation["venue"]: observation}
            changes["budget_used"] = observation["total"]
        elif name == "inspect_review":
            changes["review_evidence"] = {**self.state.get("review_evidence", {}), actor: observation}
        elif name == "get_business_rules":
            changes["business_rules"] = observation
        elif name == "apply_revision":
            changes.update(diff=observation["diff"], revision=observation["revision"], changes=observation["changes"])
        self.emit("host", "observation", "宿主观察：" + name,
                  json.dumps(observation, ensure_ascii=False), {**observation, "requested_by": actor}, changes)
        self.events[-1]["highlight"] = [actor]

    async def request(self, actor, stage, instruction, next_actor="", *, context_state=None):
        with self.lock:
            self.guard()
            if self.metrics["model_calls"] >= self.model_limit:
                raise ModelError("已达到模型调用预算，运行停止。")
            self.metrics["model_calls"] += 1
            state = deepcopy(context_state if context_state is not None else self.state)
            if self.scenario == "hierarchical" and actor == "director":
                state = {key: value for key, value in state.items() if key in {
                    "constraints", "information_report", "finance_report", "version", "control_owner"}}
        context = {"scenario": self.scenario, "actor": actor, "stage": stage,
                   "instruction": instruction + "\n本次结构约束：next_actor 必须原样输出 " +
                                  json.dumps(next_actor, ensure_ascii=False) + "，不得自行推断其他角色。",
                   "expected_next_actor": next_actor,
                   "state": state, "allowed_tools": {name: TOOL_SCHEMAS[name] for name in allowed_tools(self.scenario, actor)},
                   "remaining_model_calls": self.model_limit - self.metrics["model_calls"],
                   "remaining_tool_calls": self.tool_limit - self.metrics["tool_calls"]}
        action, usage = await self.client.complete(context)
        if not isinstance(usage, dict) or any(type(usage.get(k, 0)) is not int or usage.get(k, 0) < 0
                                               for k in ("input_tokens", "output_tokens")):
            raise ModelError("模型用量结构无效。")
        with self.lock:
            for field in ("input_tokens", "output_tokens"):
                self.metrics[field] += usage.get(field, 0)
        self.guard()
        action = validate_action(action)
        if action["next_actor"] != next_actor:
            raise ModelError("模型交接对象不符合当前角色的控制权契约。")
        return action

    def apply(self, actor, action):
        self.emit(actor, "thought", "公开决策摘要", action["summary"])
        if action["plan"]:
            self.emit(actor, "plan", "执行计划", "\n".join(action["plan"]),
                      {"steps": action["plan"]}, {"plan": action["plan"]})
        if action["reflection"]:
            self.emit(actor, "reflection", "反思与修订依据", action["reflection"],
                      updates={"reflection": action["reflection"]})
        for call in action["calls"]:
            with self.lock:
                self.guard()
                if self.metrics["tool_calls"] >= self.tool_limit:
                    raise ModelError("已达到工具调用预算，运行停止。")
                self.metrics["tool_calls"] += 1
            self.emit(actor, "action", "工具请求：" + call["name"],
                      json.dumps(call["arguments"], ensure_ascii=False), call)
            observation = execute(self.scenario, actor, call, self.state)
            self.merge_observation(actor, call["name"], observation)

    async def turn(self, actor, stage, instruction, next_actor=""):
        action = await self.request(actor, stage, instruction, next_actor)
        self.validate_stage(stage, action)
        self.apply(actor, action)
        return action

    def validate_stage(self, stage, action):
        names = [call["name"] for call in action["calls"]]
        result = action["result"]
        if stage in {"plan_v1", "plan_v2", "info_plan", "finance_plan", "delegate_info", "delegate_finance"} or stage.startswith("dispatch_"):
            self.require(not names and result is None, "规划与派遣阶段不得调用工具或发布结果。")
            if stage in {"plan_v1", "plan_v2", "info_plan", "finance_plan", "delegate_info"}:
                self.require(action["plan"], "本阶段必须先给出可执行计划。")
            if stage == "plan_v2":
                self.require(action["reflection"], "修订计划必须提供反思依据。")
        elif stage == "execute_v1":
            expected = [
                {"name": "search_venue", "arguments": {"type": "outdoor"}},
                {"name": "calculate_cost", "arguments": {"venue": "P02"}},
                {"name": "check_budget", "arguments": {"venue": "P02", "total": 270}},
                {"name": "get_weather", "arguments": {}}]
            self.require(action["calls"] == expected and result is None, "v1 执行步骤必须遵守规划器计划并回传观察。")
        elif stage == "execute_v2":
            pending = self.v2_pending_calls
            self.require(action["calls"] and action["calls"] == pending[:len(action["calls"])] and result is None,
                         "v2 只能执行当前计划尚未完成的连续步骤；不能跳过费用核验、重复已执行步骤或自行改计划。")
        elif stage == "weather":
            self.require(names == ["get_weather"] and result is None, "天气角色只能查天气并回传。")
        elif stage == "venue":
            self.require(names == ["search_venue"], "场馆角色必须查询场馆资料。")
            if self.scenario in {"supervisor", "swarm"}:
                self.require(result and result["status"] == "candidate", "场馆角色必须提交候选供预算角色核验。")
            else:
                self.require(result is None, "场馆角色不得提前验收。")
        elif stage in {"ticket", "budget"}:
            if self.scenario in {"supervisor", "swarm"}:
                selected = self.state.get("selected_venue")
                self.require(names == ["calculate_cost", "check_budget"] and all(
                    c["arguments"].get("venue") == selected for c in action["calls"]) and result is None,
                    "预算角色只能核验已选择的候选，超预算必须回报，不能自行换场馆。")
            else:
                self.require(result is None, "财务子角色不能提前验收。")
        elif stage == "final":
            self.require(not names and result and result["status"] in {"completed", "needs_human"},
                         "最终汇总只能提交有工具证据的结果。")
        elif stage in {"review_0", "review_1"}:
            self.require(names == ["inspect_review"] and result and result["status"] == "report",
                         "审查角色必须请求本角色资料并回报发现。")
        elif stage == "arbitrate":
            self.require(names == ["get_business_rules"] and result and result["status"] == "arbitrated",
                         "仲裁必须请求业务规则，不允许直接修订。")
        elif stage == "revise":
            self.require(names == ["apply_revision"] and result is None, "修订阶段只能提交修订工具请求。")
        elif stage == "review_final":
            self.require(not names and result == {"status": "review_passed"}, "终审只能依据复审证据汇总。")

    def complete_outing(self, actor, result):
        with self.lock:
            self.guard()
            itinerary = accept_outing(result, self.state)
            status = "completed" if itinerary else "needs_human"
            self.emit("host", "done", "宿主验收通过" if itinerary else "无可行方案，需调整约束或转人工",
                      "依据已执行工具的天气、完整费用与预算证据。" if itinerary else "本次未通过出游验收。",
                      {"status": status, "submitted_by": actor},
                      {"itinerary": itinerary, "status": status, "control_owner": None, "execution_actor": None})
        self.status, self.ended = status, time.monotonic()

    def final_outing_instruction(self):
        limit = self.state["constraints"]["budget"]
        return (
            f"本次任务唯一的预算上限为 {limit} 元，以 state.constraints.budget 为准，不得替换成其他情景的预算。"
            "依据共享状态或两份组报告里的实际天气、完整费用和 budget_checks 结果提交最终 result。"
            "若存在天气可行且已通过预算工具核验的场馆，返回 completed，venue 与 total 必须与该场馆工具证据一致。"
            "只有完整检索证明本次预算下确实没有可行候选时，才能返回 needs_human。"
            "本轮只汇总，不改计划：calls=[]，plan=[]，reflection=空字符串。停止条件由宿主独立验收。"
        )

    def require(self, condition, message):
        if not condition:
            raise ModelError(message)

    def v2_required_calls(self):
        calls = [{"name": "get_weather", "arguments": {}},
                 {"name": "search_venue", "arguments": {"type": "indoor" if self.state["weather"] == "rain" else "all"}}]
        candidates = feasible_venues(self.state)
        if candidates:
            selected = next((venue for venue in candidates if venue["id"] == "P03"), candidates[0])
            calls += [{"name": "calculate_cost", "arguments": {"venue": selected["id"]}},
                      {"name": "check_budget", "arguments": {"venue": selected["id"], "total": selected["total"]}}]
        return calls

    async def react(self):
        self.handoff("supervisor", "executor", "单 Agent 自主选择下一步工具")
        while self.status == "running":
            action = await self.turn("executor", "react", "先查天气，再检索符合天气的场馆（晴天检索 all）。根据观察算完整费用并核对预算。已有证据齐备则给出 result；无可行则 needs_human。允许一轮顺序请求多个已知参数工具。")
            if action["result"] is not None:
                self.complete_outing("executor", action["result"])
            else:
                self.require(action["calls"], "ReAct 没有工具请求或结果，无法继续。")

    async def planned(self, dual=False):
        planner = "planner"
        executor = "executor" if dual else "planner"
        first = await self.turn(planner, "plan_v1", "教学计划 v1：先选 P02 植物园，再算门票、交通、餐费，再核对预算，最后确认天气可行性。费用齐全但天气顺序故意滞后；仅产出 plan，calls=[]，result=null。", executor)
        self.require(first["plan"] and not first["calls"] and first["result"] is None,
                     "规划器必须给出计划，不能代替执行器执行或验收。")
        self.handoff(planner, executor, "执行计划 v1；遇到计划外情况回传，不自行改计划")
        action = await self.turn(executor, "execute_v1", "按 v1 顺序执行 search_venue(outdoor)、calculate_cost(P02)、check_budget(P02,270)、get_weather()。必须完整执行四个工具，result=null；将观察交回规划器。", planner)
        self.require([c["name"] for c in action["calls"]] == ["search_venue", "calculate_cost", "check_budget", "get_weather"] and
                     action["calls"][0]["arguments"] == {"type": "outdoor"} and
                     action["calls"][1]["arguments"] == {"venue": "P02"} and
                     action["calls"][2]["arguments"] == {"venue": "P02", "total": 270} and action["result"] is None,
                     "执行器必须遵守 v1 步骤并将工具观察回传。")
        failed = self.state["weather"] == "rain" or not self.state["budget_checks"]["P02"]["within_budget"]
        self.handoff(executor, planner, "v1 失败：天气不允许户外或总费用超预算" if failed else "v1 证据齐备，提交规划器验收")
        if failed:
            reason = "天气依赖顺序错误：选场馆前必须先查天气并过滤类型。" if self.state["weather"] == "rain" else "所选场馆超过本次预算；需要重新选择。"
            self.emit(executor, "report", "执行失败观察回传", reason, {"failed": True})
            if not dual:
                with self.lock:
                    self.guard()
                    self.emit("host", "done", "计划 v1 执行失败，停在失败现场",
                              reason + "本页只执行 v1；后续课件讨论反思与 v2 修订。本次未通过验收。",
                              {"status": "needs_human", "reason": "plan_v1_failed",
                               "failure": "weather_dependency" if self.state["weather"] == "rain" else "budget"},
                              {"status": "needs_human", "control_owner": None, "execution_actor": None})
                    self.status, self.ended = "needs_human", time.monotonic()
                return
            revised = await self.turn(planner, "plan_v2", "根据失败观察反思并给出计划 v2：查天气→按天气过滤→选符合预算场馆→算完整费用→核对预算。雨天优先P03，200元选P04；晴天低预算考虑P01。给出非空 reflection 和 plan，不调用工具，result=null。", executor)
            self.require(revised["reflection"] and revised["plan"] and not revised["calls"] and revised["result"] is None,
                         "v2 必须由规划器给出可执行修订与反思。")
            self.handoff(planner, executor, "执行修订后的计划 v2")
            self.v2_pending_calls = self.v2_required_calls()
            completed_steps = []
            while self.v2_pending_calls:
                remaining = json.dumps(self.v2_pending_calls, ensure_ascii=False)
                action = await self.turn(executor, "execute_v2",
                    "继续执行同一份已修订教学计划 v2，不得自行改变规划器计划。"
                    "当前尚未执行的连续工具步骤为：" + remaining +
                    "。可以一次提交全部剩余步骤，也可以只提交当前连续前置步骤，等待宿主观察后继续；"
                    "不得跳步、重复已经完成的步骤或提前宣称结束。result=null。"
                    "next_actor 按结构约束填 planner，但宿主仅在全部步骤及工具证据齐备后才实际交接；"
                    "步骤未完时控制权保留在 executor。", planner)
                completed_steps.extend(call["name"] for call in action["calls"])
                self.v2_pending_calls = self.v2_pending_calls[len(action["calls"]):]
                self.emit("host", "report", "v2 执行进度",
                          "步骤尚未完成，执行器继续处理当前计划。" if self.v2_pending_calls else "当前计划工具步骤已完成，可以回传规划器。",
                          updates={"execution_progress": {"phase": "v2", "completed": completed_steps,
                                   "remaining": [call["name"] for call in self.v2_pending_calls]}})
            self.handoff(executor, planner, "回传 v2 工具证据与预算结论")
        final = await self.turn(planner, "final", self.final_outing_instruction())
        self.require(not final["calls"], "最终汇总阶段不得补造工具执行。")
        self.complete_outing(planner, final["result"])

    async def supervisor(self):
        async def dispatch(actor, instruction):
            await self.turn("supervisor", "dispatch_" + actor,
                            "根据当前回报派遣 " + actor + "；calls=[]，result=null。", actor)
            self.delegate("supervisor", actor, instruction)
            response = await self.turn(actor, actor, instruction, "supervisor")
            self.handoff(actor, "supervisor", "工具观察与候选回报")
            return response
        await dispatch("weather", "调用 get_weather，result=null。")
        for attempt in range(2):
            action = await dispatch("venue", self.candidate_instruction(attempt))
            self.select_candidate(action["result"])
            await dispatch("budget", "只对 selected_venue 调用 calculate_cost 和 check_budget，不可自行换场馆。result=null；将预算是否通过交回主管。")
            if self.record_budget_result():
                break
        final = await self.turn("supervisor", "final", self.final_outing_instruction())
        self.complete_outing("supervisor", final["result"])

    def candidate_instruction(self, attempt):
        selection = ("第一候选：雨天选 P03 科技馆，晴天选 P02 植物园，交给预算角色核验。"
                     if attempt == 0 else "上一候选超预算，改选雨天 P04 美术馆或晴天 P01 城市公园。")
        return ("先按已观察天气调用 search_venue（雨天indoor、晴天all）。" + selection +
                " result 必须是 {status:'candidate',venue:'对应编号'}，不得宣布完成。")

    def select_candidate(self, result):
        venue = next((v for v in self.state["venues"] if v["id"] == result["venue"]), None)
        self.require(venue and (self.state["weather"] == "sun" or venue["type"] == "indoor") and
                     venue["id"] not in self.state.get("rejected_venues", []),
                     "候选不在当前天气允许的检索证据中，或重复选择已拒绝候选。")
        self.emit("venue", "report", "场馆角色提出候选", venue["name"], result,
                  {"selected_venue": venue["id"]})

    def record_budget_result(self):
        identifier = self.state["selected_venue"]
        evidence = self.state["budget_checks"].get(identifier)
        self.require(evidence, "预算角色未完成所选候选的预算工具核验。")
        if evidence["within_budget"]:
            return True
        rejected = self.state.get("rejected_venues", []) + [identifier]
        self.emit("host", "report", "候选超预算，需回传并重新选择", "预算角色没有更换场馆权限。",
                  evidence, {"rejected_venues": rejected})
        return False

    async def hierarchical(self):
        action = await self.turn("director", "delegate_info", "派遣信息组；plan 写明由 weather 查天气、venue 按天气筛选。calls=[] result=null。", "info_lead")
        self.require(action["plan"] and action["result"] is None, "总管需声明分组计划。")
        self.handoff("director", "info_lead", "取得信息组报告")
        action = await self.turn("info_lead", "info_plan", "plan 写明 weather 查天气→venue 按天气筛选；calls=[] result=null。", "weather")
        self.require(action["plan"] and action["result"] is None, "信息组长需声明子步骤。")
        for actor, instruction in (("weather", "调用 get_weather。"),
                                   ("venue", "根据天气调用 search_venue，雨天 indoor，晴天 all。")):
            self.handoff("info_lead", actor, "执行信息组计划")
            result = await self.turn(actor, actor, instruction + " result=null。", "info_lead")
            self.require(result["result"] is None, "信息组成员只回报观察。")
            self.handoff(actor, "info_lead", "组内回报")
        info = {"weather": self.state["weather"], "venues": self.state["venues"]}
        self.emit("info_lead", "report", "信息组汇总", "天气与候选场馆已确认。", info, {"information_report": info})
        self.handoff("info_lead", "director", "只上报信息组摘要")
        action = await self.turn("director", "delegate_finance", "根据信息组报告派财务组核算；calls=[] result=null。", "finance_lead")
        self.require(action["result"] is None, "总管尚无预算验收证据。")
        self.handoff("director", "finance_lead", "取得财务组报告")
        await self.turn("finance_lead", "finance_plan", "plan 写明 ticket 计算候选费用→budget 校验预算；无可行候选则记录没有候选。calls=[] result=null。", "ticket")
        self.handoff("finance_lead", "ticket", "计算合适候选的完整费用")
        await self.turn("ticket", "ticket", "选择预算内场馆，调用 calculate_cost。雨天300优先P03、200选P04，晴天预算不足选P01。100元则 calls=[]。result=null。", "finance_lead")
        self.handoff("ticket", "finance_lead", "票务核算回报")
        self.handoff("finance_lead", "budget", "执行财务组计划的预算核验")
        await self.turn("budget", "budget", "根据 costs 中实际费用调用 check_budget。没有可行候选则 calls=[]。result=null。", "finance_lead")
        self.handoff("budget", "finance_lead", "预算核验回报")
        finance = {"costs": self.state["costs"], "budget_checks": self.state["budget_checks"]}
        self.emit("finance_lead", "report", "财务组汇总", "完整费用及预算结论。", finance, {"finance_report": finance})
        self.handoff("finance_lead", "director", "只上报财务组摘要")
        final = await self.turn("director", "final", self.final_outing_instruction())
        self.complete_outing("director", final["result"])

    async def swarm(self):
        await self.turn("weather", "weather", "调用 get_weather，result=null。直接将控制权交给 venue。", "venue")
        self.handoff("weather", "venue", "天气角色直接交接给场馆角色")
        for attempt in range(2):
            action = await self.turn("venue", "venue", self.candidate_instruction(attempt), "budget")
            self.select_candidate(action["result"])
            self.handoff("venue", "budget", "对等交接：核验当前候选")
            selected = next(v for v in self.state["venues"] if v["id"] == self.state["selected_venue"])
            target = "venue" if attempt == 0 and selected["total"] > self.state["constraints"]["budget"] else ""
            await self.turn("budget", "budget", "只对 selected_venue 调用 calculate_cost 和 check_budget。result=null。超预算必须回传场馆角色，由它换候选；预算角色不可自行修改选择。", target)
            if self.record_budget_result():
                break
            if target:
                self.handoff("budget", "venue", "超预算，退回对等场馆角色换候选")
        final = await self.turn("budget", "final", self.final_outing_instruction())
        self.complete_outing("budget", final["result"])

    async def review_round(self, revision):
        # Independent snapshot per role; merge serially by role namespace.
        snapshot = deepcopy(self.state)
        self.emit("supervisor", "dispatch", "并行派发四个独立审查角色", "同一状态版本，不同工具资料权限。",
                  {"receivers": list(REVIEWERS), "expected_state_version": snapshot["version"], "revision": revision})
        async def request_report(actor):
            return await self.request(actor, "review_" + str(revision),
                "调用 inspect_review(revision=" + str(revision) + ")，result={status:'report',findings:[本角色问题ID],revision:" + str(revision) + "}。"
                + ("初审本角色问题ID必须覆盖：" + ",".join(FINDINGS[actor]) if revision == 0 else "修订后检查新版，预期已解决问题则 findings=[]。")
                + "只使用自己权限范围的证据。", "supervisor", context_state=snapshot)
        tasks = [asyncio.create_task(request_report(actor)) for actor in REVIEWERS]
        try:
            actions = await asyncio.gather(*tasks)
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        for actor, action in zip(REVIEWERS, actions):
            self.validate_stage("review_" + str(revision), action)
            self.apply(actor, action)
            evidence = self.state.get("review_evidence", {}).get(actor)
            result = action["result"]
            self.require(len(action["calls"]) == 1 and action["calls"][0]["name"] == "inspect_review" and
                         evidence and result and result["status"] == "report" and
                         result["revision"] == revision and set(result["findings"]) == set(evidence["findings"]),
                         "审查报告缺少本角色已执行的工具证据或版本不匹配。")
            reports = {**self.state["review_reports"], actor: result}
            self.emit(actor, "finding" if revision == 0 else "review", "初审发现" if revision == 0 else "修订后复审",
                      ", ".join(result["findings"]) or "教学规则检查通过（不是实际编译/安全扫描）。", result,
                      {"review_reports": reports})

    async def review(self):
        await self.review_round(0)
        self.emit("supervisor", "conflict", "汇总后检测到两类争议", "审计可靠性与同步开销；值对象建议与未经测量的分配担忧。",
                  updates={"conflicts": ["audit", "allocation"]})
        action = await self.turn("supervisor", "arbitrate", "先调用 get_business_rules，再按业务事实给 result={status:'arbitrated',resolutions:" + json.dumps(RESOLUTIONS) + "}。审计保留、异步落库、持久本地兜底；对象分配未测量，不能声称六数量级。")
        result = action["result"]
        self.require(self.state.get("business_rules") and result and result["status"] == "arbitrated" and result["resolutions"] == RESOLUTIONS,
                     "仲裁必须依据已执行工具返回的业务规则。")
        self.emit("supervisor", "arbitration", "业务事实驱动的仲裁", action["summary"], result,
                  {"resolutions": result["resolutions"]})
        action = await self.turn("supervisor", "revise", "调用 apply_revision，changes 必须完整包含 " + json.dumps(sorted(REQUIRED_CHANGES)) + "。宿主生成修订代码产物。result=null。")
        self.require(self.state.get("revision") == 1 and action["result"] is None, "修订未由宿主执行。")
        self.emit("supervisor", "revision", "生成修订产物，退回原角色复审", "清空初审证据，复审必须读取 revision=1。",
                  updates={"review_evidence": {}, "review_reports": {}})
        await self.review_round(1)
        action = await self.turn("supervisor", "review_final", "四个角色已独立复审新版本。无未解决问题则返回 result={status:'review_passed'}，calls=[]；说明仅为课程合成规则检查。")
        reports = self.state["review_reports"]
        self.require(action["result"] == {"status": "review_passed"} and not action["calls"] and
                     set(reports) == set(REVIEWERS) and all(r["revision"] == 1 and not r["findings"] for r in reports.values()),
                     "四个角色尚未基于修订产物完成复审。")
        with self.lock:
            self.guard()
            self.emit("host", "done", "多角色复审通过", "完成课程合成资料的审查闭环；未执行真实编译、压测或安全扫描。",
                      {"status": "completed", "scope": "synthetic_review_workflow"},
                      {"status": "completed", "control_owner": None, "execution_actor": None})
            self.status, self.ended = "completed", time.monotonic()

    async def run(self):
        try:
            async with asyncio.timeout(self.seconds):
                if self.scenario == "plan":
                    await self.planned(False)
                elif self.scenario == "dual":
                    await self.planned(True)
                else:
                    await getattr(self, self.scenario)()
        except asyncio.CancelledError:
            self.stop("cancelled", "用户已取消，正在进行的模型请求已中断。")
        except TimeoutError:
            self.stop("failed", "已达到墙钟预算，运行停止。")
        except (ModelError, ToolError) as exc:
            self.stop("failed", str(exc))
        except Exception:
            self.stop("failed", "本地运行异常，已停止；未回退为离线剧本。")

    def stop(self, status, error):
        with self.lock:
            if self.status in TERMINAL:
                return
            self.state.update(status=status, control_owner=None, execution_actor=None)
            self.state["version"] += 1
            self.writers.update({key: "host" for key in ("status", "control_owner", "execution_actor", "version")})
            self.events.append({"id": "e%03d" % (len(self.events) + 1), "actor": "host",
                "kind": "done", "title": "运行已取消" if status == "cancelled" else "运行失败",
                "detail": error, "payload": {"status": "stopped", "run_status": status},
                "state_after": deepcopy(self.state), "highlight": [], "writers": deepcopy(self.writers)})
            self.status, self.error, self.ended = status, error, time.monotonic()


class RunManager:
    def __init__(self, client, *, max_active=2, max_retained=16):
        self.client, self.max_active, self.max_retained = client, max_active, max_retained
        self.runs, self.lock = {}, threading.RLock()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, name="n5-runtime", daemon=True)
        self.thread.start()

    def start(self, scenario, weather, budget):
        with self.lock:
            active = [r for r in self.runs.values() if r.status == "running"]
            if len(active) >= self.max_active:
                raise ModelError("同时运行数量已达上限，请等待或取消旧运行。")
            expired = [key for key, run in self.runs.items() if run.status != "running" and time.monotonic() - run.started > 3600]
            for key in expired:
                del self.runs[key]
            while len(self.runs) >= self.max_retained:
                key = next((key for key, run in self.runs.items() if run.status != "running"), None)
                if key is None:
                    raise ModelError("运行存储已满。")
                del self.runs[key]
            run = Run(scenario, weather, budget, self.client)
            self.runs[run.id] = run
            run.task = asyncio.run_coroutine_threadsafe(run.run(), self.loop)
            return run

    def get(self, identifier):
        with self.lock:
            return self.runs.get(identifier)

    def cancel(self, identifier):
        run = self.get(identifier)
        if run:
            run.stop("cancelled", "用户取消运行；不会继续发布成功结果。")
            if run.task:
                run.task.cancel()
        return run

    def close(self):
        for identifier in list(self.runs):
            self.cancel(identifier)
        async def drain():
            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.run_coroutine_threadsafe(drain(), self.loop).result(timeout=5)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=5)
        self.loop.close()
