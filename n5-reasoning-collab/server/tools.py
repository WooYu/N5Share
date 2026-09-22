"""Host-owned synthetic facts, role permissions and acceptance evidence."""
from copy import deepcopy

VENUES = [
    {"id": "P01", "name": "城市公园", "type": "outdoor", "tickets": 0, "transport": 40, "meal": 80},
    {"id": "P02", "name": "植物园", "type": "outdoor", "tickets": 150, "transport": 40, "meal": 80},
    {"id": "P03", "name": "科技馆", "type": "indoor", "tickets": 90, "transport": 40, "meal": 80},
    {"id": "P04", "name": "美术馆", "type": "indoor", "tickets": 80, "transport": 40, "meal": 80},
]
for venue in VENUES:
    venue["total"] = venue["tickets"] + venue["transport"] + venue["meal"]

ORIGINAL_DIFF = '''@GetMapping("/orders")
public List<OrderVO> list(@RequestParam BigDecimal minAmount,
    @RequestParam BigDecimal maxAmount, @RequestParam String userId) {
    log.info("query orders userId={} min={} max={}", userId, minAmount, maxAmount);
    List<Order> orders = orderMapper.selectByAmountRange(minAmount, maxAmount);
    List<OrderVO> result = new ArrayList<>();
    for (Order o : orders) {
        User u = userMapper.selectById(o.getUserId());
        result.add(OrderVO.of(o, u));
    }
    return result;
}'''

# This artifact is teaching pseudocode: it is neither deployed nor executed Java.
REVISED_DIFF = '''// 教学修订产物；本课件不部署或执行 Java 服务。
@GetMapping("/orders")
public Page<OrderVO> list(Authentication auth, AmountRange range, PageRequest page) {
    range.validateNonNegativeAndOrdered();
    String owner = auth.getName();
    page.requireBoundedSize(100);
    return orderQueryService.findOwnedOrders(owner, range, page);
}
// OrderQueryService: WHERE owner_id=:owner AND amount BETWEEN :min AND :max
// JOIN users ON users.id=orders.user_id; LIMIT :pageSize OFFSET :offset
// Schema migration: CREATE INDEX ix_order_owner_amount ON orders(owner_id, amount)
// Audit: authenticated actor + timestamp + amount range, restricted audit channel.
// First append to durable local outbox; asynchronous worker persists audit records.
// Fail closed if durable outbox cannot accept; retries + deduplication + alerts.
// Ordinary logs contain request correlation id only, no userId or amount range.
// Tests: cross-owner access denied; negative, reversed range; empty page;
// pagination bounds; audit outage/outbox failure; joined query count bounded.
'''

REVIEWERS = ("security_reviewer", "performance_reviewer", "readability_reviewer", "test_reviewer")
FINDINGS = {
    "security_reviewer": ["F-AUTHZ", "F-LOG-PII", "F-AUDIT"],
    "performance_reviewer": ["F-NPLUS1", "F-INDEX", "F-PAGING", "C-SYNC-AUDIT", "C-ALLOCATION"],
    "readability_reviewer": ["F-RESPONSIBILITY", "F-AMOUNT-RANGE"],
    "test_reviewer": ["F-BOUNDARY-TESTS"],
}
REVIEW_FACTS = {
    "security_reviewer": {"permissions": "请求 userId 不能作为身份；必须认证身份并校验订单归属。",
                          "logging": "普通日志不得输出身份与金额；敏感查询必须记录受限审计事件。"},
    "performance_reviewer": {"call_chain": "原代码查询订单后逐个 selectById，N+1。",
                             "schema": "原表缺少 owner_id,amount 索引；未分页。",
                             "concerns": "同步审计可能增加等待；AmountRange 分配成本尚无测量证据。"},
    "readability_reviewer": {"style": "控制器负责参数绑定，查询服务负责权限范围与装配；金额用 AmountRange。"},
    "test_reviewer": {"coverage": "原代码未覆盖越权、负数、倒置区间、空结果、分页或审计故障。"},
}
REQUIRED_CHANGES = {"authenticated_owner", "redact_logs", "async_audit_durable_outbox",
                    "join_and_index", "bounded_pagination", "amount_range_service", "boundary_tests"}
RESOLUTIONS = {"audit": "async_audit_with_durable_fallback",
               "allocation": "measure_before_rejecting_amount_range"}
TOOL_SCHEMAS = {
    "get_weather": {}, "search_venue": {"type": "indoor|outdoor|all"},
    "calculate_cost": {"venue": "P01|P02|P03|P04"},
    "check_budget": {"venue": "P01|P02|P03|P04", "total": "整数（必须等于已计算费用）"},
    "inspect_review": {"revision": "0 或 1"}, "get_business_rules": {},
    "apply_revision": {"changes": sorted(REQUIRED_CHANGES)},
}


class ToolError(Exception):
    pass


def allowed_tools(scenario, actor):
    if scenario == "review":
        return {"inspect_review"} if actor in REVIEWERS else {"get_business_rules", "apply_revision"}
    if scenario in {"react", "plan"}:
        return {"get_weather", "search_venue", "calculate_cost", "check_budget"}
    if scenario == "dual":
        return {"get_weather", "search_venue", "calculate_cost", "check_budget"} if actor == "executor" else set()
    return {"weather": {"get_weather"}, "venue": {"search_venue"},
            "ticket": {"calculate_cost"}, "budget": {"calculate_cost", "check_budget"}}.get(actor, set())


def _arguments(arguments, fields):
    if set(arguments) != set(fields):
        raise ToolError("工具参数字段不符合契约。")


def execute(scenario, actor, call, state):
    name, arguments = call["name"], call["arguments"]
    if name not in allowed_tools(scenario, actor):
        raise ToolError("当前角色无权执行工具：" + name[:80])
    _arguments(arguments, TOOL_SCHEMAS[name])
    if name == "get_weather":
        return {"weather": state["constraints"]["weather"], "day": "周六", "source": "课程合成天气"}
    if name == "search_venue":
        category = arguments["type"]
        if category not in ("indoor", "outdoor", "all"):
            raise ToolError("场馆类型无效。")
        return {"type": category, "venues": deepcopy([v for v in VENUES if category == "all" or v["type"] == category]),
                "source": "课程合成场馆资料"}
    if name == "calculate_cost":
        venue = next((v for v in state.get("venues", []) if v["id"] == arguments["venue"]), None)
        if venue is None:
            raise ToolError("必须先检索场馆，才能计算该场馆费用。")
        return deepcopy(venue)
    if name == "check_budget":
        cost = state.get("costs", {}).get(arguments["venue"])
        total = arguments["total"]
        if cost is None or type(total) is not int or total != cost["total"]:
            raise ToolError("预算请求费用与已执行工具证据不符。")
        return {"venue": arguments["venue"], "total": total, "limit": state["constraints"]["budget"],
                "within_budget": total <= state["constraints"]["budget"]}
    if name == "inspect_review":
        revision = arguments["revision"]
        if type(revision) is not int or revision != state.get("revision", 0):
            raise ToolError("审查的修订版本已过期或不存在。")
        return {"revision": revision, "diff": state["diff"], "facts": deepcopy(REVIEW_FACTS[actor]),
                "findings": list(FINDINGS[actor]) if revision == 0 else [],
                "scope": actor, "source": "课程合成代码与规则；不是编译、压测或真实安全扫描"}
    if name == "get_business_rules":
        return {"sensitive_order_data": True, "audit_required": True, "high_qps": True,
                "allocation_profile": "尚未测量，不能断言数量级差异",
                "durability": "先持久接收，异步落库，失败重试；本地队列满时必须明确失败"}
    if name == "apply_revision":
        changes = arguments["changes"]
        if state.get("resolutions") != RESOLUTIONS or not state.get("business_rules"):
            raise ToolError("必须先基于业务事实完成仲裁，才能修订。")
        if not isinstance(changes, list) or any(not isinstance(c, str) for c in changes) or set(changes) != REQUIRED_CHANGES or len(changes) != len(REQUIRED_CHANGES):
            raise ToolError("修订必须覆盖全部已确认问题。")
        return {"revision": 1, "diff": REVISED_DIFF, "changes": sorted(changes),
                "scope": "宿主从已验证修订清单生成的教学代码产物，未声称实际运行测试"}
    raise ToolError("未知工具。")


def feasible_venues(state):
    weather = state.get("weather")
    if weather not in ("sun", "rain"):
        return []
    return [v for v in VENUES if (weather == "sun" or v["type"] == "indoor")
            and v["total"] <= state["constraints"]["budget"]]


def accept_outing(result, state):
    if not result or result["status"] not in {"completed", "needs_human"}:
        raise ToolError("尚未提交可验收的出游结果。")
    if not state.get("weather") or not state.get("venues"):
        raise ToolError("未执行天气和场馆工具，不能验收。")
    feasible = feasible_venues(state)
    if result["status"] == "needs_human":
        category = state.get("venue_filter")
        exhaustive = category == "all" or (state["weather"] == "rain" and category == "indoor")
        if feasible or not exhaustive:
            raise ToolError("现有证据不足以断言无可行方案。")
        return None
    identifier, total = result["venue"], result["total"]
    evidence = state.get("budget_checks", {}).get(identifier)
    cost = state.get("costs", {}).get(identifier)
    if not evidence or not cost or not evidence["within_budget"] or total != cost["total"] or not any(v["id"] == identifier for v in feasible):
        raise ToolError("结果未通过宿主验收：天气、完整费用或预算工具证据不符。")
    return {"venue": identifier, "name": cost["name"], "total": total, "day": "周六半日", "people": "两大一小"}
