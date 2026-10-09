import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "python"
load_dotenv(Path(__file__).with_name(".env"))
CORPUS = json.loads((ROOT / "data" / "corpus.json").read_text(encoding="utf-8"))


def make_model(check_only=False):
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not check_only and (not key or key == "replace-with-your-key"):
        raise ValueError("Set DEEPSEEK_API_KEY in the environment or python/.env")
    return ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=key or "check-only-no-api-call",
        temperature=0.2,
        max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", "1600")),
        timeout=45,
        max_retries=0,
    )


@tool
def search_tool(query: str) -> str:
    """Search the LOCAL training corpus; this tool does not search the internet."""
    terms = query.lower().split()
    matches = [item for item in CORPUS if any(
        term in (item["title"] + item["text"]).lower() for term in terms
    )]
    return json.dumps({"source": "local training corpus",
                       "fallback_to_full_corpus": not bool(matches),
                       "items": matches or CORPUS}, ensure_ascii=False)


@tool
def analyze_tool(data: str) -> str:
    """Count input characters and referenced source IDs; no fabricated market data."""
    sources = [item["id"] for item in CORPUS if item["id"] in data]
    return json.dumps({"characters": len(data), "cited_sources": sources,
                       "source_count": len(sources)}, ensure_ascii=False)


@tool
def write_tool(content: str) -> str:
    """Save a report only to the fixed training output path and return that path."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / "agent_report.md"
    destination.write_text(content, encoding="utf-8")
    return str(destination)


@tool
def design_tool(requirement: str) -> str:
    """Return a teaching architecture template for the supplied requirement."""
    return json.dumps({"requirement": requirement,
                       "kind": "teaching template, not generated software",
                       "modules": ["input", "state", "workflow", "output"],
                       "boundaries": ["validate input", "limit steps", "record sources"]})


@tool
def code_tool(spec: str) -> str:
    """Write a validated multi-file JSON bundle to the host-selected product run only."""
    root = product_workspace()
    from product_team.workspace import write_bundle, revision, read_sources
    from product_team.delivery import run_lock, write_json
    with run_lock(root):
        write_bundle(root, json.loads(spec))
        state_path = root / 'state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding='utf-8'))
            state.update(status='needs_review', review={}, tests={})
            state.pop('human_decision', None)
            write_json(state_path, state)
        return json.dumps({'revision': revision(root), 'files': list(read_sources(root / 'candidate')),
                           'status': 'needs_review'}, ensure_ascii=False)


@tool
def test_tool() -> str:
    """Execute external HTTP and browser business acceptance in Docker for the selected run."""
    root = product_workspace()
    from product_team.acceptance import run_acceptance
    from product_team.delivery import run_lock
    with run_lock(root):
        return json.dumps(run_acceptance(root), ensure_ascii=False)


def product_workspace():
    selected = os.environ.get('TRAINING_PRODUCT_RUN_DIR')
    if not selected:
        raise ValueError('The host must select TRAINING_PRODUCT_RUN_DIR; use labs.py --lab devteam --requirements JSON')
    sys.path.insert(0, str(ROOT.parent / 'agent-training' / 'demo'))
    from product_team.spec import load_spec
    root = Path(selected).resolve()
    load_spec(root / 'product.json')
    return root
