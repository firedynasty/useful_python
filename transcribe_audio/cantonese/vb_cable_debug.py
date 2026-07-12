import sounddevice as sd
import numpy as np
import wavio
import datetime
import os
import io
import time
import sys

# Configuration
SAMPLE_RATE = 44100
CHANNELS = 1  # Mono recording
DTYPE = np.int16
SECONDS_PER_CHUNK = 10  # Recording time for testing

def list_all_audio_devices():
    """Display detailed information about all available audio devices."""
    devices = sd.query_devices()
    
    print("\n===== DETAILED AUDIO DEVICE INFORMATION =====")
    print(f"Default input device: {sd.default.device[0]}")
    print(f"Default output device: {sd.default.device[1]}")
    print("\nALL AUDIO DEVICES:")
    
    for i, device in enumerate(devices):
        print(f"\n--- Device {i}: {device['name']} ---")
        for key, value in device.items():
            if key != 'name':  # Already printed the name
                print(f"  {key}: {value}")
    
    return devices

def test_recording_levels(device_id):
    """Record a short sample and analyze audio levels to detect silence."""
    print(f"\nTesting recording levels from device {device_id}...")
    
    # Record 3 seconds of audio
    test_duration = 3  # seconds
    num_frames = int(SAMPLE_RATE * test_duration)
    
    try:
        print(f"Recording {test_duration} seconds for level testing...")
        audio_data = sd.rec(frames=num_frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, device=device_id)
        sd.wait()
        
        # Calculate audio statistics
        audio_min = np.min(audio_data)
        audio_max = np.max(audio_data)
        audio_mean = np.mean(np.abs(audio_data))
        audio_rms = np.sqrt(np.mean(np.square(audio_data)))
        
        print("\nAudio Statistics:")
        print(f"Min value: {audio_min}")
        print(f"Max value: {audio_max}")
        print(f"Mean absolute value: {audio_mean}")
        print(f"RMS value: {audio_rms}")
        
        # Check if audio is mostly silence
        if audio_rms < 100:  # This threshold might need adjustment
            print("\n⚠️ WARNING: Audio signal is very low or silent!")
            print("This may indicate that no audio is being captured from this device.")
            print("If using VB-Cable, ensure that:")
            print("1. Audio is playing through your computer while recording")
            print("2. VB-Cable is set as the output device for your audio source")
            print("3. The correct VB-Cable input is selected here")
            print("4. System volume and VB-Cable volume are not muted or set too low")
        else:
            print("\n✅ Audio signal detected! Recording should be working properly.")
        
        # Save the test recording
        test_filename = f"./output/test_recording_{datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')}.wav"
        os.makedirs(os.path.dirname(test_filename), exist_ok=True)
        wavio.write(test_filename, audio_data, SAMPLE_RATE, sampwidth=2)
        print(f"Test recording saved to: {test_filename}")
        
        return test_filename, audio_rms > 100
        
    except Exception as e:
        print(f"Error during test recording: {e}")
        return None, False

def select_device_with_testing():
    """Select an audio input device with enhanced testing and feedback."""
    devices = sd.query_devices()
    
    # Filter to only input devices
    input_devices = [(i, d) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    
    if not input_devices:
        print("No input devices found. Please check your audio setup.")
        sys.exit(1)
    
    print("\n===== AVAILABLE INPUT DEVICES =====")
    for i, (device_id, device) in enumerate(input_devices):
        print(f"{i}: {device['name']} (Device ID: {device_id})")
    
    # Look for VB-Cable devices
    vb_cable_indices = [i for i, (device_id, device) in enumerate(input_devices) 
                        if 'VB-Cable' in device['name'] or 'VB-Audio' in device['name']]
    
    if vb_cable_indices:
        print("\nVB-Cable devices detected!")
        for idx in vb_cable_indices:
            device_id, device = input_devices[idx]
            print(f"Option {idx}: {device['name']} (Device ID: {device_id})")
    
    # Get user selection
    try:
        choice_idx = int(input("\nSelect device number (or press Enter for default): ") or "0")
        if 0 <= choice_idx < len(input_devices):
            device_id, device = input_devices[choice_idx]
            selected_name = device['name']
            print(f"Selected: {selected_name} (Device ID: {device_id})")
            
            # Test the selected device
            test_file, has_audio = test_recording_levels(device_id)
            
            if not has_audio:
                print("\n⚠️ The selected device appears to be recording silence.")
                print("Do you want to:")
                print("1. Continue with this device anyway")
                print("2. Try a different device")
                print("3. Display detailed device information and try again")
                print("4. Quit")
                
                action = input("Enter your choice (1-4): ")
                
                if action == "2":
                    return select_device_with_testing()  # Start over
                elif action == "3":
                    list_all_audio_devices()
                    return select_device_with_testing()  # Start over with more info
                elif action == "4":
                    print("Exiting program.")
                    sys.exit(0)
                # For option 1 or invalid input, continue with the current device
            
            return device_id, selected_name
            
    except ValueError:
        print("Invalid selection, using default.")
    
    # Default to first device if no selection made
    device_id, device = input_devices[0]
    print(f"Using default device: {device['name']} (Device ID: {device_id})")
    test_recording_levels(device_id)
    return device_id, device['name']

def record_audio_chunk(device_id, seconds=SECONDS_PER_CHUNK):
    """Record a chunk of audio from the specified device."""
    # Calculate number of frames to record
    num_frames = int(SAMPLE_RATE * seconds)
    
    print(f"Recording {seconds} seconds of audio...")
    
    try:
        # Record audio
        audio_data = sd.rec(frames=num_frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, device=device_id)
        
        # Show a progress indicator
        for i in range(seconds):
            print(".", end="", flush=True)
            time.sleep(1)
        print()
        
        # Wait until recording is finished
        sd.wait()
        
        print(f"Finished recording {seconds} seconds of audio.")
        
        # Calculate audio statistics
        audio_rms = np.sqrt(np.mean(np.square(audio_data)))
        
        if audio_rms < 100:  # This threshold might need adjustment
            print("⚠️ WARNING: Recorded audio signal is very low or silent!")
        
        # Save to a WAV file
        output_dir = "./output"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/recording_{datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')}.wav"
        wavio.write(filename, audio_data, SAMPLE_RATE, sampwidth=2)
        print(f"Saved as '{filename}'")
        
        return filename
        
    except Exception as e:
        print(f"Error during recording: {e}")
        return None

def play_audio_file(file_path):
    """Play back an audio file to verify recording quality."""
    try:
        print(f"Playing back recorded file: {file_path}")
        data, fs = sd.read(file_path)
        sd.play(data, fs)
        sd.wait()
        print("Playback finished.")
    except Exception as e:
        print(f"Error during playback: {e}")

def main():
    """Main function that walks through VB-Cable debugging and testing."""
    print("=== VB-Cable Audio Debugging Tool ===")
    
    # Check if output directory exists
    os.makedirs("./output", exist_ok=True)
    
    # Step 1: List all audio devices
    print("\nStep 1: Listing all audio devices...")
    devices = list_all_audio_devices()
    
    # Step 2: Select and test a device
    print("\nStep 2: Select and test an input device...")
    device_id, device_name = select_device_with_testing()
    
    # Step 3: Record a sample
    print("\nStep 3: Recording a test sample...")
    print("\nPlease make sure audio is playing on your computer")
    print("during this test recording if using VB-Cable.")
    input("Press Enter to start recording...")
    
    recorded_file = record_audio_chunk(device_id)
    
    if recorded_file:
        # Step 4: Offer to play back the recording
        play_choice = input("\nWould you like to play back the recording to verify quality? (y/n): ")
        if play_choice.lower() in ['y', 'yes']:
            play_audio_file(recorded_file)
        
        print("\nDebugging complete!")
        print(f"For future reference, use device ID {device_id} ({device_name})")
        print(f"Test recording saved to: {recorded_file}")
        
        print("\nRecommended next steps:")
        print("1. Check if the test recording contains the expected audio")
        print("2. In your recording script, ensure you're using the correct device ID")
        print("3. If using record_and_transcribe_cantonese.py, select option", 
              [i for i, (id, dev) in enumerate([(i, d) for i, d in enumerate(devices) if d['max_input_channels'] > 0]) if id == device_id][0])
    else:
        print("\nRecording failed. Please check your audio setup and try again.")

if __name__ == "__main__":
    main()