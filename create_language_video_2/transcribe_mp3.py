#!/usr/bin/env python3
"""
transcribe_mp3.py

Transcribe an MP3 file using OpenAI Whisper API.
Automatically chunks files over 24MB (API limit is 25MB).

Usage:
  export OPENAI_API_KEY=sk-...

  # Transcribe (auto-detect language)
  python transcribe_mp3.py -i audio.mp3

  # Transcribe with explicit language
  python transcribe_mp3.py -i audio.mp3 --language zh

  # Translate any language to English
  python transcribe_mp3.py -i audio.mp3 --translate

  # Custom output paths
  python transcribe_mp3.py -i audio.mp3 --srt output.srt --txt output.txt

Produces:
  transcript.srt  — subtitle file with timestamps
  transcript.txt  — plain text (one line per subtitle entry)
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

from openai import OpenAI


def get_file_size_mb(filepath):
    return os.path.getsize(filepath) / (1024 * 1024)


def get_duration_ms(filepath):
    """Get audio duration in milliseconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", filepath],
        capture_output=True, text=True, check=True,
    )
    return int(float(result.stdout.strip()) * 1000)


def chunk_mp3(input_path, chunk_dir, segment_time=600):
    """Split MP3 into chunks using ffmpeg. Default 10-min segments."""
    pattern = os.path.join(chunk_dir, "segment_%03d.mp3")
    subprocess.run(
        ["ffmpeg", "-i", input_path, "-f", "segment",
         "-segment_time", str(segment_time), "-c", "copy", pattern],
        check=True, capture_output=True,
    )
    return sorted(glob.glob(os.path.join(chunk_dir, "segment_*.mp3")))


def transcribe_one(client, filepath, language=None, translate=False):
    """Send a single MP3 to the Whisper API, return SRT text."""
    with open(filepath, "rb") as f:
        if translate:
            return client.audio.translations.create(
                model="whisper-1", file=f, response_format="srt",
            )
        kwargs = {"model": "whisper-1", "file": f, "response_format": "srt"}
        if language:
            kwargs["language"] = language
        return client.audio.transcriptions.create(**kwargs)


def offset_srt(srt_text, offset_ms):
    """Shift all SRT timestamps forward by offset_ms."""
    def shift(match):
        h, m, s, ms = int(match[1]), int(match[2]), int(match[3]), int(match[4])
        total = h * 3600000 + m * 60000 + s * 1000 + ms + offset_ms
        nh = total // 3600000
        nm = (total % 3600000) // 60000
        ns = (total % 60000) // 1000
        nms = total % 1000
        return f"{nh:02d}:{nm:02d}:{ns:02d},{nms:03d}"

    return re.sub(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", shift, srt_text)


def renumber_srt(srt_text):
    """Renumber SRT entries sequentially from 1."""
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    result = []
    for i, block in enumerate(blocks, 1):
        lines = block.strip().split("\n")
        if len(lines) >= 2:
            lines[0] = str(i)
            result.append("\n".join(lines))
    return "\n\n".join(result) + "\n"


def srt_to_text(srt_text):
    """Extract plain text lines from SRT content."""
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    lines = []
    for block in blocks:
        parts = block.strip().split("\n")
        if len(parts) >= 3:
            lines.append(" ".join(parts[2:]).strip())
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Transcribe MP3 with OpenAI Whisper API")
    parser.add_argument("-i", "--input", required=True, help="Input MP3 file")
    parser.add_argument("--srt", default="transcript.srt", help="Output SRT file (default: transcript.srt)")
    parser.add_argument("--txt", default="transcript.txt", help="Output text file (default: transcript.txt)")
    parser.add_argument("--language", default=None, help="Language code, e.g. zh, en, ja, tl (omit for auto-detect)")
    parser.add_argument("--translate", action="store_true", help="Translate to English instead of transcribing")
    parser.add_argument("--segment-time", type=int, default=600, help="Chunk length in seconds (default: 600)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: set OPENAI_API_KEY environment variable")
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    size_mb = get_file_size_mb(args.input)
    print(f"File: {args.input} ({size_mb:.1f} MB)")

    # API limit is 25MB — chunk if over 24MB to be safe
    if size_mb < 24:
        print("Sending directly to Whisper API...")
        srt = transcribe_one(client, args.input, args.language, args.translate)
    else:
        print(f"Large file — splitting into {args.segment_time}s chunks...")
        with tempfile.TemporaryDirectory() as chunk_dir:
            chunks = chunk_mp3(args.input, chunk_dir, args.segment_time)
            print(f"Created {len(chunks)} chunks")

            all_srt = ""
            offset_ms = 0

            for idx, chunk in enumerate(chunks):
                print(f"  Transcribing chunk {idx + 1}/{len(chunks)}...")
                chunk_srt = transcribe_one(client, chunk, args.language, args.translate)

                if offset_ms > 0:
                    chunk_srt = offset_srt(chunk_srt, offset_ms)

                all_srt += chunk_srt + "\n\n"
                offset_ms += get_duration_ms(chunk)

            srt = renumber_srt(all_srt)

    # Write SRT
    with open(args.srt, "w", encoding="utf-8") as f:
        f.write(srt)
    print(f"Wrote: {args.srt}")

    # Write plain text
    txt = srt_to_text(srt)
    with open(args.txt, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"Wrote: {args.txt}")

    print("\nDone!")


if __name__ == "__main__":
    main()
