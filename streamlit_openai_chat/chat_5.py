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
if "uploaded_files_content" not in st.session_state:
    st.session_state.uploaded_files_content = {}  # {filename: content}
if "file_modifications" not in st.session_state:
    st.session_state.file_modifications = {}  # Track which files have been modified

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
        # Check for user messages (case-insensitive)
        if line.lower().startswith("user:"):
            # Save previous message if exists
            if current_role and current_content:
                messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
                current_content = []
            # Start new user message
            current_role = "user"
            # Find the position of the colon and extract content after it
            colon_pos = line.index(':')
            content_after_prefix = line[colon_pos + 1:].strip()
            if content_after_prefix:
                current_content.append(content_after_prefix)
        # Check for assistant messages (case-insensitive)
        elif line.lower().startswith("assistant:"):
            # Save previous message if exists
            if current_role and current_content:
                messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
                current_content = []
            # Start new assistant message
            current_role = "assistant"
            # Find the position of the colon and extract content after it
            colon_pos = line.index(':')
            content_after_prefix = line[colon_pos + 1:].strip()
            if content_after_prefix:
                current_content.append(content_after_prefix)
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

# Function to build messages with file context
def build_messages_with_files(user_prompt):
    """Build message list including file contents as context."""
    messages = []

    # Add file context as system message if files are loaded
    if st.session_state.uploaded_files_content:
        file_context = """You have access to the following text files.

IMPORTANT INSTRUCTIONS:
1. Each file may contain questions at the END marked with "***" (three asterisks)
2. When the user asks to "answer the questions" or mentions "***":
   - Look at the END of each file
   - Find ALL lines that start with "***"
   - Answer each question thoroughly

3. TWO WAYS TO RESPOND:

   A) If user says "write", "update", "add to file", or "save answers":
      Format with full file content:

      --- FILE: filename.txt ---
      [Full original content]

      *** Question here?
      ANSWER: [Your answer]

   B) If user just asks to "answer" or "list":
      Just provide the answers directly without file markers:

      **filename.txt:**
      *** Question here?
      ANSWER: [Your answer]

      **another.txt:**
      *** Another question?
      ANSWER: [Your answer]

4. If questions ask for "latest data", provide the most current information you have

Here are the files:

"""
        for filename, content in st.session_state.uploaded_files_content.items():
            file_context += f"--- FILE: {filename} ---\n{content}\n\n"

        messages.append({"role": "system", "content": file_context})

    # Add conversation history
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})

    return messages

# Function to parse response and update files if needed
def parse_response_for_file_updates(response_text):
    """Parse AI response to extract file updates."""
    import re

    # Pattern to match file updates: --- FILE: filename.txt ---
    file_pattern = r'---\s*FILE:\s*([^\n]+?)\s*---\s*\n(.*?)(?=---\s*FILE:|$)'
    matches = re.findall(file_pattern, response_text, re.DOTALL)

    updated_files = []
    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()

        if filename in st.session_state.uploaded_files_content:
            st.session_state.uploaded_files_content[filename] = content
            st.session_state.file_modifications[filename] = True
            updated_files.append(filename)

    return updated_files

# Main application
st.title("💬 ChatGPT with File Processing")

# Show helpful prompt hint if files are loaded
if st.session_state.uploaded_files_content:
    st.info("💡 **Quick prompt:** Please answer each question in each file that is formatted with *** before the question, it's at the end of each file")

# Show instructions if files are loaded
if st.session_state.uploaded_files_content:
    with st.expander("💡 How to work with loaded files", expanded=False):
        st.markdown("""
        ### Working with Your Files

        Your uploaded files are automatically included in the AI's context. You can:

        **Ask questions about the files:**
        - "Summarize each file"
        - "What are the main topics in file1.txt?"
        - "Compare the content across all files"

        **Answer *** questions (view only):**
        - "Please answer the questions that start with ***"
        - "Answer all *** questions"
        - AI will show just the answers without updating files

        **Answer *** questions and UPDATE files:**
        - "Write answers to the *** questions in each file"
        - "Update files with answers to *** questions"
        - "Save answers to the *** questions in the files"
        - AI will include full file content with `--- FILE: ---` markers to trigger file updates

        **Other file modifications:**
        - "Write a summary at the top of each file"
        - "Add a conclusion section to each file"

        💡 **Tip:** If you just want to see answers, use "answer". If you want to update the files, use "write" or "update".
        """)

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

    st.header("📁 Text Files")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload text files to work with:",
        type=['txt'],
        accept_multiple_files=True,
        help="Upload multiple text files to include in your chat context"
    )

    # Process uploaded files
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.uploaded_files_content:
                content = uploaded_file.read().decode('utf-8')
                st.session_state.uploaded_files_content[uploaded_file.name] = content
                st.session_state.file_modifications[uploaded_file.name] = False

    # Display loaded files
    if st.session_state.uploaded_files_content:
        st.subheader("Loaded Files:")
        for filename in list(st.session_state.uploaded_files_content.keys()):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                modified_indicator = " ✏️" if st.session_state.file_modifications.get(filename, False) else ""
                st.text(f"{filename}{modified_indicator}")
            with col2:
                # Download button
                if st.download_button(
                    label="⬇️",
                    data=st.session_state.uploaded_files_content[filename],
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_{filename}"
                ):
                    pass
            with col3:
                # Remove button
                if st.button("🗑️", key=f"remove_{filename}"):
                    del st.session_state.uploaded_files_content[filename]
                    if filename in st.session_state.file_modifications:
                        del st.session_state.file_modifications[filename]
                    st.rerun()

        # Clear all files button
        if st.button("🗑️ Clear All Files"):
            st.session_state.uploaded_files_content = {}
            st.session_state.file_modifications = {}
            st.rerun()

        # Show file context info
        total_chars = sum(len(content) for content in st.session_state.uploaded_files_content.values())
        st.caption(f"📊 {len(st.session_state.uploaded_files_content)} files loaded ({total_chars:,} characters)")

    st.divider()
    
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

    # Initialize show_copy state
    if "show_copy_text" not in st.session_state:
        st.session_state.show_copy_text = False

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📋 Show Conversation Text"):
            st.session_state.show_copy_text = True
    with col2:
        if st.button("❌ Hide"):
            st.session_state.show_copy_text = False

    if st.session_state.show_copy_text:
        if st.session_state.messages:
            # Format the conversation for copying
            conversation_text = ""
            for msg in st.session_state.messages:
                prefix = "User: " if msg["role"] == "user" else "Assistant: "
                conversation_text += f"{prefix}{msg['content']}\n\n"

            # Display in a text area for easy copying
            st.text_area(
                "Select all text and copy (Ctrl+A, Ctrl+C / Cmd+A, Cmd+C):",
                conversation_text,
                height=300,
                key="copy_chat_text"
            )
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
                    # Build messages with file context
                    messages_with_context = build_messages_with_files(prompt)

                    # Debug: Show context being sent (optional)
                    if st.session_state.uploaded_files_content:
                        with st.expander("🔍 Debug: Files included in context", expanded=False):
                            st.write(f"Total messages sent: {len(messages_with_context)}")
                            st.write(f"Files loaded: {len(st.session_state.uploaded_files_content)}")
                            if messages_with_context and messages_with_context[0]["role"] == "system":
                                st.text_area("System message preview:", messages_with_context[0]["content"][:500] + "...", height=150)

                    # Use standard Chat Completions API
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=messages_with_context,
                        stream=True,
                    )

                    response = st.write_stream(stream)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # Check if response contains file updates
                    updated_files = parse_response_for_file_updates(response)
                    if updated_files:
                        st.success(f"✏️ Updated {len(updated_files)} file(s): {', '.join(updated_files)}")
                        st.rerun()

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
