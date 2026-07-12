import sounddevice as sd
import numpy as np
import wavio
import datetime
import os
import time
import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Configuration
SAMPLE_RATE = 44100
CHANNELS = 1  # Mono recording
DTYPE = np.int16
WINDOW_SIZE = 1000  # samples for visualization

# For real-time visualization
fig, ax = plt.subplots()
line, = ax.plot(np.zeros(WINDOW_SIZE))
ax.set_ylim(-32768, 32767)  # Full int16 range
ax.set_xlim(0, WINDOW_SIZE)
ax.set_title('Real-time Audio Level Monitor')
ax.set_xlabel('Sample')
ax.set_ylabel('Amplitude')
fig.tight_layout()

# Buffer for audio data
audio_buffer = np.zeros(WINDOW_SIZE)

def list_audio_devices():
    """List all available audio devices with details."""
    devices = sd.query_devices()
    
    print("\n=== AUDIO DEVICE INFORMATION ===")
    print(f"Default input device: {sd.default.device[0]}")
    print(f"Default output device: {sd.default.device[1]}")
    
    print("\nINPUT DEVICES:")
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"{i}: {d['name']} (Channels: {d['max_input_channels']}, Default Sr: {d['default_samplerate']})")
    
    print("\nOUTPUT DEVICES:")
    for i, d in enumerate(devices):
        if d['max_output_channels'] > 0:
            print(f"{i}: {d['name']} (Channels: {d['max_output_channels']}, Default Sr: {d['default_samplerate']})")
    
    return devices

def select_audio_devices():
    """Let user select input and output devices for testing."""
    devices = sd.query_devices()
    
    # Filter to only show input and output devices
    input_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    output_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_output_channels'] > 0]
    
    # Look for VB-Cable devices
    vb_input_indices = [i for i, (idx, name) in enumerate(input_devices) 
                       if 'VB-Cable' in name or 'VB-Audio' in name or 'VB Audio' in name]
    
    vb_output_indices = [i for i, (idx, name) in enumerate(output_devices) 
                        if 'VB-Cable' in name or 'VB-Audio' in name or 'VB Audio' in name]
    
    # Print input devices
    print("\n=== INPUT DEVICES ===")
    for i, (idx, name) in enumerate(input_devices):
        vb_marker = " (VB-Cable)" if i in vb_input_indices else ""
        print(f"{i}: {name}{vb_marker} (Device ID: {idx})")
    
    # Default to VB-Cable input if available
    default_input = vb_input_indices[0] if vb_input_indices else 0
    
    # Get input selection
    try:
        input_choice = int(input(f"\nSelect INPUT device (or press Enter for default {default_input}): ") or default_input)
        if 0 <= input_choice < len(input_devices):
            input_id = input_devices[input_choice][0]
            print(f"Selected input: {input_devices[input_choice][1]} (Device ID: {input_id})")
        else:
            print("Invalid selection, using default.")
            input_id = input_devices[default_input][0]
    except ValueError:
        print("Invalid selection, using default.")
        input_id = input_devices[default_input][0]
    
    # Print output devices
    print("\n=== OUTPUT DEVICES ===")
    for i, (idx, name) in enumerate(output_devices):
        vb_marker = " (VB-Cable)" if i in vb_output_indices else ""
        print(f"{i}: {name}{vb_marker} (Device ID: {idx})")
    
    # Default to system output but recommend VB-Cable if available
    default_output = vb_output_indices[0] if vb_output_indices else 0
    
    # Get output selection
    try:
        output_choice = int(input(f"\nSelect OUTPUT device (or press Enter for default {default_output}): ") or default_output)
        if 0 <= output_choice < len(output_devices):
            output_id = output_devices[output_choice][0]
            print(f"Selected output: {output_devices[output_choice][1]} (Device ID: {output_id})")
        else:
            print("Invalid selection, using default.")
            output_id = output_devices[default_output][0]
    except ValueError:
        print("Invalid selection, using default.")
        output_id = output_devices[default_output][0]
    
    return input_id, output_id

def audio_callback(indata, frames, time, status):
    """Callback for audio stream to update visualization."""
    global audio_buffer
    if status:
        print(f"Status: {status}")
    
    # Roll the buffer and add new data
    audio_buffer = np.roll(audio_buffer, -len(indata))
    audio_buffer[-len(indata):] = indata.flatten()
    
    # Calculate RMS for this chunk and print level meter
    rms = np.sqrt(np.mean(np.square(indata)))
    max_val = np.max(np.abs(indata))
    
    # Visual level meter in console
    meter_length = 40
    level = int(min(meter_length, meter_length * (rms / 10000)))
    print(f"\rRMS: {rms:8.2f} | {'#' * level}{' ' * (meter_length - level)} | Max: {max_val:8.2f}", end="")

def update_plot(frame):
    """Update function for matplotlib animation."""
    line.set_ydata(audio_buffer)
    return line,

def visualize_device_audio(device_id):
    """Real-time visualization of audio from a device."""
    print(f"\nVisualizing audio from device {device_id}")
    print("Close the plot window to stop visualization")
    
    try:
        # Set up the animation
        ani = FuncAnimation(fig, update_plot, interval=30, blit=True)
        
        # Start the audio stream
        with sd.InputStream(device=device_id, channels=CHANNELS, 
                           samplerate=SAMPLE_RATE, dtype=DTYPE,
                           callback=audio_callback):
            plt.show()
        
    except Exception as e:
        print(f"Error during visualization: {e}")

def play_test_tone(output_device, duration=3):
    """Play a test tone to the selected output device."""
    print(f"\nPlaying test tone on device {output_device} for {duration} seconds")
    
    # Generate a simple sine wave test tone
    t = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    test_tone = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone at 30% volume
    
    try:
        # Play the test tone
        sd.play(test_tone, SAMPLE_RATE, device=output_device)
        sd.wait()
        print("Test tone complete")
    except Exception as e:
        print(f"Error playing test tone: {e}")

def record_test_sample(input_device, duration=5):
    """Record a test sample from the selected input device."""
    print(f"\nRecording {duration} seconds from device {input_device}")
    
    # Calculate frames
    frames = int(SAMPLE_RATE * duration)
    
    try:
        # Record the audio
        audio_data = sd.rec(frames=frames, samplerate=SAMPLE_RATE, 
                           channels=CHANNELS, dtype=DTYPE, device=input_device)
        
        # Show progress
        for i in range(duration):
            print(f"\rRecording {i+1}/{duration} seconds...", end="")
            time.sleep(1)
        print("\rRecording complete!            ")
        
        # Wait for recording to complete
        sd.wait()
        
        # Calculate stats
        rms = np.sqrt(np.mean(np.square(audio_data)))
        max_val = np.max(np.abs(audio_data))
        
        print(f"\nAudio stats:")
        print(f"RMS level: {rms:.2f}")
        print(f"Max value: {max_val:.2f}")
        
        if rms < 100:
            print("\n⚠️ WARNING: Very low audio levels detected. Recording may be silent.")
            print("Check that audio is playing and being routed correctly to the input device.")
        
        # Save the recording
        os.makedirs("./output", exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
        filename = f"./output/test_recording_{timestamp}.wav"
        
        wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
        print(f"Test recording saved to: {filename}")
        
        return filename, rms >= 100
        
    except Exception as e:
        print(f"Error during recording: {e}")
        return None, False

def test_with_tone(input_device, output_device):
    """Test the full audio path by playing a tone and recording it simultaneously."""
    print("\n=== AUDIO PATH TEST ===")
    print(f"This test will play a tone on device {output_device} and record from device {input_device}")
    print("For VB-Cable testing, these should be different devices")
    print("The output device should feed into the input device")
    
    # Duration of test
    duration = 5  # seconds
    
    # Generate a test tone with increasing frequency
    t = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    frequency = np.linspace(300, 1200, int(SAMPLE_RATE * duration))
    test_tone = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Prepare for recording
    frames = int(SAMPLE_RATE * duration)
    recorded_audio = np.zeros((frames, CHANNELS), dtype=DTYPE)
    
    try:
        # Start recording
        with sd.InputStream(device=input_device, channels=CHANNELS, 
                           samplerate=SAMPLE_RATE, dtype=DTYPE) as instream:
            
            # Start playback
            sd.play(test_tone, SAMPLE_RATE, device=output_device)
            
            # Record while playing
            print("\nRecording and playing simultaneously...")
            chunk_size = int(SAMPLE_RATE * 0.1)  # 100ms chunks
            for i in range(0, frames, chunk_size):
                if i + chunk_size > frames:
                    chunk_size = frames - i
                
                chunk, overflowed = instream.read(chunk_size)
                if overflowed:
                    print("Buffer overflow!")
                
                recorded_audio[i:i+chunk_size] = chunk
                
                # Progress indicator
                progress = (i + chunk_size) / frames * 100
                print(f"\rProgress: {progress:.1f}%", end="")
                
            print("\rTest complete!          ")
            
            # Wait for playback to finish
            sd.wait()
        
        # Analyze the recorded audio
        rms = np.sqrt(np.mean(np.square(recorded_audio)))
        max_val = np.max(np.abs(recorded_audio))
        
        print(f"\nRecorded audio stats:")
        print(f"RMS level: {rms:.2f}")
        print(f"Max value: {max_val:.2f}")
        
        # Save the recording
        os.makedirs("./output", exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
        filename = f"./output/tone_test_{timestamp}.wav"
        
        wavio.write(filename, recorded_audio, SAMPLE_RATE, sampwidth=2)
        print(f"Test recording saved to: {filename}")
        
        # Evaluate results
        if rms < 100:
            print("\n⚠️ WARNING: Very low audio levels detected in the recording.")
            print("This indicates the audio path between output and input devices is not working properly.")
            print("\nTroubleshooting steps:")
            print("1. Make sure VB-Cable is properly installed")
            print("2. Check system sound settings to ensure VB-Cable is configured correctly")
            print("3. Try using system audio controls to route audio to VB-Cable")
            print("4. Try restarting the VB-Cable driver")
            return False
        else:
            print("\n✅ Success! Audio path between output and input devices is working.")
            print(f"You should use device {input_device} as your recording input.")
            return True
            
    except Exception as e:
        print(f"Error during audio path test: {e}")
        return False

def main():
    """Main function for macOS audio testing."""
    print("=== macOS Audio Testing Tool ===")
    print("This tool will help diagnose issues with audio input and output devices,")
    print("especially for VB-Cable configuration.")
    
    # List all audio devices
    print("\nStep 1: Listing all audio devices")
    devices = list_audio_devices()
    
    # Let user select input and output devices
    print("\nStep 2: Select devices for testing")
    input_device, output_device = select_audio_devices()
    
    # Menu loop
    while True:
        print("\n=== AUDIO TESTING MENU ===")
        print("1. Visualize input device audio in real-time")
        print("2. Play test tone on output device")
        print("3. Record test sample from input device")
        print("4. Test full audio path (play tone and record simultaneously)")
        print("5. Change devices")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == "1":
            visualize_device_audio(input_device)
        elif choice == "2":
            play_test_tone(output_device)
        elif choice == "3":
            record_test_sample(input_device)
        elif choice == "4":
            test_with_tone(input_device, output_device)
        elif choice == "5":
            input_device, output_device = select_audio_devices()
        elif choice == "6":
            print("\nExiting audio testing tool.")
            break
        else:
            print("Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main()