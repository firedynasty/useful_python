import streamlit as st
import os
import glob
import re
from openai import OpenAI

st.set_page_config(page_title="ChatGPT-like Clone with File Loading")

# Initialize session states
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "folder_files" not in st.session_state:
    st.session_state.folder_files = []
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

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
