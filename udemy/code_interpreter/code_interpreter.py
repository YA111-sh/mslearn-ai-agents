import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, CodeInterpreterTool,AutoCodeInterpreterToolParam

load_dotenv()

project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_name = os.getenv("MODEL_NAME")



project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)

# ---------------------------------------------------------------------------------------------
# WHY openai_client VS project_client?
# - openai_client (OpenAI-compatible client):
#   Used for Files API (`openai_client.files.create`). OpenAI's Files endpoint standardizes
#   uploading, storing, and referencing file streams for Assistants/Code Interpreter tools.
# - project_client (Azure AI Project client):
#   Used for Agent lifecycle management (`project_client.agents.create_version`). It handles
#   Azure AI Foundry project resources, Azure IAM/Entra ID authentication, agent versioning,
#   and enterprise governance.
# ---------------------------------------------------------------------------------------------

openai_client = project_client.get_openai_client()



# Upload the CSV file for the code interpreter to use
# "rb" stands for "read binary" mode - it opens and reads the file as raw bytes,
# which is required when uploading files via the API to prevent encoding/newline issues.
file = openai_client.files.create(purpose="assistants",file=open("./electronics_products.csv","rb"))
print(f"File uploaded(id:{file.id})")

# Create Agent using project_client to register and version the agent in Azure AI Foundry
agent = project_client.agents.create_version(
    agent_name="code-interpreter-agent",
    definition=PromptAgentDefinition(
        model=model_name,
        instructions="You are a helpful AI Assistant with code interpreter capabilities.",
        tools=[
            CodeInterpreterTool(
                container = AutoCodeInterpreterToolParam(
                    file_ids=[file.id]
                )
            )
        ]
    )
)


# printing the agent id
print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")


# create a conversation to use with the agent
conversation = openai_client.conversations.create()
print(f"Created conversation with id: {conversation.id}")

response = openai_client.responses.create(
    conversation=conversation.id,
    input="Could you please create a column chart with products on the x-axis and their respective prices on the y-axis?",
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
)

print(f"Response completed with id: {response.id}")
print("Response:{response}")
file_id = ""
filename=""
container_id=""

#Extracting file from information from the response annotation
# Get the last message which should contain file citations
last_message = response.output[-1] # ResponseOutputMessage
if last_message.type == "message":
    # Get the last content item (contains the file annotations)
    text_content = last_message.content[-1] # ResponseOutputText
    if text_content.type == "output_text":
        # Get the last annotation (most recent file)
        if text_content.annotations:
            file_citation = text_content.annotations[-1]# AnnotationContainerFileCitation
            if file_citation.type == "container_file_citation":
                file_id = file_citation.file_id
                filename = file_citation.filename
                container_id = file_citation.container_id
                print(f"Found generated file: {filename} (ID: {file_id})")


# Download the generated file if available
if file_id and filename:
    file_content = openai_client.containers.files.content.retrieve(file_id=file_id, container_id=container_id)
    with open(filename ,"wb") as f:
        f.write(file_content.read())
        print(f"File {filename} downloaded successfully.")
        
else:
        print("No file generated in response")                    
        






