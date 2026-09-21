import asyncio
import os

from dotenv import load_dotenv
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

load_dotenv()
FOUNDRY_PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
FOUNDRY_MODEL = os.getenv("MODEL_NAME")

ms_learn_mcp_tool = MCPStreamableHTTPTool(
    name="Microsoft Learn MCP Tool",
    url="https://learn.microsoft.com/api/mcp",
    approval_mode="never_require",
    description="Search Microsoft Learn documentation.",
)


async def main() -> None:
    # Everything opened here is automatically closed when this block ends,
    # in reverse order (ms_learn_mcp_tool closes first, then credential),
    # even if an error happens inside the block.
    async with (
        AzureCliCredential() as credential,
        ms_learn_mcp_tool,
    ):
        client = FoundryChatClient(
            project_endpoint=FOUNDRY_PROJECT_ENDPOINT,
            model=FOUNDRY_MODEL,
            credential=credential,
        )
        
        
        code_interpreter_tool = client.get_code_interpreter_tool()

        agent = Agent(
            client=client,
            name="multi-tool-agent",
            instructions="You are a helpful multi-tool agent",
            tools=[code_interpreter_tool, ms_learn_mcp_tool],
        )

        user_query = input("How may I help you? ")

        print("Agent: ", end="", flush=True)
        async for update in agent.run(user_query, stream=True):
            if update.text:
                print(update.text, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(main())