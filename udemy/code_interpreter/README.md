# Code Interpreter with Azure AI Foundry & OpenAI Client

## 📌 Overview
This script demonstrates how to create and use an AI agent equipped with **Code Interpreter** capabilities in Azure AI Foundry to analyze a dataset (`electronics_products.csv`) and generate a downloadable chart.

---

## 🚀 Key Steps in the Workflow
1. **Initialize Clients**:
   - `AIProjectClient`: Connects to Azure AI Foundry using `DefaultAzureCredential`.
   - `openai_client`: Obtained from `project_client.get_openai_client()` for OpenAI-compatible APIs.
2. **Upload Dataset**:
   - Uploads `electronics_products.csv` using `openai_client.files.create(..., purpose="assistants")` in binary mode (`"rb"`).
3. **Create Agent Version**:
   - Registers a `code-interpreter-agent` version via `project_client.agents.create_version` with `CodeInterpreterTool` attached to the uploaded file ID.
4. **Run Conversation & Prompt**:
   - Starts a conversation and requests the agent to generate a column chart (products vs prices).
5. **Parse Annotations & Download File**:
   - Inspects `response.output` to find `container_file_citation` annotations.
   - Downloads the generated image file using `openai_client.containers.files.content.retrieve(...)` and saves it locally in `"wb"` mode.

---

## 🧠 Key Learnings & Short Notes

* **`"rb"` vs `"wb"` Mode**:
  * `"rb"` (Read Binary): Reads raw bytes for file upload without text encoding issues.
  * `"wb"` (Write Binary): Writes raw bytes to disk when saving downloaded images/artifacts.

* **`project_client` vs `openai_client`**:
  * **`project_client`**: Used for Azure AI Foundry lifecycle operations (creating/versioning agents, security, enterprise management).
  * **`openai_client`**: Used for standard OpenAI Assistant/Files/Conversations operations (uploading files, executing responses, retrieving container file streams).

* **Annotations (`response.output[...].annotations`)**:
  * The model does not return raw binary images in chat text.
  * Instead, it returns a **`container_file_citation`** annotation containing `container_id`, `file_id`, and `filename`, which can be retrieved programmatically.
