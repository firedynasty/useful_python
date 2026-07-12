"""
Multi-speaker dialogue generation using ElevenLabs API.
Generates audio for each line of dialogue with different voices,
then stitches them into a single output file.

Usage:
    pip install elevenlabs pydub
    # Also need ffmpeg installed: brew install ffmpeg

    export ELEVENLABS_API_KEY="your-api-key"
    python multi_speaker.py
"""

import os
import sys
from pathlib import Path
from elevenlabs import ElevenLabs
from pydub import AudioSegment
import io


# --- Configuration ---

API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not API_KEY:
    print("Error: Set ELEVENLABS_API_KEY environment variable")
    print("  export ELEVENLABS_API_KEY='your-key-here'")
    sys.exit(1)

# ElevenLabs pre-made voice IDs (free to use)
# Browse more at: https://elevenlabs.io/voice-library
VOICES = {
    "narrator": "pNInz6obpgDQGcFmaJgB",   # Adam - deep, authoritative
    "man":      "VR6AewLTigWG4xSOukaG",   # Arnold - strong male
    "woman":    "EXAVITQu4vr4xnSDxMaL",   # Bella - warm female
}

MODEL_ID = "eleven_multilingual_v2"  # Best for natural speech

PAUSE_BETWEEN_LINES_MS = 600  # Pause between dialogue lines
OUTPUT_FILE = "dialogue_output.mp3"


# --- Dialogue Script ---
# Each entry: (speaker_key, text)

SCRIPT = [
    ("narrator", "In the city of Philippi, at midnight, Paul and Silas were praying and singing hymns to God."),
    ("man",      "Sirs, what must I do to be saved?"),
    ("narrator", "Paul looked at the jailer and spoke with conviction."),
    ("man",      "Believe in the Lord Jesus, and you will be saved, you and your household."),
    ("woman",    "Come into our home. Let us wash your wounds and prepare a meal for you."),
    ("narrator", "And the jailer brought them into his house, and he and his entire family were baptized that very hour."),
]


def generate_line(client: ElevenLabs, voice_id: str, text: str, speaker: str) -> AudioSegment:
    """Generate audio for a single line of dialogue."""
    print(f"  Generating: [{speaker}] {text[:60]}...")

    audio_iter = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.4,
        },
    )

    # Collect the streamed bytes
    audio_bytes = b"".join(audio_iter)
    return AudioSegment.from_mp3(io.BytesIO(audio_bytes))


def main():
    client = ElevenLabs(api_key=API_KEY)

    print(f"Generating {len(SCRIPT)} lines of dialogue...\n")

    # Generate each line and stitch together
    pause = AudioSegment.silent(duration=PAUSE_BETWEEN_LINES_MS)
    combined = AudioSegment.empty()

    for speaker, text in SCRIPT:
        voice_id = VOICES[speaker]
        segment = generate_line(client, voice_id, text, speaker)
        if len(combined) > 0:
            combined += pause
        combined += segment

    # Export final audio
    output_path = Path(__file__).parent / OUTPUT_FILE
    combined.export(output_path, format="mp3")
    print(f"\nDone! Output saved to: {output_path}")
    print(f"Duration: {len(combined) / 1000:.1f} seconds")


if __name__ == "__main__":
    main()
