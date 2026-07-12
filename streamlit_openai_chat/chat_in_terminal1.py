import os
import glob
import re
import datetime
import numpy as np
import sounddevice as sd
import wavio
import io
import math
from openai import OpenAI
from pydub import AudioSegment
from google.cloud import speech
from google.oauth2 import service_account

# Configuration for the recording
SAMPLE_RATE = 44100
CHANNELS = 1  # Mono recording
DTYPE = np.int16
SECONDS_PER_CHUNK = 10

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

# Audio recording and transcription functions
def select_device():
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]
    device_names = [device['name'] for device in input_devices]
    
    print("Available input devices:")
    for i, name in enumerate(device_names):
        print(f"{i}: {name}")
    
    try:
        choice = int(input("Select device number (or press Enter for default): ") or "0")
        if 0 <= choice < len(device_names):
            selected_device = device_names[choice]
            print(f"Selected: {selected_device}")
            return selected_device
    except ValueError:
        print("Invalid selection, using default.")
    
    # If no selection made or invalid, use first available device
    if input_devices:
        print(f"Using default device: {device_names[0]}")
        return device_names[0]
    
    # If no input devices found
    print("No input devices found. Please check your audio setup.")
    exit(1)

def get_filename_with_date_and_time():
    current_time = datetime.datetime.now()
    formatted_date_time = current_time.strftime('%m-%d-%Y_%H-%M-%S')
    # Ensure output directory exists
    os.makedirs("./output", exist_ok=True)
    filename = f"./output/recording_{formatted_date_time}.wav"
    return filename

def record_until_closed(device_name):
    import signal
    import sys
    
    # Flag to track if we're already handling an exit
    exiting = False
    all_data = []
    
    def signal_handler(sig, frame):
        nonlocal exiting
        if exiting:
            print("\nForce exiting...")
            sys.exit(0)
        exiting = True
        
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, device=device_name) as stream:
            print("Recording... Press Ctrl+C to stop and save.")
            
            while not exiting:
                try:
                    audio_chunk, _ = stream.read(int(SAMPLE_RATE))  # Read smaller chunks (1 second)
                    all_data.append(audio_chunk)
                    # Print a dot every 5 seconds to show recording is active
                    if len(all_data) % 5 == 0:
                        print(".", end="", flush=True)
                except KeyboardInterrupt:
                    break
                
            print("\nRecording stopped. Saving...")
            
            # Concatenate all chunks to form the complete audio data
            if all_data:
                audio_data = np.concatenate(all_data, axis=0)
                
                # Get filename with date and time
                filename = get_filename_with_date_and_time()
                
                # Save to a WAV file
                wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
                print(f"Saved as '{filename}'")
                return filename
            else:
                print("No data recorded.")
                return None
    except Exception as e:
        print(f"Error during recording: {e}")
        return None

def transcribe_audio(audio_file_path):
    """Transcribe English audio file using Google Speech-to-Text API."""
    print("Preparing to transcribe English audio...")
    
    # Default sample rate (will be overridden if MP3 is converted)
    sample_rate = 44100
    
    # Check if file is MP3 and convert if needed
    if audio_file_path.endswith('.mp3'):
        print("Converting MP3 to WAV format...")
        audio = AudioSegment.from_mp3(audio_file_path)
        wav_file_path = audio_file_path.replace('.mp3', '.wav')
        audio.export(wav_file_path, format="wav", parameters=["-ar", str(audio.frame_rate), "-ac", "1", "-sample_fmt", "s16"])
        audio_file_path = wav_file_path
        sample_rate = audio.frame_rate
        print(f"Detected sample rate: {sample_rate} Hz")
    # Add support for .wave extension
    elif audio_file_path.endswith('.wave'):
        # Read .wave file directly using pydub to get sample rate
        audio = AudioSegment.from_file(audio_file_path, format="wav")
        sample_rate = audio.frame_rate
        print(f"Detected sample rate from .wave file: {sample_rate} Hz")
    
    # Check audio duration
    audio = AudioSegment.from_file(audio_file_path)
    duration_ms = len(audio)
    
    # Read the audio file
    with io.open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with language-specific credentials
    try:
        print("Authenticating with Google Cloud...")
        # Use the direct file path to credentials
        credentials = service_account.Credentials.from_service_account_file("./service_account_key.json")
        client = speech.SpeechClient(credentials=credentials)
        print("Using credentials from: ./service_account_key.json")
    except Exception as e:
        print(f"Authentication error: {e}")
        print("Please make sure the service account key file exists at: ./service_account_key.json")
        return None
    
    # Configure audio
    audio = speech.RecognitionAudio(content=content)
    
    # Configure request with English language code
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="en-US",  # English (US)
        enable_automatic_punctuation=True,
    )
    
    # Make request
    print("Transcribing English audio...")
    response = client.recognize(config=config, audio=audio)
    
    # Process response
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    
    return transcript

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

# Function to record, transcribe and chat
def record_and_chat():
    if not client:
        print("OpenAI API Key not set. Please set up the API key first.")
        return
    
    print("\n=== Record your question ===")
    device_name = select_device()
    recorded_file = record_until_closed(device_name)
    
    if not recorded_file:
        print("Recording failed or was empty.")
        return
    
    # Transcribe the audio
    transcript = transcribe_audio(recorded_file)
    
    if transcript:
        # Save transcript to file
        output_file = recorded_file.replace('.wav', '.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        print(f"Transcription complete. Output saved to {output_file}")
        print("\nTranscript:")
        print(transcript)
        
        # Use transcription as prompt for OpenAI
        print("\nSending to OpenAI...")
        chat_with_openai(transcript)
    else:
        print("Transcription failed. Please check your credentials and try again.")

def main():
    global messages
    
    print("="*50)
    print("TERMINAL CHAT WITH OPENAI")
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
        print("4. Record and transcribe a message")
        print("5. Save conversation")
        print("6. Change OpenAI model")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
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
            prompt = input("\nYour message: ")
            if prompt:
                chat_with_openai(prompt)
        
        elif choice == "4":
            # Record and transcribe
            record_and_chat()
        
        elif choice == "5":
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
        
        elif choice == "6":
            # Change model
            select_openai_model()
        
        elif choice == "7":
            # Exit
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()