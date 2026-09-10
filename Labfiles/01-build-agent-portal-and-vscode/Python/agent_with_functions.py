from dotenv import load_dotenv  # Reads key/value settings from a local .env file.
import os  # Provides access to environment variables such as PROJECT_ENDPOINT.
from pathlib import Path  # Gives us a convenient, cross-platform way to work with paths.
from azure.ai.projects import AIProjectClient  # pyright: ignore[reportMissingImports]
from azure.identity import DefaultAzureCredential # pyright: ignore[reportMissingImports]


# All files created by the agent will be written below this folder.
OUTPUT_DIR = Path("agent_outputs")

def get_output_path(filename):
    """Create a unique local path for a generated file.

    Args:
        filename: The desired filename, such as ``report.csv``.

    Returns:
        A Path object inside the ``agent_outputs`` folder. If the requested
        filename already exists, a number is added to make the path unique.
    """
    # mkdir(exist_ok=True) creates the directory only when it is missing.
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Path(filename).name removes any folders from a filename supplied by the agent.
    file_name = Path(filename).name
    # stem is the filename without its extension; suffix is the extension itself.
    stem = Path(file_name).stem or "output"
    suffix = Path(file_name).suffix
    output_path = OUTPUT_DIR / file_name

    counter = 1
    # Keep changing the name until we find a path that is not already in use.
    while output_path.exists():
        output_path = OUTPUT_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    return output_path


def save_bytes(file_bytes, filename):
    """Save binary data, such as an image or downloaded file, locally.

    Args:
        file_bytes: The file content represented as bytes.
        filename: The name to use for the saved file.

    Returns:
        The Path object pointing to the newly saved file.
    """
    output_path = get_output_path(filename)
    # "wb" means write-binary, which is needed for images and other file bytes.
    with open(output_path, "wb") as file_handle:
        file_handle.write(file_bytes)
    return output_path


"""Decode Base64 image data and save the image as a local file.
    Base64 is a text representation of binary data. The data must be decoded
    back into bytes before it can be written to an image file.
    Args:
        image_data: Base64-encoded image data.
        filename: The name to use for the saved image.
    Returns:
        The Path object pointing to the newly saved image.
    """
def save_image(image_data, filename):
    # Base64 is text used to represent bytes; decode it before saving the image.
    return save_bytes(base64.b64decode(image_data), filename)


"""Download an agent-generated file from its remote container.
    The dictionary in ``downloaded_files`` acts as a cache. This prevents the
    same remote file from being downloaded more than once during a response.
    Args:
        openai_client: The client used to access files in the remote container.
        annotation: Citation metadata containing the container and file IDs.
        downloaded_files: A dictionary used to remember downloaded file paths.
    Returns:
        The local Path object where the file was saved.
    """
def download_container_file(openai_client, annotation, downloaded_files):
    
    # The pair identifies the file inside its remote container.
    cache_key = (annotation.container_id, annotation.file_id)
    # Reuse a previously downloaded file instead of downloading it again.
    if cache_key in downloaded_files:
        return downloaded_files[cache_key]

    file_content = openai_client.containers.files.content.retrieve(
        file_id=annotation.file_id,
        container_id=annotation.container_id,
    )
    output_path = save_bytes(
        file_content.read(),
        annotation.filename or f"{annotation.file_id}.bin",
    )
    # Store the local path so later citations of the same file can reuse it.
    downloaded_files[cache_key] = output_path
    return output_path


"""Format agent text and replace remote file citations with local paths.
    When an agent creates a file, its response may contain a citation pointing
    to that file in a remote sandbox. This function downloads the file and
    changes the citation text so the user can see where the local copy is.
    Args:
        content_item: One text portion of the agent response.
        openai_client: The client used to download cited files.
        downloaded_files: A cache of files already downloaded for this response.
    Returns:
        A tuple containing the formatted text and a set of referenced local paths.
    """
def format_output_text(content_item, openai_client, downloaded_files):
    
    # Start with the text written by the agent. Some response objects may have no text.
    text = content_item.text or ""
    # Citations can refer to files that the agent created in its remote container.
    replacements = []
    # A set automatically ignores duplicate paths.
    referenced_files = set()

    # An annotation is metadata attached to part of the agent's output text.
    for annotation in content_item.annotations or []:
        # Ignore annotations that are not citations to files in a container.
        if getattr(annotation, "type", "") != "container_file_citation":
            continue

        output_path = download_container_file(openai_client, annotation, downloaded_files)
        replacement_text = f"{annotation.filename} (saved to {output_path})"
        referenced_files.add(output_path)

        start_index = getattr(annotation, "start_index", None)
        end_index = getattr(annotation, "end_index", None)
        if start_index is not None and end_index is not None:
            # Save index-based replacements for later, after all citations are found.
            replacements.append((start_index, end_index, replacement_text))
            continue

        # Older or different response shapes may provide the annotated text instead.
        annotated_text = getattr(annotation, "text", "")
        if annotated_text:
            text = text.replace(annotated_text, replacement_text)

    # Replace from right to left so earlier character indexes stay valid.
    for start_index, end_index, replacement_text in sorted(replacements, reverse=True):
        text = f"{text[:start_index]}{replacement_text}{text[end_index:]}"

    return text, referenced_files



"""Connect to the configured agent and run an interactive chat session.
    The function loads configuration, connects to Microsoft Foundry, accepts
    messages from the user, sends them to the agent, and displays text or files
    returned by the agent. The loop ends when the user types ``exit``, ``quit``,
    or ``bye``.
    """
def main():
   
    # Load environment variables from .env before reading PROJECT_ENDPOINT.
    load_dotenv()
    
    project_endpoint = os.environ.get("PROJECT_ENDPOINT")
    # The second argument is a default used when AGENT_NAME is not set.
    agent_name = os.environ.get("AGENT_NAME", "it-support-agent")
    
    
    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable not set. Please set it in your .env file or environment")
        return
        
    print("Connecting to Microsoft Foundry Project...")
    
    # DefaultAzureCredential tries the Azure login methods available on this machine.
    credential = DefaultAzureCredential()
    
    project_client = AIProjectClient(
        credential = credential,
        endpoint = project_endpoint
    )
    
    # This client is used for conversations, responses, and generated files.
    openai_client = project_client.get_openai_client()
    
     # Get the agent created in the portal
    print(f"Loading agent: {agent_name}")
    agent = project_client.agents.get(agent_name=agent_name)
    print(f"Connected to agent: {agent.name} (id: {agent.id})")
    
    
    # A conversation stores the ongoing history between the user and the agent.
    conversation = openai_client.conversations.create(items=[])
    print(f"Conversation created (id: {conversation.id})")
    
    # Chat loop
    print("\n" + "="*60)
    print("IT Support Agent Ready!")
    print("Ask questions, request data analysis, or get help.")
    print("Type 'exit' to quit.")
    print("="*60 + "\n")
    
    while True:
        # input() pauses the program until the user types a message and presses Enter.
        user_input = input("You: ").strip()
        
        # lower() makes EXIT, Exit, and exit behave the same way.
        if user_input.lower() in ['exit','quit','bye']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        
        # Add the user's message to the conversation history.
        openai_client.conversations.items.create(
            conversation_id = conversation.id,
            items = [{"type": "message", "role": "user", "content": user_input}]
        )
        
        # Get response from agent
        print("\n[Agent is thinking...]")
        
        response = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            input=""
        )
        
        # Display response and save any generated files locally
        # These variables track which kinds of output have already been displayed.
        handled_output = False
        downloaded_files = {}
        referenced_files = set()
        image_count = 0
        
        if hasattr(response,"output") and response.output:
            # A response can contain several items: text, images, or generated files.
            for item in response.output:
                item_type = getattr(item,"type","")
                
                if item_type == "message" and getattr(item, "content", None):
                    # A message can contain multiple content parts, so inspect each one.
                    for content_item in item.content:
                        if getattr(content_item , "type","") != "output_text":
                            continue
                        
                        formatted_text, message_files = format_output_text(
                            content_item,
                            openai_client,
                            downloaded_files,
                        )
                        referenced_files.update(message_files)
                        
                        if formatted_text:
                            print(f"\nAgent: {formatted_text}\n")
                            handled_output = True
                
                # Some SDK response shapes expose text directly on the item.
                elif hasattr(item,"text") and item.text:
                    print(f"\nAgent: {item.text}\n")
                    handled_output = True
                
                elif item_type == "image":
                    image_count += 1
                    filename = f"chart_{image_count}.png"
                    
                    if hasattr(item, "image") and hasattr(item.image, "data"):
                        file_path = save_image(item.image.data, filename)
                        print(f"\n[Agent generated a chart - saved to: {file_path}]")
                    else:
                        print("\n[Agent generated an image]")
                    handled_output = True
            
            # Report downloaded files that were generated but not mentioned in text.
            for file_path in downloaded_files.values():
                if file_path not in referenced_files:
                    print(f"\n[Agent generated a file - saved to: {file_path}]")
                    handled_output = True
        
        # Fallback for SDK versions that provide one combined output_text property.
        if not handled_output and hasattr(response, "output_text") and response.output_text:
            print(f"\nAgent: {response.output_text}\n")
            

if __name__ == "__main__":
    main()            
                        
                                

    
    
    
    
    

        
    
    
    