import sounddevice as sd
import numpy as np
import wavio
import datetime
import os
import io
import math
import google.auth
from google.cloud import speech
from pydub import AudioSegment
from google.oauth2 import service_account
import google_auth_oauthlib.flow
import googleapiclient.discovery
import json

def verify_credentials():
    """Verify that the service account credentials file exists and is valid."""
    # First, check the hardcoded path from the error message
    hardcoded_path = "/Users/stanleytan/Documents/46-python/transcribe_audio/cantonese/service_account_key.json"
    env_var_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
    
    # If the environment variable isn't set, suggest using the hardcoded path
    if not env_var_path:
        print("WARNING: GOOGLE_APPLICATION_CREDENTIALS_CANTONESE environment variable is not set.")
        print(f"Checking hardcoded path instead: {hardcoded_path}")
        credential_path = hardcoded_path
    else:
        credential_path = env_var_path
        print(f"Checking credentials file from environment variable: {credential_path}")
    
    # Check if file exists
    if not os.path.exists(credential_path):
        print(f"ERROR: Credentials file not found at {credential_path}")
        return False
        
    # Check if file is readable
    try:
        with open(credential_path, 'r') as f:
            creds_content = f.read()
    except Exception as e:
        print(f"ERROR: Cannot read credentials file: {e}")
        return False
        
    # Check if file contains valid JSON
    try:
        creds_json = json.loads(creds_content)
        
        # Check for required fields in service account key
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds_json:
                print(f"ERROR: Credentials file is missing required field: {field}")
                return False
                
        # Verify it's a service account key
        if creds_json.get('type') != 'service_account':
            print(f"ERROR: Credentials file is not a service account key (type={creds_json.get('type')})")
            return False
            
        print(f"Credentials file is valid for project: {creds_json.get('project_id')}")
        print(f"Service account: {creds_json.get('client_email')}")
        
        # Attempt to create a speech client to test if the credentials work
        try:
            print("Testing credentials by creating a Speech client...")
            credentials = service_account.Credentials.from_service_account_file(credential_path)
            client = speech.SpeechClient(credentials=credentials)
            print("Successfully created Speech client - credentials appear valid!")
            
            # If the environment variable isn't set but the hardcoded path works, 
            # suggest setting the environment variable
            if not env_var_path:
                print("\nIMPORTANT: Your credentials file works, but the environment variable is not set.")
                print("To fix this permanently, add this line to your ~/.zshrc file:")
                print(f"export GOOGLE_APPLICATION_CREDENTIALS_CANTONESE=\"{hardcoded_path}\"")
                print("Then run: source ~/.zshrc")
                
                # Set the environment variable for the current session
                os.environ["GOOGLE_APPLICATION_CREDENTIALS_CANTONESE"] = hardcoded_path
                print(f"Set GOOGLE_APPLICATION_CREDENTIALS_CANTONESE={hardcoded_path} for this session.")
            
            return True
            
        except Exception as auth_error:
            print(f"ERROR: Credentials file exists and is valid JSON, but failed to authenticate: {auth_error}")
            print("This could be caused by:")
            print("1. The service account does not have permission to use the Speech-to-Text API")
            print("2. The API is not enabled for the project")
            print("3. The project billing is not enabled")
            print("Please check your Google Cloud Console to resolve these issues.")
            return False
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Credentials file contains invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to validate credentials: {e}")
        return False

# Configuration for the recording
SAMPLE_RATE = 44100
CHANNELS = 1  # Mono recording
DTYPE = np.int16
SECONDS_PER_CHUNK = 10

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

def mp3_to_wav(mp3_file_path):
    """Convert MP3 file to WAV format for Google Speech-to-Text API."""
    audio = AudioSegment.from_mp3(mp3_file_path)
    wav_file_path = mp3_file_path.replace('.mp3', '.wav')
    audio.export(wav_file_path, format="wav", parameters=["-ar", str(audio.frame_rate), "-ac", "1", "-sample_fmt", "s16"])
    return wav_file_path, audio.frame_rate

def split_audio_file(audio_file_path, segment_length_ms=30000):
    """Split audio file into segments of specified length (default 30 seconds)."""
    print(f"Loading audio file: {audio_file_path}")
    audio = AudioSegment.from_file(audio_file_path)
    sample_rate = audio.frame_rate
    
    # Calculate number of segments
    duration_ms = len(audio)
    num_segments = math.ceil(duration_ms / segment_length_ms)
    print(f"Audio duration: {duration_ms/1000:.2f} seconds")
    print(f"Splitting into {num_segments} segments of {segment_length_ms/1000} seconds each")
    
    segments = []
    for i in range(num_segments):
        start_ms = i * segment_length_ms
        end_ms = min((i + 1) * segment_length_ms, duration_ms)
        segment = audio[start_ms:end_ms]
        segment_path = f"{os.path.splitext(audio_file_path)[0]}_segment_{i+1}.wav"
        segment.export(segment_path, format="wav", parameters=["-ar", str(sample_rate), "-ac", "1", "-sample_fmt", "s16"])
        segments.append((segment_path, sample_rate))
        print(f"Created segment {i+1}/{num_segments}: {segment_path}")
    
    return segments

def transcribe_audio_segment(segment_path, sample_rate):
    """Transcribe a single audio segment using Google Speech-to-Text API."""
    print(f"Transcribing segment: {segment_path}")
    
    # Read the audio file
    with io.open(segment_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with language-specific credentials
    print("Authenticating with Google Cloud for segment...")
    
    # Try to use language-specific credentials first
    cantonese_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
    hardcoded_path = "/Users/stanleytan/Documents/46-python/transcribe_audio/cantonese/service_account_key.json"
    
    # Initialize client variable
    client = None
    
    try:
        # Determine which credentials path to use
        if cantonese_credentials:
            credential_path = cantonese_credentials
            print(f"Using Cantonese-specific credentials from environment: {credential_path}")
        elif os.path.exists(hardcoded_path):
            credential_path = hardcoded_path
            print(f"Using hardcoded credentials path: {credential_path}")
            # Set environment variable for this session
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_CANTONESE"] = hardcoded_path
        else:
            print("WARNING: No credentials found in environment or hardcoded path")
            print("Falling back to default credentials...")
            try:
                credentials, project = google.auth.default()
                print(f"Successfully loaded default credentials for project: {project}")
                client = speech.SpeechClient(credentials=credentials)
                print("Successfully created Speech client with default credentials")
            except Exception as default_cred_error:
                print(f"ERROR: Failed to load default credentials: {default_cred_error}")
                return None
        
        # If we have a credential path but no client yet
        if not client and 'credential_path' in locals():
            # Check if the credential file exists
            if not os.path.exists(credential_path):
                print(f"ERROR: Credential file does not exist at path: {credential_path}")
                return None
                
            # Check if the credential file is readable
            try:
                with open(credential_path, 'r') as f:
                    # Just check if we can read it
                    credential_content = f.read(100)  # Read just a bit to verify it's readable
                    print("Credential file is readable")
            except Exception as file_error:
                print(f"ERROR: Could not read credential file: {file_error}")
                return None
                
            try:
                credentials = service_account.Credentials.from_service_account_file(credential_path)
                print("Successfully loaded credentials from file")
                client = speech.SpeechClient(credentials=credentials)
                print("Successfully created Speech client with credentials")
            except Exception as cred_error:
                print(f"ERROR: Failed to create credentials from file: {cred_error}")
                print("This may be because:")
                print("1. The credentials file is corrupted or has incorrect format")
                print("2. The service account does not have sufficient permissions")
                print("3. Speech-to-Text API is not enabled for this project")
                print("4. The project billing is not set up")
                return None
            
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    
    # If we still don't have a client, return None
    if not client:
        print("ERROR: Failed to create Speech client")
        return None
    
    # Configure audio
    audio = speech.RecognitionAudio(content=content)
    
    # Configure request with Chinese language code
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="yue-Hant-HK",  # Traditional Chinese (Cantonese)
        enable_automatic_punctuation=True,
    )
    
    # Make request
    try:
        print("Sending transcription request to Google Cloud...")
        response = client.recognize(config=config, audio=audio)
        print("Successfully received transcription response")
    except Exception as api_error:
        print(f"ERROR: API request failed: {api_error}")
        print("This could be due to:")
        print("1. Invalid credentials or insufficient permissions")
        print("2. Speech API not enabled for this project")
        print("3. Network connectivity issues")
        print("4. Quota limitations or billing issues")
        return None
    
    # Process response
    transcript = ""
    if not response.results:
        print("WARNING: No transcription results received from the API for this segment")
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    
    return transcript

def transcribe_audio(audio_file_path):
    """Transcribe Chinese audio file using Google Speech-to-Text API."""
    print("Preparing to transcribe Cantonese audio...")
    
    # Default sample rate (will be overridden if MP3 is converted)
    sample_rate = 44100
    
    # Check if file is MP3 and convert if needed
    if audio_file_path.endswith('.mp3'):
        print("Converting MP3 to WAV format...")
        audio_file_path, sample_rate = mp3_to_wav(audio_file_path)
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
    
    # If audio is longer than 30 seconds, use segmented approach
    if duration_ms > 30000:
        print(f"Audio file is {duration_ms/1000:.2f} seconds long. Using segmented transcription.")
        return transcribe_large_audio(audio_file_path)
    
    # For shorter files, use the original transcription method
    # Read the audio file
    with io.open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with language-specific credentials
    print("Authenticating with Google Cloud...")
    
    # Try to use language-specific credentials first
    cantonese_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
    hardcoded_path = "/Users/stanleytan/Documents/46-python/transcribe_audio/cantonese/service_account_key.json"
    
    # Initialize client variable
    client = None
    
    try:
        # Determine which credentials path to use
        if cantonese_credentials:
            credential_path = cantonese_credentials
            print(f"Using Cantonese-specific credentials from environment: {credential_path}")
        elif os.path.exists(hardcoded_path):
            credential_path = hardcoded_path
            print(f"Using hardcoded credentials path: {credential_path}")
            # Set environment variable for this session
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_CANTONESE"] = hardcoded_path
        else:
            print("WARNING: No credentials found in environment or hardcoded path")
            print("Falling back to default credentials...")
            try:
                credentials, project = google.auth.default()
                print(f"Successfully loaded default credentials for project: {project}")
                client = speech.SpeechClient(credentials=credentials)
                print("Successfully created Speech client with default credentials")
            except Exception as default_cred_error:
                print(f"ERROR: Failed to load default credentials: {default_cred_error}")
                return None
        
        # If we have a credential path but no client yet
        if not client and 'credential_path' in locals():
            # Check if the credential file exists
            if not os.path.exists(credential_path):
                print(f"ERROR: Credential file does not exist at path: {credential_path}")
                return None
                
            # Check if the credential file is readable
            try:
                with open(credential_path, 'r') as f:
                    # Just check if we can read it
                    credential_content = f.read(100)  # Read just a bit to verify it's readable
                    print("Credential file is readable")
            except Exception as file_error:
                print(f"ERROR: Could not read credential file: {file_error}")
                return None
                
            try:
                credentials = service_account.Credentials.from_service_account_file(credential_path)
                print("Successfully loaded credentials from file")
                client = speech.SpeechClient(credentials=credentials)
                print("Successfully created Speech client with credentials")
            except Exception as cred_error:
                print(f"ERROR: Failed to create credentials from file: {cred_error}")
                print("This may be because:")
                print("1. The credentials file is corrupted or has incorrect format")
                print("2. The service account does not have sufficient permissions")
                print("3. Speech-to-Text API is not enabled for this project")
                print("4. The project billing is not set up")
                return None
            
    except Exception as e:
        print(f"Authentication error: {e}")
        print("Trying alternative authentication method...")
        # If you need to use OAuth flow instead
        # Note: This is typically not used for Speech-to-Text API
        # You should obtain a service account key instead
        print("Please obtain a service account key from Google Cloud Console.")
        print("Visit: https://console.cloud.google.com/apis/credentials")
        print("Create a service account key and download it as JSON.")
        print("Then set it in your environment as GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
        return None
    
    # If we still don't have a client, return None
    if not client:
        print("ERROR: Failed to create Speech client")
        return None
    
    # Configure audio
    audio = speech.RecognitionAudio(content=content)
    
    # Configure request with Chinese language code (Cantonese)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="yue-Hant-HK",  # Traditional Chinese (Cantonese)
        enable_automatic_punctuation=True,
    )
    
    # Make request
    print("Transcribing Cantonese audio...")
    try:
        response = client.recognize(config=config, audio=audio)
        print("Successfully received transcription response")
    except Exception as api_error:
        print(f"ERROR: API request failed: {api_error}")
        print("This could be due to:")
        print("1. Invalid credentials or insufficient permissions")
        print("2. Speech API not enabled for this project")
        print("3. Network connectivity issues")
        print("4. Quota limitations or billing issues")
        print("Please check your Google Cloud Console for more details.")
        return None
    
    # Process response
    transcript = ""
    if not response.results:
        print("WARNING: No transcription results received from the API")
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    
    return transcript

def transcribe_large_audio(audio_file_path):
    """Transcribe a large audio file by splitting it into segments."""
    # Check file extension
    if audio_file_path.endswith('.mp3'):
        print("Converting MP3 to WAV format...")
        wav_file_path, _ = mp3_to_wav(audio_file_path)
        audio_file_path = wav_file_path
    
    # Split the file into 30-second segments
    segments = split_audio_file(audio_file_path)
    
    # Transcribe each segment
    full_transcript = ""
    for i, (segment_path, sample_rate) in enumerate(segments):
        print(f"\nProcessing segment {i+1}/{len(segments)}")
        segment_transcript = transcribe_audio_segment(segment_path, sample_rate)
        
        if segment_transcript:
            full_transcript += segment_transcript + " "
            print(f"Segment {i+1} transcription: {segment_transcript[:50]}...")
        else:
            print(f"Failed to transcribe segment {i+1}")
    
    # Cleanup temporary files
    print("\nCleaning up temporary files...")
    for segment_path, _ in segments:
        try:
            os.remove(segment_path)
            print(f"Deleted: {segment_path}")
        except Exception as e:
            print(f"Could not delete {segment_path}: {e}")
    
    return full_transcript

def main():
    # Step 0: Verify credentials before anything else
    print("=== Cantonese Audio Recorder ===")
    print("\nVerifying Google Cloud credentials...")
    creds_valid = verify_credentials()
    if not creds_valid:
        print("\nWARNING: Credential verification failed. Transcription may not work.")
        credentials_choice = input("Do you want to continue anyway? (y/n): ").lower()
        if credentials_choice not in ['y', 'yes']:
            print("Exiting. Please fix the credentials issue and try again.")
            return
        print("Continuing despite credential issues...")
    else:
        print("Credentials verified successfully!")

    # Step 1: Record audio
    device_name = select_device()
    recorded_file = record_until_closed(device_name)
    
    if not recorded_file:
        print("Recording failed or was empty.")
        return
    
    # Step 2: Ask if user wants to transcribe
    transcribe_choice = input(f"\nDo you want to transcribe the recorded file '{recorded_file}'? (y/n): ").lower()
    
    if transcribe_choice in ['y', 'yes']:
        # Step 3: Transcribe the audio
        print("\nStarting transcription process...")
        
        # Verify credentials again right before transcription
        if not creds_valid:
            print("Reminder: Credential verification failed earlier. Transcription may not work.")
            print("Attempting transcription anyway...")
        
        transcript = transcribe_audio(recorded_file)
        
        if transcript:
            # Save transcript to file
            output_file = recorded_file.replace('.wav', '.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            print(f"Transcription complete. Output saved to {output_file}")
            print("\nTranscript:")
            print(transcript)
        else:
            print("Transcription failed. Please check your credentials and try again.")
            print("\nTroubleshooting tips:")
            print("1. Verify your service_account_key.json file is valid")
            print("2. Make sure the Speech-to-Text API is enabled for your project")
            print("3. Check that the service account has the Speech-to-Text API role")
            print("4. Ensure your project has billing enabled")
            print("5. Check for any quotas or limits on your Google Cloud project")
    else:
        print("Transcription skipped.")

if __name__ == "__main__":
    main()