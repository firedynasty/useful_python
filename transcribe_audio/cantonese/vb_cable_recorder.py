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
    
    # First, look for devices with VB-Cable in the name
    vb_cable_devices = [i for i, d in enumerate(devices) if ('VB-Cable' in d['name'] or 'VB-Audio' in d['name']) and d['max_input_channels'] > 0]
    
    # List all input devices for the user
    input_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    
    print("Available input devices:")
    for i, (device_id, name) in enumerate(input_devices):
        print(f"{i}: {name} (Device ID: {device_id})")
        
        # Add a VB-Cable indicator if this is one of them
        if device_id in vb_cable_devices:
            print("   ↳ VB-Cable device detected!")
    
    if vb_cable_devices:
        # Default to the first VB-Cable device
        default_option = [i for i, (device_id, _) in enumerate(input_devices) if device_id == vb_cable_devices[0]][0]
        print(f"\nDefault option ({default_option}) is the first VB-Cable device")
    else:
        default_option = 0
        print("\nNo VB-Cable devices detected. Using first available input as default.")
    
    try:
        choice = int(input(f"\nSelect device number (or press Enter for default {default_option}): ") or str(default_option))
        if 0 <= choice < len(input_devices):
            device_id = input_devices[choice][0]
            print(f"Selected: {input_devices[choice][1]} (Device ID: {device_id})")
            return device_id
    except ValueError:
        print("Invalid selection, using default.")
        return input_devices[default_option][0]

def test_audio_levels(device_id, test_duration=3):
    """Test audio levels to ensure the device is capturing sound."""
    print(f"\nTesting audio levels on device {device_id} for {test_duration} seconds...")
    print("Make sure audio is playing on your system during this test")
    
    num_frames = int(SAMPLE_RATE * test_duration)
    
    try:
        # Record a short test sample
        print("Recording test sample...")
        audio_data = sd.rec(frames=num_frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, device=device_id)
        
        # Show progress
        for _ in range(test_duration):
            print(".", end="", flush=True)
            time.sleep(1)
        print()
        
        sd.wait()
        
        # Calculate audio statistics
        audio_rms = np.sqrt(np.mean(np.square(audio_data)))
        
        print(f"Audio RMS level: {audio_rms:.2f}")
        
        if audio_rms < 100:  # Threshold for "silence" detection
            print("\n⚠️ WARNING: Audio levels are very low. The recording may be silent.")
            print("Possible solutions:")
            print("1. Ensure audio is playing on your system")
            print("2. Make sure VB-Cable is configured as an output device for your audio")
            print("3. Check system volume and make sure nothing is muted")
            
            retry = input("Do you want to try recording anyway? (y/n): ")
            return retry.lower() in ['y', 'yes']
        else:
            print("✅ Audio levels look good!")
            return True
            
    except Exception as e:
        print(f"Error during audio level test: {e}")
        return False

def get_filename_with_date_and_time():
    """Generate a filename with the current date and time."""
    current_time = datetime.datetime.now()
    formatted_date_time = current_time.strftime('%m-%d-%Y_%H-%M-%S')
    filename = f"./output/recording_{formatted_date_time}.wav"
    return filename

def record_chunk(device_id, seconds=SECONDS_PER_CHUNK):
    """Record a chunk of audio from the specified device."""
    # Calculate number of frames to record
    num_frames = int(SAMPLE_RATE * seconds)
    
    print(f"\nRecording {seconds} seconds of audio...")
    
    # Record audio
    audio_data = sd.rec(frames=num_frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, device=device_id)
    
    # Wait and show progress
    for i in range(seconds):
        if i % 5 == 0:  # Print progress every 5 seconds
            print(f"{i}/{seconds} seconds", end="", flush=True)
        else:
            print(".", end="", flush=True)
        time.sleep(1)
    print(f" {seconds}/{seconds} seconds")
    
    # Wait until recording is finished
    sd.wait()
    
    print("Recording complete.")
    
    # Check for silence
    audio_rms = np.sqrt(np.mean(np.square(audio_data)))
    if audio_rms < 100:
        print("⚠️ WARNING: Recorded audio has very low levels and may be silent.")
    
    # Save to a WAV file
    filename = get_filename_with_date_and_time()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
    print(f"Saved as '{filename}'")
    
    return filename

def transcribe_audio(audio_file_path):
    """Transcribe Cantonese audio file using Google Speech-to-Text API."""
    print(f"\nTranscribing {os.path.basename(audio_file_path)}...")
    
    # Create client with language-specific credentials
    try:
        # Look for credentials in common locations
        cantonese_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
        hardcoded_path = "/Users/stanleytan/Documents/46-python/transcribe_audio/cantonese/service_account_key.json"
        
        if cantonese_credentials:
            print(f"Using credentials from environment variable")
            credentials = service_account.Credentials.from_service_account_file(cantonese_credentials)
        elif os.path.exists(hardcoded_path):
            print(f"Using hardcoded credentials path")
            credentials = service_account.Credentials.from_service_account_file(hardcoded_path)
        else:
            print("No specific credentials found, using default")
            client = speech.SpeechClient()
            credentials = None
            
        if credentials:
            client = speech.SpeechClient(credentials=credentials)
            
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    
    try:
        # Read the audio file
        with io.open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()
        
        # Configure audio
        audio = speech.RecognitionAudio(content=content)
        
        # Configure request with Cantonese language code
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="yue-Hant-HK",  # Traditional Chinese (Cantonese)
            enable_automatic_punctuation=True,
            # Try increasing sensitivity
            # If audio is quiet, this might help
            audio_channel_count=CHANNELS,
            enable_separate_recognition_per_channel=False,
            model="default",  # Using default model for best general results
            use_enhanced=True,  # Use enhanced model
        )
        
        # Make request
        print("Sending audio to Google for transcription...")
        response = client.recognize(config=config, audio=audio)
        
        # Process response
        transcript = ""
        results_count = 0
        
        for result in response.results:
            results_count += 1
            transcript += result.alternatives[0].transcript + " "
        
        if results_count == 0:
            print("No speech detected in the audio.")
            # Check if there was actually sound in the recording
            audio_data, _ = sd.read(audio_file_path)
            audio_rms = np.sqrt(np.mean(np.square(audio_data)))
            
            if audio_rms < 100:
                print("The audio recording appears to be silent or very quiet.")
                print("Please check that audio is actually playing and being captured by VB-Cable.")
            else:
                print("The audio has sound, but Google couldn't transcribe any speech.")
                print("This might be due to background noise, music, or non-speech audio.")
            
            return None
        else:
            return transcript
            
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

def main():
    """Main function that continuously records and transcribes audio."""
    print("=== VB-Cable Cantonese Recording & Transcription ===")
    print(f"Recording in {SECONDS_PER_CHUNK}-second chunks")
    
    # Create output directory if it doesn't exist
    os.makedirs("./output", exist_ok=True)
    
    # Find and test VB-Cable device
    device_id = find_vb_cable_device()
    
    # Test audio levels
    if not test_audio_levels(device_id):
        print("Exiting due to audio level issues.")
        return
    
    try:
        print("\nStarting continuous recording and transcription.")
        print("Press Ctrl+C at any time to stop.\n")
        
        chunks_recorded = 0
        
        # Continuous recording loop
        while True:
            chunks_recorded += 1
            print(f"\n=== Chunk #{chunks_recorded} ===")
            
            # Record audio chunk
            audio_file = record_chunk(device_id, SECONDS_PER_CHUNK)
            
            # Transcribe the audio
            transcript = transcribe_audio(audio_file)
            
            if transcript:
                print("\n" + "="*50)
                print(f"Transcription (Chunk #{chunks_recorded}):")
                print(transcript)
                print("="*50 + "\n")
                
                # Save transcript to text file
                text_file = audio_file.replace('.wav', '.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                print(f"Saved transcript to {text_file}")
            else:
                print("\nNo transcription for this chunk.")
            
    except KeyboardInterrupt:
        print("\nStopping recording and transcription...")
        print("Done!")

if __name__ == "__main__":
    main()