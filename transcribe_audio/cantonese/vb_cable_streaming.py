import sounddevice as sd
import numpy as np
import wavio
import datetime
import os
import io
import time
from google.cloud import speech
from google.oauth2 import service_account
from pydub import AudioSegment

# Configuration
SAMPLE_RATE = 44100
CHANNELS = 1  # Mono recording
DTYPE = np.int16
SECONDS_PER_CHUNK = 20  # Record in 20-second chunks

def find_vb_cable_device():
    """Find the VB-Cable device in the list of available devices."""
    devices = sd.query_devices()
    vb_cable_devices = [i for i, d in enumerate(devices) if 'VB-Cable' in d['name'] and d['max_input_channels'] > 0]
    
    if not vb_cable_devices:
        print("No VB-Cable input device found. Available input devices:")
        input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        for i in input_devices:
            print(f"{i}: {devices[i]['name']}")
        device_id = int(input("Select input device number: "))
    else:
        device_id = vb_cable_devices[0]
        print(f"Found VB-Cable at device index {device_id}: {devices[device_id]['name']}")
    
    return device_id

def get_filename_with_date_and_time():
    current_time = datetime.datetime.now()
    formatted_date_time = current_time.strftime('%m-%d-%Y_%H-%M-%S')
    filename = f"./output/recording_{formatted_date_time}.wav"
    return filename

def record_chunk(device_id, seconds=SECONDS_PER_CHUNK):
    """Record a chunk of audio from the specified device."""
    # Calculate number of frames to record
    num_frames = int(SAMPLE_RATE * seconds)
    
    print(f"Recording {seconds} seconds of audio...")
    
    # Record audio
    audio_data = sd.rec(frames=num_frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, device=device_id)
    
    # Wait until recording is finished
    sd.wait()
    
    print(f"Finished recording {seconds} seconds of audio.")
    
    # Save to a WAV file
    filename = get_filename_with_date_and_time()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
    print(f"Saved as '{filename}'")
    
    return filename

def transcribe_audio(audio_file_path):
    """Transcribe Cantonese audio file using Google Speech-to-Text API."""
    print(f"Transcribing {os.path.basename(audio_file_path)}...")
    
    # Read the audio file
    with io.open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with language-specific credentials
    try:
        # Try to use language-specific credentials first
        cantonese_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
        if cantonese_credentials:
            print(f"Using Cantonese-specific credentials")
            credentials = service_account.Credentials.from_service_account_file(cantonese_credentials)
            client = speech.SpeechClient(credentials=credentials)
        else:
            # Fall back to default credentials
            print("Using default credentials")
            client = speech.SpeechClient()
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    
    # Configure audio
    audio = speech.RecognitionAudio(content=content)
    
    # Configure request with Cantonese language code
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="yue-Hant-HK",  # Traditional Chinese (Cantonese)
        enable_automatic_punctuation=True,
    )
    
    # Make request
    response = client.recognize(config=config, audio=audio)
    
    # Process response
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    
    return transcript

def main():
    """Main function that continuously records and transcribes audio in a loop."""
    print("=== VB-Cable Cantonese Real-time Recording and Transcription ===")
    print(f"Recording in {SECONDS_PER_CHUNK}-second chunks")
    
    # Make sure Google credentials are set
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE"):
        print("WARNING: Google Cloud credentials not found in environment variables.")
        print("Please set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
        print("Continue anyway? (y/n)")
        if input().lower() != 'y':
            return
    
    # Find VB-Cable device
    device_id = find_vb_cable_device()
    
    try:
        print("\nStarting continuous recording and transcription. Press Ctrl+C to stop.\n")
        
        # Continuous recording loop
        while True:
            # Record audio chunk
            audio_file = record_chunk(device_id)
            
            # Transcribe the audio
            transcript = transcribe_audio(audio_file)
            
            if transcript:
                print("\n" + "="*50)
                print(f"Transcription ({datetime.datetime.now().strftime('%H:%M:%S')}):")
                print(transcript)
                print("="*50 + "\n")
                
                # Save transcript to text file
                text_file = audio_file.replace('.wav', '.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                print(f"Saved transcript to {text_file}")
            else:
                print("No speech detected in this chunk.")
            
    except KeyboardInterrupt:
        print("\nStopping recording and transcription...")
        print("Done!")

if __name__ == "__main__":
    main()