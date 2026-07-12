# Google Speech-to-Text Transcription

A Python script to transcribe MP3 audio files using Google's Speech-to-Text API.

## Setup

1. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. **Important: Get proper credentials**
   The current credentials file is in OAuth client format, but Google's Speech-to-Text API requires a service account key.

   To get a service account key:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create credentials" and select "Service account"
   - Follow the prompts to create a service account
   - Create a key for this service account (JSON format)
   - Download the key and save it as `service_account_key.json` in this directory

3. Set the environment variable to point to your service account key:
   ```
   export GOOGLE_APPLICATION_CREDENTIALS="service_account_key.json"
   ```

## Usage

Run the script with your MP3 file as the argument:
```
python transcribe_audio.py your_audio_file.mp3
```

The script will:
1. Convert the MP3 file to WAV format
2. Transcribe the audio using Google's Speech-to-Text API
3. Save the transcript to a text file with the same name as your audio file

## Requirements

- Python 3.7+
- Google Cloud Speech-to-Text API enabled in your Google Cloud project
- Service account with access to the Speech-to-Text API
- FFmpeg (for MP3 to WAV conversion via pydub)





export GOOGLE_APPLICATION_CREDENTIALS="service_account_key.json"

created the service account .json, from the google console, 



export GOOGLE_APPLICATION_CREDENTIALS="/Users/stanleytan/Downloads/google_text_to_speech/service_account_key.json"   



