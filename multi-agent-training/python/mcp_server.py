import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("training-local-corpus")
CORPUS = json.loads((Path(__file__).resolve().parents[1] / "data" / "corpus.json").read_text(encoding="utf-8"))


@mcp.tool()
def search_local(query: str) -> str:
    """Search the LOCAL training corpus; no internet access."""
    matches = [item for item in CORPUS if query.lower() in
               (item["title"] + item["text"]).lower()]
    return json.dumps({"source": "local corpus", "items": matches}, ensure_ascii=False)


@mcp.resource("training://patterns")
def patterns() -> str:
    return json.dumps(CORPUS, ensure_ascii=False)


@mcp.prompt()
def compare_patterns(topic: str) -> str:
    return f"Compare Supervisor, Swarm and Sequential Chain for {topic}. Cite the local corpus."


if __name__ == "__main__":
    mcp.run(transport="stdio")
