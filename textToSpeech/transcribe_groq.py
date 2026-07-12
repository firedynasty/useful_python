"""
Transcribe an MP3 with Groq's Whisper API.

Setup:
    pip install groq
    # ffmpeg must be installed (brew install ffmpeg)
    export GROQ_API_KEY="your_key_here"   # get one at https://console.groq.com/keys

Usage:
    python transcribe_groq.py path/to/audio.mp3
    python transcribe_groq.py path/to/audio.mp3 --timestamps
"""

import os
import sys
import subprocess
import tempfile
from groq import Groq

# Groq has an upload size cap (~25 MB free tier). We re-encode to 16 kHz mono
# at a low bitrate, which is all Whisper needs and shrinks the file a lot.
MAX_BYTES = 24 * 1024 * 1024  # stay just under 25 MB


def compress(src: str) -> str:
    """Re-encode to 16 kHz mono MP3 so big files fit under the size cap."""
    out = tempfile.mktemp(suffix=".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", "-b:a", "32k", out],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


def fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def transcribe(path: str, timestamps: bool = False) -> str:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    upload_path = path
    if os.path.getsize(path) > MAX_BYTES:
        print("File is large — compressing for upload...")
        upload_path = compress(path)

    with open(upload_path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(os.path.basename(upload_path), f.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json" if timestamps else "text",
        )

    if not timestamps:
        return result if isinstance(result, str) else result.text

    lines = []
    for seg in result.segments:
        ts = fmt_time(seg["start"])
        lines.append(f"[{ts}] {seg['text'].strip()}")
    return "\n".join(lines)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    timestamps = "--timestamps" in flags

    if len(args) != 1:
        sys.exit("Usage: python transcribe_groq.py path/to/audio.mp3 [--timestamps]")

    audio = args[0]
    text = transcribe(audio, timestamps=timestamps)

    out_file = os.path.splitext(audio)[0] + ".txt"
    with open(out_file, "w") as f:
        f.write(text)

    print(f"\nDone. Transcript saved to: {out_file}\n")
    print(text[:500] + ("..." if len(text) > 500 else ""))


if __name__ == "__main__":
    main()
