import os
import subprocess
import datetime
import time
import io
import json
import sys
import pyperclip
from google.cloud import speech
from google.oauth2 import service_account

# Configuration
CHUNK_SECONDS = 20  # Record in 20-second chunks
OUTPUT_DIR = "./output"
FFMPEG_INPUT = ":1"  # This is the AVFoundation input device that works for you

def verify_credentials():
    """Verify that the service account credentials file exists and is valid."""
    # First, check the hardcoded path that worked previously
    hardcoded_path = "/Users/stanleytan/Documents/46-python/transcribe_audio/cantonese/service_account_key.json"
    env_var_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
    
    # If the environment variable isn't set, use the hardcoded path
    if not env_var_path:
        print("Using hardcoded credentials path")
        credential_path = hardcoded_path
    else:
        credential_path = env_var_path
        print(f"Using credentials from environment variable")
    
    # Check if file exists
    if not os.path.exists(credential_path):
        print(f"ERROR: Credentials file not found at {credential_path}")
        return False
        
    # Check if file is readable
    try:
        with open(credential_path, 'r') as f:
            creds_content = f.read()
            
        # Check if file contains valid JSON
        creds_json = json.loads(creds_content)
        
        # Set the environment variable for this session if using hardcoded path
        if not env_var_path and os.path.exists(hardcoded_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_CANTONESE"] = hardcoded_path
            print(f"Set GOOGLE_APPLICATION_CREDENTIALS_CANTONESE for this session")
            
        return True
            
    except Exception as e:
        print(f"ERROR: Issue with credentials file: {e}")
        return False

def get_filename_with_date_and_time():
    """Generate a filename with the current date and time."""
    current_time = datetime.datetime.now()
    formatted_date_time = current_time.strftime('%m-%d-%Y_%H-%M-%S')
    base_filename = f"recording_{formatted_date_time}"
    return base_filename

def record_chunk_with_ffmpeg(device=FFMPEG_INPUT, seconds=CHUNK_SECONDS):
    """Record a chunk of audio using FFmpeg."""
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate filename based on current date and time
    base_filename = get_filename_with_date_and_time()
    wav_path = f"{OUTPUT_DIR}/{base_filename}.wav"
    
    print(f"\nRecording {seconds} seconds of audio using FFmpeg...")
    print("Press Ctrl+C to cancel recording")
    
    # Build FFmpeg command
    # Using WAV format for better quality and compatibility with Google Speech API
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "avfoundation",
        "-i", device,
        "-t", str(seconds),
        "-ac", "1",            # Mono audio (1 channel)
        "-ar", "44100",        # 44.1 kHz sample rate
        "-y",                  # Overwrite output file if it exists
        wav_path
    ]
    
    try:
        # Start FFmpeg process
        process = subprocess.Popen(
            ffmpeg_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True           # Get text output instead of bytes
        )
        
        # Show progress during recording
        start_time = time.time()
        
        while process.poll() is None:  # While FFmpeg is still running
            elapsed = time.time() - start_time
            if elapsed > seconds:
                # We've exceeded the recording time, FFmpeg should finish soon
                break
                
            # Display progress bar
            progress = min(elapsed / seconds, 1.0)
            bar_length = 30
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + ' ' * (bar_length - filled_length)
            
            sys.stdout.write(f"\rRecording: [{bar}] {elapsed:.1f}s/{seconds}s")
            sys.stdout.flush()
            
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                # User pressed Ctrl+C, terminate the recording
                print("\nRecording cancelled by user")
                process.terminate()
                process.wait()
                
                # Check if the file was created but is incomplete
                if os.path.exists(wav_path):
                    print(f"Removing incomplete recording: {wav_path}")
                    os.remove(wav_path)
                return None
            
        # Wait for FFmpeg to finish
        stdout, stderr = process.communicate()
        
        print(f"\nRecording complete. Saved to {wav_path}")
        
        # Check for FFmpeg errors
        if process.returncode != 0:
            print(f"FFmpeg Error: {stderr}")
            return None
            
        return wav_path
        
    except Exception as e:
        print(f"Error during FFmpeg recording: {e}")
        return None

def transcribe_audio(audio_file_path):
    """Transcribe Cantonese audio file using Google Speech-to-Text API."""
    print(f"\nTranscribing {os.path.basename(audio_file_path)}...")
    
    # Read the audio file
    with io.open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with language-specific credentials
    try:
        # Get the credentials path - use either environment variable or hardcoded path
        credential_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE", 
                                        "/Users/stanleytan/Documents/46-python/transcribe_audio/cantonese/service_account_key.json")
        
        # Create Speech client
        credentials = service_account.Credentials.from_service_account_file(credential_path)
        client = speech.SpeechClient(credentials=credentials)
        
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    
    # Configure audio
    audio = speech.RecognitionAudio(content=content)
    
    # Configure request with Cantonese language code
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,  # Match FFmpeg sample rate
        language_code="yue-Hant-HK",  # Traditional Chinese (Cantonese)
        enable_automatic_punctuation=True,
        audio_channel_count=1,    # Mono
        enable_separate_recognition_per_channel=False,
        model="default",
        use_enhanced=True,        # Use enhanced model
    )
    
    # Make request
    try:
        print("Sending request to Google Speech-to-Text API...")
        response = client.recognize(config=config, audio=audio)
        
        # Process response
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
        
        if not transcript.strip():
            print("No speech detected in the audio")
            return None
            
        return transcript
        
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

def list_avfoundation_devices():
    """List all audio devices available through AVFoundation."""
    print("Listing all available AVFoundation audio devices...")
    
    try:
        # Run FFmpeg with special flags to list devices
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "avfoundation",
            "-list_devices", "true",
            "-i", ""  # Empty input
        ]
        
        # This will intentionally produce an error with device info
        process = subprocess.run(
            ffmpeg_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # The device list is in stderr
        device_info = process.stderr
        
        print("\n=== AVAILABLE DEVICES ===")
        print(device_info)
        
        # Help user find the right audio device
        print("\nNOTE: Look for the audio device you want to record from.")
        print("In your original command 'ffmpeg -f avfoundation -i \":1\" output.mp3'")
        print("you're using ':1' which means no video device (empty before colon) and audio device #1.")
        
    except Exception as e:
        print(f"Error listing devices: {e}")

def copy_to_clipboard(text):
    """Copy text to clipboard and print confirmation."""
    try:
        pyperclip.copy(text)
        print("\n✅ Transcription copied to clipboard!")
        os.system('echo "This is now in the clipboard!"')
    except Exception as e:
        print(f"\n❌ Failed to copy to clipboard: {e}")

def main():
    """Main function that continuously records and transcribes audio."""
    # Define ffmpeg_device as a local variable within the function
    ffmpeg_device = FFMPEG_INPUT  # Start with the default
    
    print("=== FFmpeg Cantonese Recorder & Transcriber ===")
    print(f"Recording {CHUNK_SECONDS}-second chunks from AVFoundation device {ffmpeg_device}")
    print("Press Ctrl+C at any time to exit the program")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Verify credentials for Google Speech API
    if not verify_credentials():
        creds_choice = input("Credentials verification failed. Continue anyway? (y/n): ")
        if creds_choice.lower() not in ['y', 'yes']:
            print("Exiting. Please fix credentials and try again.")
            return
    
    # List available devices
    list_avfoundation_devices()
    
    # Ask if user wants to change the input device
    device_choice = input(f"\nCurrent FFmpeg input is '{ffmpeg_device}'. Change it? (y/n): ")
    if device_choice.lower() in ['y', 'yes']:
        ffmpeg_device = input("Enter new FFmpeg input (e.g. ':1'): ")
        print(f"Input device changed to '{ffmpeg_device}'")
    
    # Start continuous recording and transcription
    try:
        print("\nStarting recording session")
        print("Press Ctrl+C at any time to exit the program\n")
        
        chunk_count = 0
        
        while True:
            chunk_count += 1
            print(f"\n=== Chunk #{chunk_count} ===")
            
            # Record audio using FFmpeg
            wav_file = record_chunk_with_ffmpeg(ffmpeg_device, CHUNK_SECONDS)
            
            if not wav_file:
                print("Recording was cancelled or failed.")
                choice = input("\nContinue with another recording? (y/n) [y]: ") or "y"
                if choice.lower() not in ['y', 'yes']:
                    print("Exiting program.")
                    break
                continue
            
            # Ask user if they want to transcribe this recording
            transcribe_choice = input(f"\nDo you want to transcribe this recording? (y/n): ")
            if transcribe_choice.lower() not in ['y', 'yes']:
                print("Skipping transcription for this recording.")
                
                # For skipped transcriptions, automatically continue to the next recording
                print("Continuing to next recording...")
                continue
            
            # Transcribe the audio
            transcript = transcribe_audio(wav_file)
            
            if transcript:
                print("\n" + "="*50)
                print(f"Transcription (Chunk #{chunk_count}):")
                print(transcript)
                print("="*50 + "\n")
                
                # Copy transcription to clipboard
                copy_to_clipboard(transcript)
                
                # Save transcript to text file
                txt_file = wav_file.replace('.wav', '.txt')
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                print(f"Saved transcript to {txt_file}")
            else:
                print("No transcription was produced for this recording.")
            
            # After transcription, wait for user to continue (don't auto-continue)
            continue_choice = input("\nContinue with another recording? (y/n) [y]: ") or "y"
            if continue_choice.lower() not in ['y', 'yes']:
                print("Exiting program.")
                break
            
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user (Ctrl+C)")
        print("Exiting...")

if __name__ == "__main__":
    main()