# Py Audio Capture Updates

## Recent Improvements

### Device Selection Enhancement
- Added interactive device selection menu
- Lists all available input devices with numbers
- Allows users to select specific device or use default
- Better handling of device detection for VB-Cable and other inputs

### Better Recording Experience
- Improved Ctrl+C handling for clean exit
- Added visual feedback during recording (dots every 5 seconds)
- Reduced audio chunk size for more responsive controls
- Emergency exit option (double Ctrl+C for force exit)
- Better error handling

### How to Use Updated Script

1. Install dependencies if not already installed:
   ```
   pip install sounddevice numpy wavio
   ```

2. Run the script:
   ```
   python source.py
   ```

3. Select your input device from the displayed list (VB-Cable recommended)

4. Recording will start automatically with visual progress indicators

5. Press Ctrl+C once to stop recording and save
   - If needed, press Ctrl+C again to force exit

6. Recordings are saved in the `output` folder with timestamp filenames