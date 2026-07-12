import sounddevice as sd
import numpy as np
import wavio
import datetime
import os
import io
import threading
import time
import queue
from google.cloud import speech
from google.oauth2 import service_account
from pydub import AudioSegment

# Configuration
SAMPLE_RATE = 44100
CHANNELS = 1  # Mono recording
DTYPE = np.int16
CHUNK_SECONDS = 20  # Process in 20-second chunks

# Queue for passing audio chunks between threads
audio_queue = queue.Queue()
# Flag to signal when to stop
should_stop = False

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

def audio_callback(indata, frames, time, status):
    """This function is called for each audio block by the streaming function."""
    if status:
        print(f"Status: {status}")
    # Put the audio data in the queue
    audio_queue.put(indata.copy())

def recorder_thread(device_id):
    """Thread function that records audio from the specified device."""
    global should_stop
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs("./output", exist_ok=True)
        
        # The blocksize defines how many frames are processed each time the callback is called
        # For 20 seconds at 44100 Hz
        blocksize = int(SAMPLE_RATE * CHUNK_SECONDS)
        
        print(f"Starting recording from device {device_id}...")
        with sd.InputStream(device=device_id, channels=CHANNELS, 
                           samplerate=SAMPLE_RATE, dtype=DTYPE,
                           callback=audio_callback, blocksize=blocksize):

            # Keep recording until should_stop is set to True
            while not should_stop:
                time.sleep(0.1)
    
    except Exception as e:
        print(f"Error in recorder thread: {e}")
        should_stop = True

def get_filename_with_date_and_time():
    current_time = datetime.datetime.now()
    formatted_date_time = current_time.strftime('%m-%d-%Y_%H-%M-%S')
    filename = f"./output/recording_{formatted_date_time}.wav"
    return filename

def save_audio_chunk(audio_data):
    """Save an audio chunk to a WAV file with timestamp."""
    filename = get_filename_with_date_and_time()
    
    # Save to WAV file
    wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
    print(f"Saved audio chunk to {filename}")
    
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

def transcription_thread():
    """Thread function that processes audio chunks from the queue and transcribes them."""
    global should_stop
    
    while not should_stop or not audio_queue.empty():
        try:
            # Get a chunk from the queue with a timeout
            audio_data = audio_queue.get(timeout=1)
            
            # Save the audio chunk to a file
            audio_file = save_audio_chunk(audio_data)
            
            # Transcribe the audio
            transcript = transcribe_audio(audio_file)
            
            if transcript:
                print("\n" + "="*50)
                print(f"Transcription ({datetime.datetime.now().strftime('%H:%M:%S')}):")
                print(transcript)
                print("="*50 + "\n")
                
                # Save transcript to text file
                with open(audio_file.replace('.wav', '.txt'), 'w', encoding='utf-8') as f:
                    f.write(transcript)
            else:
                print("No speech detected in this chunk.")
                
            # Mark task as done
            audio_queue.task_done()
            
        except queue.Empty:
            # No chunks available, just continue
            continue
        except Exception as e:
            print(f"Error in transcription thread: {e}")

def main():
    """Main function that sets up the recording and transcription threads."""
    global should_stop
    
    print("=== VB-Cable Cantonese Recording and Transcription ===")
    print(f"Recording in {CHUNK_SECONDS}-second chunks")
    
    # Make sure Google credentials are set
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE"):
        print("WARNING: Google Cloud credentials not found in environment variables.")
        print("Please set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
        print("Continue anyway? (y/n)")
        if input().lower() != 'y':
            return
    
    # Find VB-Cable device
    device_id = find_vb_cable_device()
    
    # Create and start recorder thread
    rec_thread = threading.Thread(target=recorder_thread, args=(device_id,))
    rec_thread.daemon = True
    rec_thread.start()
    
    # Create and start transcription thread
    trans_thread = threading.Thread(target=transcription_thread)
    trans_thread.daemon = True
    trans_thread.start()
    
    print("\nRecording and transcribing. Press Ctrl+C to stop.\n")
    
    try:
        # Keep the main thread alive until Ctrl+C
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping recording and transcription...")
        should_stop = True
        
        # Wait for threads to finish
        rec_thread.join(timeout=2)
        trans_thread.join(timeout=5)
        
        print("Done!")

if __name__ == "__main__":
    main()