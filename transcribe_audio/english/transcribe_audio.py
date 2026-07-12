import os
import io
import google.auth
from google.cloud import speech
from pydub import AudioSegment
from google.oauth2 import service_account
import google_auth_oauthlib.flow
import googleapiclient.discovery

def mp3_to_wav(mp3_file_path):
    """Convert MP3 file to WAV format for Google Speech-to-Text API."""
    audio = AudioSegment.from_mp3(mp3_file_path)
    wav_file_path = mp3_file_path.replace('.mp3', '.wav')
    audio.export(wav_file_path, format="wav")
    return wav_file_path, audio.frame_rate

def transcribe_audio(audio_file_path):
    """Transcribe audio file using Google Speech-to-Text API."""
    print("Preparing to transcribe...")
    
    # Default sample rate (will be overridden if MP3 is converted)
    sample_rate = 44100
    
    # Check if file is MP3 and convert if needed
    if audio_file_path.endswith('.mp3'):
        print("Converting MP3 to WAV format...")
        audio_file_path, sample_rate = mp3_to_wav(audio_file_path)
        print(f"Detected sample rate: {sample_rate} Hz")
    
    # Read the audio file
    with io.open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with explicit credentials
    try:
        print("Authenticating with Google Cloud...")
        # For service account approach
        credentials, project = google.auth.default()
        client = speech.SpeechClient(credentials=credentials)
    except Exception as e:
        print(f"Authentication error: {e}")
        print("Trying alternative authentication method...")
        # If you need to use OAuth flow instead
        # Note: This is typically not used for Speech-to-Text API
        # You should obtain a service account key instead
        print("Please obtain a service account key from Google Cloud Console.")
        print("Visit: https://console.cloud.google.com/apis/credentials")
        print("Create a service account key and download it as JSON.")
        print("Then run the script again with that key file.")
        return None
    
    # Configure audio
    audio = speech.RecognitionAudio(content=content)
    
    # Configure request with detected sample rate
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )
    
    # Make request
    print("Transcribing audio...")
    response = client.recognize(config=config, audio=audio)
    
    # Process response
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    
    return transcript

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python transcribe_audio.py <audio_file_path>")
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    
    if not os.path.exists(audio_file_path):
        print(f"Error: File '{audio_file_path}' not found.")
        sys.exit(1)
    
    transcript = transcribe_audio(audio_file_path)
    
    if transcript:
        # Save transcript to file
        output_file = audio_file_path.replace('.mp3', '.txt').replace('.wav', '.txt')
        with open(output_file, 'w') as f:
            f.write(transcript)
        
        print(f"Transcription complete. Output saved to {output_file}")
        print("\nTranscript:")
        print(transcript)
    else:
        print("Transcription failed. Please check your credentials and try again.")