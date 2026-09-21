import asyncio
import os

from dotenv import load_dotenv
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

load_dotenv()

FOUNDRY_PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
FOUNDRY_MODEL = os.getenv("MODEL_NAME")


async def main() -> None:
    # AzureCliCredential + FoundryChatClient replace the old
    # AIProjectClient(...).get_openai_client() + conversations.create() dance.
    # FoundryChatClient talks to the Foundry project's Responses endpoint directly.
    async with (
        AzureCliCredential() as credential,
        Agent(
            client=FoundryChatClient(
                project_endpoint=FOUNDRY_PROJECT_ENDPOINT,
                model=FOUNDRY_MODEL,
                credential=credential,
            ),
            name="BatmanAgent",
            instructions="You are Batman, the dark knight of Gotham City.",
        ) as agent,
    ):
        print("Agent: ", end="", flush=True)
        async for update in agent.run("Who is the Joker?", stream=True):
            if update.text:
                print(update.text, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(main())