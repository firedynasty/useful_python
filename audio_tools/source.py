import sounddevice as sd
import numpy as np
import wavio
import datetime
import sys
import os

# Configuration for the recording
SAMPLE_RATE = 44100
CHANNELS = 2
DTYPE = np.int16
SECONDS_PER_CHUNK = 10  # You can modify this to record larger or smaller chunks at a time

def select_device():
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]
    device_names = [device['name'] for device in input_devices]

    # Auto-select Loopback if available
    for name in device_names:
        if "loopback" in name.lower():
            print(f"Using Loopback device: {name}")
            return name

    # Loopback not found — fall back and warn
    print("Warning: No Loopback device found. Available input devices:")
    for i, name in enumerate(device_names):
        print(f"{i}: {name}")

    if not input_devices:
        print("No input devices found. Please check your audio setup.")
        exit(1)

    print(f"Falling back to: {device_names[0]}")
    return device_names[0]

def get_filename_with_date_and_time(output_dir):
    current_time = datetime.datetime.now()
    formatted_date_time = current_time.strftime('%m-%d-%Y_%H-%M-%S')
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"recording_{formatted_date_time}.wav")
    return filename

def record_until_closed(device_name, output_dir, logfile=None):
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
                filename = get_filename_with_date_and_time(output_dir)
                
                # Save to a WAV file
                wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
                total_seconds = len(audio_data) / SAMPLE_RATE
                print(f"Recorded: {total_seconds:.1f}s")
                print(f"Saved as '{filename}'")
                if logfile:
                    with open(logfile, 'w') as f:
                        f.write(filename + '\n')
            else:
                print("No data recorded.")
    except Exception as e:
        print(f"Error during recording: {e}")

if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./output"
    logfile = sys.argv[2] if len(sys.argv) > 2 else None
    device_name = select_device()
    record_until_closed(device_name, output_dir, logfile)
