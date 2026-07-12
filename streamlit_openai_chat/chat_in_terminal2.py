import os
import glob
import re
import datetime
import numpy as np
import io
from openai import OpenAI
from google.oauth2 import service_account

# Available OpenAI models
AVAILABLE_MODELS = {
    "GPT-3.5 Turbo": "gpt-3.5-turbo",
    "GPT-4o": "gpt-4o",
    "GPT-4o Mini": "gpt-4o-mini",
    "GPT-4 Turbo": "gpt-4-turbo",
    "o1 (Reasoning focused)": "o1"
}

# Current conversation
messages = []
openai_model = "gpt-3.5-turbo"
client = None

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
        print(f"Error reading file: {e}")
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
def load_conversation(file_path):
    global messages
    if file_path:
        text = extract_text(file_path)
        messages = parse_conversation(text)
        print(f"Loaded conversation from {os.path.basename(file_path)}")
        display_conversation()
    else:
        print("No file selected.")

# Function to save conversation to file
def save_conversation(file_path):
    """Save current conversation to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for msg in messages:
            prefix = "User: " if msg["role"] == "user" else "Assistant: "
            f.write(f"{prefix}{msg['content']}\n\n")
    print(f"Conversation saved to {file_path}")

# Function to display conversation
def display_conversation():
    """Display the current conversation."""
    if not messages:
        print("No messages in conversation.")
        return
    
    print("\n" + "="*50)
    print("CONVERSATION")
    print("="*50)
    for msg in messages:
        prefix = "User: " if msg["role"] == "user" else "Assistant: "
        print(f"\n{prefix}{msg['content']}")
    print("\n" + "="*50)

# Function to set up OpenAI API
def setup_openai_api():
    global client
    api_key = input("Enter your OpenAI API Key: ")
    if api_key:
        client = OpenAI(api_key=api_key)
        print("API Key set successfully.")
        return True
    else:
        print("No API Key provided.")
        return False

# Function to select model
def select_openai_model():
    global openai_model
    
    print("\nAvailable Models:")
    for i, (name, model_id) in enumerate(AVAILABLE_MODELS.items()):
        print(f"{i+1}: {name}")
    
    try:
        choice = int(input("\nSelect model number (default is GPT-3.5 Turbo): ") or "1")
        if 1 <= choice <= len(AVAILABLE_MODELS):
            model_name = list(AVAILABLE_MODELS.keys())[choice-1]
            openai_model = AVAILABLE_MODELS[model_name]
            print(f"Selected: {model_name} ({openai_model})")
            
            # Display model info
            if model_name == "o1 (Reasoning focused)":
                print("Note: o1 is specialized for reasoning and complex tasks. It's more expensive to use.")
            elif model_name == "GPT-4o":
                print("Note: GPT-4o is OpenAI's flagship multimodal model with strong performance across text, vision, and audio tasks.")
            elif model_name == "GPT-4o Mini":
                print("Note: GPT-4o Mini is a smaller, faster version of GPT-4o with a lower cost.")
        else:
            print("Invalid selection, using GPT-3.5 Turbo.")
    except ValueError:
        print("Invalid input, using GPT-3.5 Turbo.")

# Function to chat with OpenAI
def chat_with_openai(prompt):
    global messages
    
    if not client:
        print("OpenAI API Key not set. Please set up the API key first.")
        return False
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        # Create the completion with the selected model
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": m["role"], "content": m["content"]} 
                for m in messages
            ],
        )
        
        assistant_response = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_response})
        
        print(f"\nAssistant: {assistant_response}")
        return True
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"\nAssistant: Sorry, I encountered an error: {error_msg}")
        messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {error_msg}"})
        return False

def main():
    global messages
    
    print("="*50)
    print("TERMINAL CHAT WITH OPENAI (TEXT INPUT)")
    print("="*50)
    
    # Ensure conversation directory exists
    os.makedirs("conversations", exist_ok=True)
    
    # Setup OpenAI API
    if not setup_openai_api():
        print("You need to set up an OpenAI API key to use this application.")
        return
    
    # Select model
    select_openai_model()
    
    while True:
        print("\n" + "="*50)
        print("MENU")
        print("="*50)
        print("1. Load conversation")
        print("2. Display current conversation")
        print("3. Type a message")
        print("4. Save conversation")
        print("5. Change OpenAI model")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == "1":
            # Load conversation
            folder_path = "conversations"
            found_files = scan_folder(folder_path)
            
            if found_files:
                print("\nAvailable conversation files:")
                for i, file_path in enumerate(found_files):
                    print(f"{i+1}: {os.path.basename(file_path)}")
                
                try:
                    file_choice = int(input("\nSelect file number: "))
                    if 1 <= file_choice <= len(found_files):
                        selected_file = found_files[file_choice-1]
                        load_conversation(selected_file)
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Invalid input.")
            else:
                print(f"No .txt files found in {folder_path}.")
        
        elif choice == "2":
            # Display conversation
            display_conversation()
        
        elif choice == "3":
            # Type a message
            print("\nEnter your message (type 'END' on a new line to submit):")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            
            prompt = "\n".join(lines)
            
            if prompt.strip():
                chat_with_openai(prompt)
            else:
                print("Empty message not sent.")
        
        elif choice == "4":
            # Save conversation
            if not messages:
                print("No conversation to save.")
                continue
                
            folder_path = "conversations"
            filename = input("Save conversation as (without .txt extension): ")
            
            if not filename:
                print("No filename provided.")
                continue
                
            # Add .txt extension if not present
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            save_path = os.path.join(folder_path, filename)
            save_conversation(save_path)
        
        elif choice == "5":
            # Change model
            select_openai_model()
        
        elif choice == "6":
            # Exit
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()