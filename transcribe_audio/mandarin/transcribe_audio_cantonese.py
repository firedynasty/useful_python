import os
import io
import math
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
    audio.export(wav_file_path, format="wav", parameters=["-ar", str(audio.frame_rate), "-ac", "1", "-sample_fmt", "s16"])
    return wav_file_path, audio.frame_rate

def split_audio_file(audio_file_path, segment_length_ms=30000):
    """Split audio file into segments of specified length (default 30 seconds)."""
    print(f"Loading audio file: {audio_file_path}")
    audio = AudioSegment.from_file(audio_file_path)
    sample_rate = audio.frame_rate
    
    # Calculate number of segments
    duration_ms = len(audio)
    num_segments = math.ceil(duration_ms / segment_length_ms)
    print(f"Audio duration: {duration_ms/1000:.2f} seconds")
    print(f"Splitting into {num_segments} segments of {segment_length_ms/1000} seconds each")
    
    segments = []
    for i in range(num_segments):
        start_ms = i * segment_length_ms
        end_ms = min((i + 1) * segment_length_ms, duration_ms)
        segment = audio[start_ms:end_ms]
        segment_path = f"{os.path.splitext(audio_file_path)[0]}_segment_{i+1}.wav"
        segment.export(segment_path, format="wav", parameters=["-ar", str(sample_rate), "-ac", "1", "-sample_fmt", "s16"])
        segments.append((segment_path, sample_rate))
        print(f"Created segment {i+1}/{num_segments}: {segment_path}")
    
    return segments

def transcribe_audio_segment(segment_path, sample_rate):
    """Transcribe a single audio segment using Google Speech-to-Text API."""
    print(f"Transcribing segment: {segment_path}")
    
    # Read the audio file
    with io.open(segment_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with language-specific credentials
    try:
        # Try to use language-specific credentials first
        cantonese_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
        if cantonese_credentials:
            credentials = service_account.Credentials.from_service_account_file(cantonese_credentials)
            client = speech.SpeechClient(credentials=credentials)
        else:
            # Fall back to default credentials
            credentials, project = google.auth.default()
            client = speech.SpeechClient(credentials=credentials)
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    
    # Configure audio
    audio = speech.RecognitionAudio(content=content)
    
    # Configure request with Chinese language code
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
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

def transcribe_audio(audio_file_path):
    """Transcribe Chinese audio file using Google Speech-to-Text API."""
    print("Preparing to transcribe Chinese audio...")
    
    # Default sample rate (will be overridden if MP3 is converted)
    sample_rate = 44100
    
    # Check if file is MP3 and convert if needed
    if audio_file_path.endswith('.mp3'):
        print("Converting MP3 to WAV format...")
        audio_file_path, sample_rate = mp3_to_wav(audio_file_path)
        print(f"Detected sample rate: {sample_rate} Hz")
    # Add support for .wave extension
    elif audio_file_path.endswith('.wave'):
        # Read .wave file directly using pydub to get sample rate
        audio = AudioSegment.from_file(audio_file_path, format="wav")
        sample_rate = audio.frame_rate
        print(f"Detected sample rate from .wave file: {sample_rate} Hz")
    
    # Check audio duration
    audio = AudioSegment.from_file(audio_file_path)
    duration_ms = len(audio)
    
    # If audio is longer than 30 seconds, use segmented approach
    if duration_ms > 30000:
        print(f"Audio file is {duration_ms/1000:.2f} seconds long. Using segmented transcription.")
        return transcribe_large_audio(audio_file_path)
    
    # For shorter files, use the original transcription method
    # Read the audio file
    with io.open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create client with language-specific credentials
    try:
        print("Authenticating with Google Cloud...")
        # Try to use language-specific credentials first
        cantonese_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
        if cantonese_credentials:
            print(f"Using Cantonese-specific credentials from: {cantonese_credentials}")
            credentials = service_account.Credentials.from_service_account_file(cantonese_credentials)
            client = speech.SpeechClient(credentials=credentials)
        else:
            # Fall back to default credentials
            print("No language-specific credentials found, using default credentials")
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
    
    # Configure request with Chinese language code (Cantonese)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="yue-Hant-HK",  # Traditional Chinese (Cantonese)
        enable_automatic_punctuation=True,
    )
    
    # Make request
    print("Transcribing Cantonese audio...")
    response = client.recognize(config=config, audio=audio)
    
    # Process response
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    
    return transcript

def transcribe_large_audio(audio_file_path):
    """Transcribe a large audio file by splitting it into segments."""
    # Check file extension
    if audio_file_path.endswith('.mp3'):
        print("Converting MP3 to WAV format...")
        wav_file_path, _ = mp3_to_wav(audio_file_path)
        audio_file_path = wav_file_path
    
    # Split the file into 30-second segments
    segments = split_audio_file(audio_file_path)
    
    # Transcribe each segment
    full_transcript = ""
    for i, (segment_path, sample_rate) in enumerate(segments):
        print(f"\nProcessing segment {i+1}/{len(segments)}")
        segment_transcript = transcribe_audio_segment(segment_path, sample_rate)
        
        if segment_transcript:
            full_transcript += segment_transcript + " "
            print(f"Segment {i+1} transcription: {segment_transcript[:50]}...")
        else:
            print(f"Failed to transcribe segment {i+1}")
    
    # Cleanup temporary files
    print("\nCleaning up temporary files...")
    for segment_path, _ in segments:
        try:
            os.remove(segment_path)
            print(f"Deleted: {segment_path}")
        except Exception as e:
            print(f"Could not delete {segment_path}: {e}")
    
    return full_transcript

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python transcribe_audio_chinese.py <audio_file_path>")
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    
    if not os.path.exists(audio_file_path):
        print(f"Error: File '{audio_file_path}' not found.")
        sys.exit(1)
    
    transcript = transcribe_audio(audio_file_path)
    
    if transcript:
        # Save transcript to file
        output_file = audio_file_path.replace('.mp3', '.txt').replace('.wav', '.txt').replace('.wave', '.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        print(f"Transcription complete. Output saved to {output_file}")
        print("\nTranscript:")
        print(transcript)
    else:
        print("Transcription failed. Please check your credentials and try again.")