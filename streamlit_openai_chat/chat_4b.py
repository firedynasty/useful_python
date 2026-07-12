import streamlit as st
import os
import glob
import re
from openai import OpenAI

st.set_page_config(page_title="ChatGPT-like Clone with File Loading")

# Initialize session states
# Define available models

if "available_models" not in st.session_state:
    st.session_state["available_models"] = {
        "GPT-3.5 Turbo": "gpt-3.5-turbo",
        "GPT-4o": "gpt-4o",
        "GPT-4o Mini": "gpt-4o-mini",
        "GPT-4 Turbo": "gpt-4-turbo",
        "GPT-5": "gpt-5",
        "GPT-5 Mini": "gpt-5-mini",
        "GPT-5 Nano": "gpt-5-nano",
        "GPT-5 Codex": "gpt-5-codex",
        "o1 (Reasoning focused)": "o1",
        "o1 Preview": "o1-preview",
        "o1 Mini": "o1-mini"
    }

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "folder_files" not in st.session_state:
    st.session_state.folder_files = []
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
if "web_search_enabled" not in st.session_state:
    st.session_state.web_search_enabled = False

# Function to sort filenames naturally
def natural_sort_key(s):
    """Sort strings with embedded numbers naturally."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

# Function to scan for text files in a directory
def scan_folder(folder_path):
    """Scan folder for .txt files and return sorted list."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    found_files = glob.glob(os.path.join(folder_path, "*.txt"))
    found_files.sort(key=natural_sort_key)
    return found_files

# Function to extract text from file
def extract_text(file_path):
    """Extract text from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

# Function to parse a conversation file into messages
def parse_conversation(text):
    """Parse a text file into user and assistant messages."""
    messages = []
    lines = text.split('\n')
    current_role = None
    current_content = []
    
    for line in lines:
        if line.startswith("User: "):
            # Save previous message if exists
            if current_role and current_content:
                messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
                current_content = []
            # Start new user message
            current_role = "user"
            current_content.append(line[6:])  # Remove "User: " prefix
        elif line.startswith("Assistant: "):
            # Save previous message if exists
            if current_role and current_content:
                messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
                current_content = []
            # Start new assistant message
            current_role = "assistant"
            current_content.append(line[11:])  # Remove "Assistant: " prefix
        else:
            # Continue current message
            if current_role:
                current_content.append(line)
    
    # Add the last message
    if current_role and current_content:
        messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
    
    return messages

# Function to load conversation from file
def load_conversation():
    if st.session_state.selected_file:
        text = extract_text(st.session_state.selected_file)
        st.session_state.messages = parse_conversation(text)

# Function to save conversation to file
def save_conversation(file_path):
    """Save current conversation to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for msg in st.session_state.messages:
            prefix = "User: " if msg["role"] == "user" else "Assistant: "
            f.write(f"{prefix}{msg['content']}\n\n")

# Main application
st.title("ChatGPT-like Clone with File Loading")

# Sidebar for API key and folder input
with st.sidebar:
    st.header("Configuration")
    
    # API key input
    api_key = st.text_input("OpenAI API Key:", type="password")
    
    # Model selection
    model_display_name = st.selectbox(
        "Select Model:",
        options=list(st.session_state["available_models"].keys()),
        index=0
    )
    
    # Update the model in session state when selection changes
    st.session_state["openai_model"] = st.session_state["available_models"][model_display_name]
    
    # Display model info
    if model_display_name == "o1 (Reasoning focused)":
        st.info("o1 is specialized for reasoning and complex tasks. It's more expensive to use.")
    elif model_display_name == "GPT-4o":
        st.info("GPT-4o is OpenAI's flagship multimodal model with strong performance across text, vision, and audio tasks.")
    elif model_display_name == "GPT-4o Mini":
        st.info("GPT-4o Mini is a smaller, faster version of GPT-4o with a lower cost.")

    # Web search toggle (available for most models via Responses API)
    st.session_state.web_search_enabled = st.checkbox(
        "🔍 Enable Web Search",
        value=st.session_state.web_search_enabled,
        help="Enable real-time web search for up-to-date information (uses Responses API)"
    )
    
    # Initialize OpenAI client when API key is provided
    client = None
    if api_key:
        client = OpenAI(api_key=api_key)
    
    st.header("Conversation Files")
    
    # Input for conversation folder path
    folder_input = st.text_input(
        "Conversation Folder Path:", 
        value="conversations", 
        help="Path to folder containing conversation .txt files"
    )
    
    # Process folder button to refresh file list
    if st.button("Process Folder"):
        if folder_input:
            st.session_state.folder_files = scan_folder(folder_input)
            if not st.session_state.folder_files:
                st.info(f"No .txt files found in {folder_input}. Create some conversation files.")
        else:
            st.warning("Please enter a folder path first")
    
    # Scan folder for files
    if folder_input:
        st.session_state.folder_files = scan_folder(folder_input)
        
        if st.session_state.folder_files:
            file_options = ["Select a file..."] + [os.path.basename(f) for f in st.session_state.folder_files]
            selected_file_name = st.selectbox("Select a conversation file:", file_options)
            
            if selected_file_name != "Select a file...":
                file_idx = file_options.index(selected_file_name) - 1  # Adjust for the "Select a file..." option
                st.session_state.selected_file = st.session_state.folder_files[file_idx]
                
                # Button to load conversation
                if st.button("Load Conversation"):
                    load_conversation()
                    st.success(f"Loaded conversation from {selected_file_name}")
        else:
            st.info(f"No .txt files found in {folder_input}. Create some conversation files.")
    
    # File name input for saving current conversation
    save_filename = st.text_input("Save conversation as:", 
                                 help="Filename to save current conversation (will be saved to the folder specified above)")
    
    if save_filename and folder_input:
        # Add .txt extension if not present
        if not save_filename.endswith('.txt'):
            save_filename += '.txt'

        save_path = os.path.join(folder_input, save_filename)

        if st.button("Save Current Conversation"):
            save_conversation(save_path)
            st.success(f"Conversation saved to {save_filename}")
            # Update file list
            st.session_state.folder_files = scan_folder(folder_input)

    # Copy conversation section
    st.header("Copy Conversation")
    if st.button("Copy Entire Chat"):
        if st.session_state.messages:
            # Format the conversation for copying
            conversation_text = ""
            for msg in st.session_state.messages:
                prefix = "User: " if msg["role"] == "user" else "Assistant: "
                conversation_text += f"{prefix}{msg['content']}\n\n"

            # Display in a text area for easy copying
            st.text_area(
                "Copy the text below:",
                conversation_text,
                height=300,
                key="copy_chat_text"
            )
            st.info("👆 Select all text above and copy (Ctrl+A, Ctrl+C / Cmd+A, Cmd+C)")
        else:
            st.warning("No conversation to copy yet.")

# Add information about model pricing
st.sidebar.markdown("""
### Model Pricing Information
- **GPT-3.5 Turbo**: Lowest cost option
- **GPT-4o Mini**: Moderate cost
- **GPT-4o**: Higher cost
- **GPT-4 Turbo**: Higher cost
- **o1**: Highest cost (3x GPT-4o)
""")

# Display conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Check if client is initialized (API key is provided)
    if client:
        with st.chat_message("assistant"):
            try:
                # Display a message when using the expensive o1 model
                if st.session_state["openai_model"] == "o1":
                    st.warning("Note: You are using the o1 model which has significantly higher costs than other models.")

                # Check if web search is enabled
                if st.session_state.web_search_enabled:
                    # Use the Responses API with web_search tool
                    response_obj = client.responses.create(
                        model=st.session_state["openai_model"],
                        tools=[{"type": "web_search"}],
                        tool_choice="auto",
                        input=prompt
                    )

                    # Extract the response text
                    response = response_obj.output_text

                    # Display citations if available
                    if hasattr(response_obj, 'output') and response_obj.output:
                        for output_item in response_obj.output:
                            if output_item.type == "message" and hasattr(output_item, 'content'):
                                for content_item in output_item.content:
                                    if hasattr(content_item, 'annotations') and content_item.annotations:
                                        with st.expander("🔍 Web Search Citations", expanded=False):
                                            for annotation in content_item.annotations:
                                                if annotation.type == "url_citation":
                                                    st.markdown(f"- [{annotation.title}]({annotation.url})")

                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    # Use standard Chat Completions API
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )

                    response = st.write_stream(stream)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                # Show model used for this response
                st.caption(f"Response generated using: {model_display_name}")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                # Add a placeholder response in case of error
                st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {error_msg}"})
    else:
        with st.chat_message("assistant"):
            error_msg = "Please enter your OpenAI API key in the sidebar to enable chat functionality."
            st.warning(error_msg)
            # Don't add this message to the conversation history
