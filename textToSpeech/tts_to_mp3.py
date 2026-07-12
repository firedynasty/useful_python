"""
Convert text to MP3 using Kokoro TTS.

Usage:
    # From clipboard
    python tts_to_mp3.py

    # From argument
    python tts_to_mp3.py "Hello world"

    # Custom output path
    python tts_to_mp3.py -o /path/to/output.mp3

    # Custom voice/speed
    python tts_to_mp3.py --voice af_bella --speed 1.2
"""

import argparse
import asyncio
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

VOICE = "am_michael"
SPEED = 1.0

_dir = os.path.dirname(os.path.abspath(__file__))


def sanitize_filename(text, max_len=40):
    """Create a filename-safe string from the first words of text."""
    # Take first ~max_len chars, break at word boundary
    snippet = text[:max_len].strip()
    # Break at last space if we truncated mid-word
    if len(text) > max_len:
        last_space = snippet.rfind(" ")
        if last_space > 10:
            snippet = snippet[:last_space]
    # Replace non-alphanumeric with underscores, collapse multiples
    snippet = re.sub(r"[^a-zA-Z0-9]+", "_", snippet)
    snippet = snippet.strip("_").lower()
    return snippet or "tts_output"


def main():
    parser = argparse.ArgumentParser(description="Text to MP3 via Kokoro TTS")
    parser.add_argument("text", nargs="?", help="Text to speak (default: clipboard)")
    parser.add_argument("-o", "--output", help="Output MP3 path (default: ~/Downloads/<text-snippet>.mp3)")
    parser.add_argument("--voice", default=VOICE, help=f"Kokoro voice (default: {VOICE})")
    parser.add_argument("--speed", type=float, default=SPEED, help=f"Speech speed (default: {SPEED})")
    args = parser.parse_args()

    # Get text
    if args.text:
        text = args.text.strip()
    else:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        text = result.stdout.strip()

    if not text:
        print("Error: No text provided and clipboard is empty.")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        snippet = sanitize_filename(text)
        output_path = os.path.expanduser(f"~/Downloads/{snippet}.mp3")

    # Auto-increment if file exists
    if os.path.exists(output_path):
        base, ext = os.path.splitext(output_path)
        n = 1
        while os.path.exists(f"{base}_{n}{ext}"):
            n += 1
        output_path = f"{base}_{n}{ext}"

    print(f"Generating {len(text)} chars with voice={args.voice} speed={args.speed}...")

    # Load Kokoro and generate
    kokoro = Kokoro(
        os.path.join(_dir, "kokoro-v1.0.onnx"),
        os.path.join(_dir, "voices-v1.0.bin"),
    )

    stream = kokoro.create_stream(text, voice=args.voice, speed=args.speed, lang="en-us")

    # Collect all audio chunks
    all_samples = []
    sample_rate = None

    async def generate():
        nonlocal sample_rate
        async for samples, sr in stream:
            all_samples.append(samples)
            sample_rate = sr

    asyncio.run(generate())

    if not all_samples:
        print("Error: No audio generated.")
        sys.exit(1)

    # Concatenate and save
    audio = np.concatenate(all_samples)

    # Write WAV to temp, convert to MP3 with ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_wav = tmp.name
        sf.write(tmp_wav, audio, sample_rate)

    try:
        subprocess.run(
            ["/opt/homebrew/bin/ffmpeg", "-y", "-i", tmp_wav, "-b:a", "192k", output_path],
            capture_output=True,
            check=True,
        )
    finally:
        os.unlink(tmp_wav)

    print(f"Saved:\nopen {output_path}")


if __name__ == "__main__":
    main()
