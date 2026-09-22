import unittest
from server.deepseek import ModelError, parse_json, validate_action
from server.tools import VENUES, ToolError, execute, accept_outing


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.state = {"constraints": {"weather": "rain", "budget": 300},
                      "weather": "rain", "venues": VENUES, "costs": {}, "budget_checks": {}}

    def test_full_costs(self):
        self.assertEqual({v["id"]: v["total"] for v in VENUES}, {"P01": 120, "P02": 270, "P03": 210, "P04": 200})

    def test_permissions_are_role_specific(self):
        with self.assertRaises(ToolError):
            execute("supervisor", "weather", {"name": "calculate_cost", "arguments": {"venue": "P03"}}, self.state)
        with self.assertRaises(ToolError):
            execute("dual", "planner", {"name": "get_weather", "arguments": {}}, self.state)
        with self.assertRaises(ToolError):
            execute("review", "security_reviewer", {"name": "get_business_rules", "arguments": {}}, self.state)

    def test_cost_requires_search_and_budget_requires_actual_cost(self):
        self.state["venues"] = []
        with self.assertRaises(ToolError):
            execute("react", "executor", {"name": "calculate_cost", "arguments": {"venue": "P03"}}, self.state)
        with self.assertRaises(ToolError):
            execute("react", "executor", {"name": "check_budget", "arguments": {"venue": "P03", "total": 210}}, self.state)

    def test_success_requires_tools_and_rejects_forged_result(self):
        with self.assertRaises(ToolError):
            accept_outing({"status": "completed", "venue": "P03", "total": 210}, self.state)
        cost = execute("react", "executor", {"name": "calculate_cost", "arguments": {"venue": "P03"}}, self.state)
        self.state["costs"]["P03"] = cost
        self.state["budget_checks"]["P03"] = execute("react", "executor", {"name": "check_budget", "arguments": {"venue": "P03", "total": 210}}, self.state)
        self.assertEqual(accept_outing({"status": "completed", "venue": "P03", "total": 210}, self.state)["total"], 210)
        with self.assertRaises(ToolError):
            accept_outing({"status": "completed", "venue": "P03", "total": 190}, self.state)

    def test_no_feasible_requires_complete_weather_filtered_evidence(self):
        self.state["constraints"]["budget"] = 100
        self.state["venue_filter"] = "outdoor"
        with self.assertRaises(ToolError):
            accept_outing({"status": "needs_human"}, self.state)
        self.state["venue_filter"] = "indoor"
        self.assertIsNone(accept_outing({"status": "needs_human"}, self.state))
        self.state["constraints"]["budget"] = 200
        with self.assertRaises(ToolError):
            accept_outing({"status": "needs_human"}, self.state)

    def test_json_schema_is_strict(self):
        with self.assertRaises(ValueError):
            parse_json('{"a":1,"a":2}')
        with self.assertRaises(ValueError):
            parse_json('{"a":NaN}')
        base = dict(summary="test", calls=[], plan=[], reflection="", next_actor="", result=None)
        self.assertEqual(validate_action(base), base)
        with self.assertRaises(ModelError):
            validate_action({**base, "observation": {"weather": "sun"}})
        with self.assertRaises(ModelError):
            validate_action({**base, "result": {"status": "completed", "venue": "P03", "total": True}})


if __name__ == "__main__":
    unittest.main()
