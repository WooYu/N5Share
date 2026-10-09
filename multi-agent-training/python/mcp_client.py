import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    parameters = StdioServerParameters(command=sys.executable,
                                       args=[str(Path(__file__).with_name("mcp_server.py"))])
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [item.name for item in tools.tools])
            result = await session.call_tool("search_local", arguments={"query": "Supervisor"})
            if result.isError:
                raise RuntimeError("MCP tool returned an error")
            print("TOOL RESULT:", result.model_dump_json())
            resource = await session.read_resource("training://patterns")
            print("RESOURCE:", resource.model_dump_json())
            prompt = await session.get_prompt("compare_patterns", arguments={"topic": "training"})
            print("PROMPT:", prompt.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
