# Model Context Protocol (MCP) Agent with Azure AI Foundry

## 📌 Overview
This project demonstrates how to build and invoke an AI Agent integrated with an **MCP (Model Context Protocol)** tool in Azure AI Foundry using `azure-ai-projects` and the OpenAI client.

The agent uses the **Microsoft Learn MCP Server** (`https://learn.microsoft.com/api/mcp`) to retrieve up-to-date documentation and code samples for Microsoft technologies.

---

## 🚀 Key Steps in the Workflow

1. **Authentication & Client Setup**:
   - `AIProjectClient`: Connects to Azure AI Foundry using `DefaultAzureCredential`.
   - `openai_client`: Obtained via `project_client.get_openai_client()` to run conversations and responses.

2. **Discover / Bind Project Connections**:
   - Queries `project_client.connections.list()` to optionally locate any registered MCP connection ID configured in Azure AI Foundry.

3. **Define MCP Tool (`MCPTool`)**:
   - Configures the MCP endpoint:
     - `server_label`: Identifier for the tool (`microsoft_learn_mcp_server`).
     - `server_url`: Endpoint of the MCP server (`https://learn.microsoft.com/api/mcp`).
     - `require_approval`: `"never"` to allow automated tool execution without manual approval.
     - `project_connection_id`: ID from Foundry connections (optional for public endpoints).

4. **Create / Version the Agent**:
   - Creates `MCP-Agent` via `project_client.agents.create_version()` with the MCP tool attached to its definition.

5. **Run Interactive Conversation**:
   - Creates a conversation session via `openai_client.conversations.create()`.
   - Takes user input from the console (`input(...)`) and sends the request referencing the agent.
   - The agent calls the MCP server behind the scenes to fetch information and returns the answer.

---

## 🧠 Key Learnings & Notes

* **What is MCP (Model Context Protocol)?**:
  * An open protocol allowing AI models to securely discover and invoke tools, data sources, and services across different platforms.

* **Public vs Authenticated MCP Servers**:
  * **Public MCP Servers** (like Microsoft Learn API) work directly via `server_url`.
  * **Private / Enterprise MCP Servers** (hosted on Container Apps, APIM, etc.) require registering a connection in Foundry Hub and passing `project_connection_id`.

* **Role of `project_client.connections`**:
  * Manages connections inside Azure AI Foundry (Vector DBs/Azure AI Search, Azure OpenAI endpoints, external MCP tools, and Azure databases).
