import os
import glob
import re
import argparse
import datetime
from openai import OpenAI

# For loading environment variables
try:
    from dotenv import load_dotenv
    DOTENV_SUPPORT = True
except ImportError:
    print("Warning: python-dotenv not installed. .env support will be disabled.")
    print("To enable .env support, install python-dotenv: pip install python-dotenv")
    DOTENV_SUPPORT = False

# For PDF processing
try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer
    PDF_SUPPORT = True
except ImportError:
    print("Warning: pdfminer.six not installed. PDF support will be disabled.")
    print("To enable PDF support, install pdfminer.six: pip install pdfminer.six")
    PDF_SUPPORT = False

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

def natural_sort_key(s):
    """Sort strings with embedded numbers naturally."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def scan_folder(folder_path, file_types=None):
    """
    Scan folder for files with specified extensions.
    
    Args:
        folder_path (str): Path to the folder to scan
        file_types (list): List of file extensions to include (default: ['.txt', '.md', '.pdf'])
    
    Returns:
        list: Sorted list of found files
    """
    if file_types is None:
        file_types = ['.txt', '.md', '.pdf']
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return []
    
    # Filter for specified file types
    found_files = []
    for ext in file_types:
        pattern = os.path.join(folder_path, f"*{ext}")
        found_files.extend(glob.glob(pattern))
    
    # Sort files naturally
    found_files.sort(key=natural_sort_key)
    return found_files

def extract_text_from_txt_or_md(file_path):
    """Extract text from a .txt or .md file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using pdfminer."""
    if not PDF_SUPPORT:
        return "PDF support is not available. Please install pdfminer.six."
    
    try:
        text = ""
        # Extract all pages and combine them
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text += element.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return f"Error extracting PDF: {str(e)}"

def extract_text(file_path):
    """Extract text based on file extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    else:  # .txt or .md
        return extract_text_from_txt_or_md(file_path)

def format_notes_for_prompt(notes_text, filename, max_length=8000, custom_instruction=None):
    """Format extracted notes into a prompt for OpenAI."""
    # Use a higher token limit to avoid truncation
    
    # Format the prompt with the filename and content
    formatted_prompt = f"""
The following are notes/content from file: {filename}

---
{notes_text}
---

{custom_instruction or "Please continue or respond to this content as appropriate."}
"""
    return formatted_prompt

def create_env_file(api_key):
    """Create a .env file with the API key."""
    if not DOTENV_SUPPORT:
        print("Cannot create .env file. python-dotenv module not installed.")
        return False
        
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    try:
        with open(env_file, 'w') as f:
            f.write(f'OPENAI_API_KEY="{api_key}"\n')
        print(f".env file created successfully at {env_file}")
        return True
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False

def setup_openai_api():
    """Set up the OpenAI API client."""
    global client
    api_key = None
    
    # First check for API key in environment variables or .env file
    if DOTENV_SUPPORT:
        # Load from .env file if it exists
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_file):
            print(f"Found .env file at {env_file}")
            load_dotenv(env_file)
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                print("API Key loaded from .env file.")
            else:
                print("No OPENAI_API_KEY found in .env file.")
                print("Please add OPENAI_API_KEY=\"your_key_here\" to your .env file.")
    
    # If no API key found in environment, prompt the user
    if not api_key:
        api_key = input("Enter your OpenAI API Key: ")
        
        # Ask if the user wants to save the API key to a .env file
        if api_key and DOTENV_SUPPORT:
            save_to_env = input("Would you like to save your API key to a .env file for future use? (y/n): ")
            if save_to_env.lower() in ['y', 'yes']:
                create_env_file(api_key)
    
    if api_key:
        client = OpenAI(api_key=api_key)
        print("API Key set successfully.")
        return True
    else:
        print("No API Key provided.")
        return False

def select_openai_model():
    """Let the user select an OpenAI model."""
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
        else:
            print("Invalid selection, using GPT-3.5 Turbo.")
    except ValueError:
        print("Invalid input, using GPT-3.5 Turbo.")

def chat_with_openai(prompt):
    """Send a message to OpenAI and get a response."""
    global messages
    
    if not client:
        print("OpenAI API Key not set. Please set up the API key first.")
        return False
    
    print(f"\nSending notes to {openai_model}...")
    messages.append({"role": "user", "content": prompt})
    
    try:
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
        print(f"\nError communicating with OpenAI: {error_msg}")
        messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {error_msg}"})
        return False

def save_conversation(file_path):
    """Save current conversation to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for msg in messages:
            prefix = "User: " if msg["role"] == "user" else "Assistant: "
            f.write(f"{prefix}{msg['content']}\n\n")
    print(f"Conversation saved to {file_path}")

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
        print(f"\n{prefix}{msg['content']}")  # Show full content
    print("\n" + "="*50)

def load_notes_and_chat():
    """Main function to load notes from files and start a chat."""
    folder_path = input("Enter folder path containing your notes/conversations: ")
    
    # Get available files
    allowed_types = ['.txt', '.md']
    if PDF_SUPPORT:
        allowed_types.append('.pdf')
    
    found_files = scan_folder(folder_path, allowed_types)
    
    if not found_files:
        print(f"No suitable files found in {folder_path}")
        return
    
    # Display available files
    print(f"\nFound {len(found_files)} files:")
    for i, file_path in enumerate(found_files):
        filename = os.path.basename(file_path)
        print(f"{i+1}: {filename}")
    
    # Let user select a file
    try:
        file_choice = int(input("\nSelect file number (or 0 to cancel): "))
        if file_choice == 0:
            return
        if 1 <= file_choice <= len(found_files):
            selected_file = found_files[file_choice-1]
        else:
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return
    
    # Extract text from selected file
    filename = os.path.basename(selected_file)
    print(f"Processing: {filename}")
    
    file_content = extract_text(selected_file)
    if not file_content:
        print("Failed to extract content or file is empty.")
        return
    
    # Show content to the user
    print("\n" + "="*50)
    print(f"CONTENT FROM: {filename}")
    print("="*50)
    
    # Display the full content without truncation
    print(file_content)
    print("="*50)
    
    # Ask for custom instruction
    print("\nHow would you like to continue with this content?")
    print("1. Continue the conversation/notes where it left off")
    print("2. Summarize this content")
    print("3. Ask questions about this content")
    print("4. Custom instruction")
    print("5. Return to file selection")
    
    prompt_choice = input("\nEnter choice (1-5): ")
    
    # Option to return to file selection
    if prompt_choice == "5":
        print("Returning to file selection...")
        return False
    
    custom_instruction = None
    if prompt_choice == "1":
        custom_instruction = "Please continue this conversation or these notes where they left off. Help me develop these ideas further."
    elif prompt_choice == "2":
        custom_instruction = "Please provide a comprehensive summary of this content."
    elif prompt_choice == "3":
        custom_instruction = "Based on this content, what questions should I be asking? Please identify key points that need clarification or exploration."
    elif prompt_choice == "4":
        custom_instruction = input("\nEnter your custom instruction for the AI: ")
    else:
        custom_instruction = "Please continue or respond to this content as appropriate."
    
    # Create prompt from notes
    prompt = format_notes_for_prompt(file_content, filename, custom_instruction=custom_instruction)
    
    # Ask for confirmation before sending to OpenAI
    print(f"\nReady to send content to {openai_model}.")
    confirm = input("Send now? (y/n): ")
    
    if confirm.lower() not in ['y', 'yes']:
        print("Operation cancelled.")
        return
    
    # Send to OpenAI
    success = chat_with_openai(prompt)
    
    if success:
        # Continue conversation if desired
        continue_chat()

def continue_chat():
    """Continue the conversation with follow-up messages."""
    while True:
        print("\nOptions:")
        print("1. Send follow-up message")
        print("2. Save conversation")
        print("3. Return to main menu")
        
        choice = input("\nEnter choice (1-3): ")
        
        if choice == "1":
            # Get follow-up message
            print("\nEnter your follow-up message (type 'END' on a new line to submit):")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            
            follow_up = "\n".join(lines)
            
            if follow_up.strip():
                chat_with_openai(follow_up)
            else:
                print("Empty message not sent.")
                
        elif choice == "2":
            # Save conversation
            folder_path = "conversations"
            os.makedirs(folder_path, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"conversation_{timestamp}.txt"
            
            filename = input(f"Save conversation as (default: {default_filename}): ") or default_filename
            
            # Add .txt extension if not present
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            save_path = os.path.join(folder_path, filename)
            save_conversation(save_path)
            
        elif choice == "3":
            return
        
        else:
            print("Invalid choice. Please try again.")

def select_file_from_current_directory():
    """Select a file from the current directory to process."""
    # List files in current directory
    current_dir = os.path.abspath(os.getcwd())
    files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]
    
    if not files:
        print("No files found in the current directory.")
        return None
    
    # Sort files alphabetically by name
    files.sort()
    
    # Create a numbered list of files
    print("\nFiles in current directory:")
    print("="*50)
    for i, file_name in enumerate(files, 1):
        # Get file size
        file_path = os.path.join(current_dir, file_name)
        file_size = os.path.getsize(file_path)
        size_str = f"{file_size} bytes"
        if file_size > 1024:
            size_str = f"{file_size/1024:.1f} KB"
        if file_size > 1024*1024:
            size_str = f"{file_size/(1024*1024):.1f} MB"
            
        # Display file with size and extension
        _, ext = os.path.splitext(file_name)
        print(f"{i}. {file_name:<30} [{size_str:<10}] {ext}")
    print("="*50)
    
    # Get user input for which file to read
    try:
        choice = int(input("\nEnter the number of the file you want to process: "))
        if 1 <= choice <= len(files):
            selected_file = os.path.join(current_dir, files[choice-1])
            return selected_file
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Please enter a valid number.")
        return None

def process_file_directly(file_path):
    """Process a specific file directly from command line argument."""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    # Check file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    allowed_types = ['.txt', '.md']
    if PDF_SUPPORT:
        allowed_types.append('.pdf')
    
    if ext not in allowed_types:
        print(f"Error: Unsupported file type {ext}. Supported types are: {', '.join(allowed_types)}")
        return False
    
    # Extract text from file
    filename = os.path.basename(file_path)
    print(f"Processing: {filename}")
    
    file_content = extract_text(file_path)
    if not file_content:
        print("Failed to extract content or file is empty.")
        return False
    
    # Show content to the user
    print("\n" + "="*50)
    print(f"CONTENT FROM: {filename}")
    print("="*50)
    
    # Display the full content without truncation
    print(file_content)
    print("="*50)
    
    # Ask for custom instruction
    print("\nHow would you like to continue with this content?")
    print("1. Continue the conversation/notes where it left off")
    print("2. Summarize this content")
    print("3. Ask questions about this content")
    print("4. Custom instruction")
    print("5. Return to file selection")
    
    prompt_choice = input("\nEnter choice (1-5): ")
    
    # Option to return to file selection
    if prompt_choice == "5":
        print("Returning to file selection...")
        return False
    
    custom_instruction = None
    if prompt_choice == "1":
        custom_instruction = "Please continue this conversation or these notes where they left off. Help me develop these ideas further."
    elif prompt_choice == "2":
        custom_instruction = "Please provide a comprehensive summary of this content."
    elif prompt_choice == "3":
        custom_instruction = "Based on this content, what questions should I be asking? Please identify key points that need clarification or exploration."
    elif prompt_choice == "4":
        custom_instruction = input("\nEnter your custom instruction for the AI: ")
    else:
        custom_instruction = "Please continue or respond to this content as appropriate."
    
    # Create prompt from notes
    prompt = format_notes_for_prompt(file_content, filename, custom_instruction=custom_instruction)
    
    # Ask for confirmation before sending to OpenAI
    print(f"\nReady to send content to {openai_model}.")
    confirm = input("Send now? (y/n): ")
    
    if confirm.lower() not in ['y', 'yes']:
        print("Operation cancelled.")
        return False
    
    # Send to OpenAI
    success = chat_with_openai(prompt)
    
    if success:
        # Continue conversation if desired
        continue_chat()
    
    return True

def main():
    global messages
    
    # Set up argparse
    parser = argparse.ArgumentParser(description='Research Notes Chat Assistant')
    parser.add_argument('-i', '--input', help='Input file or folder path')
    parser.add_argument('-o', '--output', default='./conversations', help='Output folder for saved conversations')
    # Add positional argument for input file
    parser.add_argument('file', nargs='?', help='Input file to process (.txt, .md, or .pdf)')
    
    # Parse arguments
    args = parser.parse_args()
    
    print("="*50)
    print("RESEARCH NOTES CHAT ASSISTANT")
    print("="*50)
    print("This tool helps you continue conversations with your research notes.")
    
    if DOTENV_SUPPORT:
        print("\nℹ️  You can store your OpenAI API key in a .env file using the variable:")
        print("   OPENAI_API_KEY=\"your_key_here\"")
        print("   This way you won't need to enter it each time.")
    
    # Setup OpenAI API
    if not setup_openai_api():
        print("You need to set up an OpenAI API key to use this application.")
        return
    
    # Select model
    select_openai_model()
    
    # Process file directly if provided as positional or --input argument
    file_path = args.file or args.input
    if file_path and os.path.isfile(file_path):
        process_file_directly(file_path)
        return
    
    # If no file argument was provided, prompt to select a file from current directory
    print("\nNo file specified. Would you like to select a file from the current directory?")
    select_file = input("Select a file? (y/n): ")
    
    if select_file.lower() in ['y', 'yes']:
        while True:
            selected_file = select_file_from_current_directory()
            if not selected_file:
                break
            
            # Process the file and check if user wanted to return to file selection
            if process_file_directly(selected_file):
                # File was processed successfully and user didn't choose to return to file selection
                return
            # If we get here, the user chose to return to file selection
    
    # Otherwise, show interactive menu
    while True:
        print("\n" + "="*50)
        print("MAIN MENU")
        print("="*50)
        print("1. Load notes/conversation and start chat")
        print("2. Display current conversation")
        print("3. Change OpenAI model")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            # Load notes and start chat
            load_notes_and_chat()
        
        elif choice == "2":
            # Display conversation
            display_conversation()
        
        elif choice == "3":
            # Change model
            select_openai_model()
        
        elif choice == "4":
            # Exit
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
