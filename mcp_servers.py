"The MCP servers this project uses."

import asyncio
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient


SECOND_BRAIN = r"C:\Users\jorge\Documents\code\ai-eng-labs\lab06_mcp_server.py"


client = MultiServerMCPClient(
    {
        "fetch": {
            "command": sys.executable,  # Use the current Python interpreter
            "args": [
                "-m",
                "mcp_server_fetch",
            ],  # Run the installed fetch server as a script
            "transport": "stdio",  # Use stdio for communication
        },
        "second-brain": {
            "command": sys.executable,
            "args": [SECOND_BRAIN], # no -m here. The second-brain server is a local script, not an installed package
            "transport": "stdio",
        }
    }
)


async def fetch_page(url: str) -> str:
    """Download a web page through the Fetch MCP server, as markdown."""
    async with client.session(
        "fetch"
    ) as session:  # Open a session with the fetch server
        result = await session.call_tool(
            "fetch", {"url": url, "max_length": 20000}
        )  # Call the fetch tool with the URL and a max length
    text = result.content[0].text  # MCP returns a list of content blocks.
    if (
        result.isError
    ):  # MCP reports tool failures in the result, not as Python exceptions
        raise RuntimeError(text)
    return text


if __name__ == "__main__":
    page = asyncio.run(
        fetch_page("https://job-boards.greenhouse.io/anthropic/jobs/5076109008")
    )
    print(f"{len(page)} characters\n")
    print(page[:1500])
