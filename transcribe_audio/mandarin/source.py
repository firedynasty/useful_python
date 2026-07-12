import sounddevice as sd
import numpy as np
import wavio
import datetime

# Configuration for the recording
SAMPLE_RATE = 44100
CHANNELS = 1  # Changed from 2 to 1 for mono recording
DTYPE = np.int16
SECONDS_PER_CHUNK = 10  # You can modify this to record larger or smaller chunks at a time

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
            else:
                print("No data recorded.")
    except Exception as e:
        print(f"Error during recording: {e}")

if __name__ == "__main__":
    device_name = select_device()
    record_until_closed(device_name)
