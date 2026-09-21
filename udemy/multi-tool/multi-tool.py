import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool
import json


load_dotenv()

project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_name = os.getenv("MODEL_NAME")
mcp_server_name = os.getenv("MCP_SERVER_NAME")


project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)

openai_client = project_client.get_openai_client()

# Initialize agent OpenAi tool using the read in OpenAPI spec
with open("./weather_openapi.json","r") as f:
    openapi_weather = json.load(f)
    
# Initialize agent OpenAPi tool using the read in OpenApi Spec
weather_tool = {
    "type":"openapi",
    "openapi":{
        "name":"weather",
        "spec":openapi_weather,
        "auth":{
            "type":"anonymous"
        }
    }
}

#Getting the Connection ID for the MCP Server

connection_id = None

for connection in project_client.connections.list():
    print(f"Found connection: {connection.name}")
    if mcp_server_name and connection.name == mcp_server_name:
        connection_id = connection.id
        break

print(f"The MCP server connection Id is: {connection_id}")

# Creating the MCP Tool Spec
mcp_tool = MCPTool(
    server_label="microsoft_learn_mcp_server",
    server_url="https://learn.microsoft.com/api/mcp",
    require_approval="never",
    project_connection_id=connection_id
)  

#Creating the Agent with Multiple Tools
agent = project_client.agents.create_version(
    agent_name="multi-tool-agent",
    definition=PromptAgentDefinition(
        model=model_name,
        instructions="You are a helpful assistant that can use multiple tools to answer user queries.",
        tools=[weather_tool, mcp_tool]
    )
) 

print(f"Created agent: {agent.name} with ID: {agent.id}")

#Creating a Conversation Object for the Agent Chat System
conversation = openai_client.conversations.create()

user_query = input("How can I help you? :")

response = openai_client.responses.create(
    conversation=conversation.id,
    input = user_query,
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}}
)

print(f"Agent response: {response.output_text}")