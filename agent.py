import asyncio
from langchain.agents import create_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from db import list_saved_jobs
from mcp_servers import client


from report import build_report, top_skills
from track import save_post

SYSTEM = (
    "You help the user compare job posts with what they have learned. "
    "Use fetch to read a job post from a URL. "
    "Use list_saved_jobs for questions about the jobs the user has saved. "
    "Use search_vault to check the user's notes for a skill; one search per skill. "
    "A skill mentioned in a plan or goal is NOT evidence that the user knows it."
    "Use top_skills for any question about how many posts ask for a skill; never count them yourself. ")


# Not extract.py's llm: here reasoning stays on, because thinking helps the model choose tools.
# num_ctx: the conversation and all tool results must fit, or Ollama silently drops the oldest text
llm = ChatOllama(model="qwen3.5:9b",num_ctx=16384)

async def build_agent(fetch,brain):
    """The agent: tools from both MCP and the local database, plus a memory saver."""
    # load_mcp_tools asks a running server for its tools: fetch gives fetch,
    # brain gives search_vault, read_note and list_notes. list_saved_jobs is a plain Python function.
    tools = await load_mcp_tools(fetch) + await load_mcp_tools(brain) + [list_saved_jobs, top_skills]
    # create_agent builds the loop: model -> tools -> model ... until the model answers without a tool call
    return create_agent(model=llm, tools=tools, system_prompt=SYSTEM, checkpointer=InMemorySaver())

async def ask(agent, text: str):
    """Send one message to the agent, printing each tool call as it happens."""
    # Only the new message: the checkpointer adds the earlier turns of this thread
    inputs = {"messages": [{"role": "user", "content": text }]}
    # thread_id: which conversation to load and save. recursion_limit: max steps before it stops
    config = {"configurable": {"thread_id": "terminal"}, "recursion_limit":25}
    # One update each time a node finishes, e.g. {"model": {"messages": [AIMessage(...)]}}
    async for update in agent.astream(inputs,config,stream_mode="updates"):
        for state in update.values():  # skip the node name, keep {"messages": [...]}
            for msg in (state or {}).get("messages",[]):  # state can be empty for some steps
                for call in getattr(msg,"tool_calls",[]):  # ToolMessages have no tool_calls, so []
                    print(f"   ACTION: {call["name"]}({call["args"]})")
    return msg.content # the last message is the agent's answer

async def handle(text: str, agent, brain) -> str:
    """A command runs code directly (workflow); anything else goes to the agent."""
    words = text.split()
    # Only the first word decides the route, and each return ends the function, so one path runs
    if words[0].lower() == "save":
        # words[1:] = every word after "save", each treated as a URL. No URLs -> "" -> the usage message
        return "\n".join([await save_post(url) for url in words[1:]]) or "Usage: save <url> [<url> ...]"
    if words[0].lower() == "report":
        return await build_report(brain)  # reuses the second-brain session opened in main
    return await ask(agent, text)  # not a command: the LLM decides which tools to use


async def main():
    # Both servers start here and stay running for the whole chat, because the agent's tools use these sessions
    async with client.session("fetch") as fetch, client.session("second-brain") as brain:
        agent = await build_agent(fetch, brain)
        print ("Ask the agent a question about your saved jobs or a new job post. Ctrl-C or type 'quit' to exit. ")

        while True:
            # input() blocks, so it runs on a side thread to keep the async machinery free
            text = (await asyncio.to_thread(input, "\nYOU: ")).strip()
            if text.lower() in ("quit", "exit"):
                break
            if text:  # ignore empty lines
                try:
                    print(f"\nAGENT: {await handle(text, agent, brain)}")
                except Exception as error:  # a dead URL shouldn't end the whole chat
                    print(f"\nERROR: {error}")


if __name__ == "__main__":
    asyncio.run(main())

