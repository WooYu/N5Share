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
