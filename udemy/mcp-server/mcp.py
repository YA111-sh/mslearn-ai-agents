import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool, Tool

load_dotenv()

project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_name = os.getenv("MODEL_NAME")
mcp_server_name = os.getenv("MCP_SERVER_NAME")


project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)

openai_client = project_client.get_openai_client()


# ---------------------------------------------------------------------------------------------
# What type of connections does project_client.connections manage?
#
# `project_client.connections` manages connected external and Azure resources linked to 
# your Azure AI Foundry project hub/workspace, such as:
# 1. Custom / Remote MCP Server Connections (e.g., custom web API endpoints, serverless tools)
# 2. Azure AI Search / Vector DB connections (for RAG and grounding)
# 3. Azure OpenAI Service / Model Endpoint connections
# 4. Remote Web APIs & API Management (APIM) connections
# 5. Azure Storage & Database connections (Cosmos DB, Blob Storage)
# ---------------------------------------------------------------------------------------------

# Finding the MCP server connection ID (if registered in Foundry Connections)
connection_id = None

for connection in project_client.connections.list():
    print(f"Found connection: {connection.name}")
    if mcp_server_name and connection.name == mcp_server_name:
        connection_id = connection.id
        break

print(f"The MCP server connection Id is: {connection_id}")


# Creating the MCP tool spec
tool = MCPTool(
    server_label="microsoft_learn_mcp_server",
    server_url="https://learn.microsoft.com/api/mcp",
    require_approval="never",
    project_connection_id=connection_id
)

#Creating the MCP agent
agent = project_client.agents.create_version(
    agent_name="MCP-Agent",
    definition=PromptAgentDefinition(
        model=model_name,
        instructions="You are an intelligent assistant that can interact with the Microsoft Learn MCP server to provide users with relevant learning resources and information about Microsoft technologies.",
        tools=[tool]
    )
)



#create a conversation to use with the agent
conversation = openai_client.conversations.create()
print(f"Created conversation with id: {conversation.id}")

user_query = input("Please enter your question: ")

response = openai_client.responses.create(
    conversation=conversation.id,
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    input=user_query
)

print(f"Agent Response: {response.output_text}")




