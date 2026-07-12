"""
Narrate markdown/text content with multiple voices using ElevenLabs.

Parses markdown structure to assign voices:
  - Scripture quotes (> blockquotes) → scripture voice (deep, reverent)
  - Bold quoted speech (**"..."**) → speaker voice (dramatic)
  - Italic emphasis (*...*) → emphasis voice (reflective)
  - Everything else → narrator voice

Usage:
    pip install elevenlabs pydub pyperclip
    brew install ffmpeg

    export ELEVENLABS_API_KEY="your-api-key"

    # From clipboard
    python narrator.py -c

    # From a text/markdown file
    python narrator.py sermon.txt
    python narrator.py notes.md

    # Specify output filename
    python narrator.py -c -o my_narration.mp3
"""

import argparse
import io
import os
import re
import subprocess
import sys
from pathlib import Path

from elevenlabs import ElevenLabs
from pydub import AudioSegment


# --- Configuration ---

API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Voice assignments — swap these IDs for any voice from elevenlabs.io/voice-library
VOICES = {
    "narrator":  "pNInz6obpgDQGcFmaJgB",  # Adam — warm, steady narrator
    "scripture": "ErXwobaYiN019PkySvjV",  # Antoni — deep, reverent
    "speaker":   "VR6AewLTigWG4xSOukaG",  # Arnold — dramatic, authoritative
    "emphasis":  "EXAVITQu4vr4xnSDxMaL",  # Bella — reflective, gentle
}

MODEL_ID = "eleven_multilingual_v2"

PAUSE_BETWEEN_SEGMENTS_MS = 500
PAUSE_AFTER_HEADING_MS = 800
PAUSE_AFTER_SCRIPTURE_MS = 1000


def get_clipboard_text() -> str:
    """Get text from macOS clipboard."""
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: Could not read clipboard")
        sys.exit(1)
    text = result.stdout.strip()
    if not text:
        print("Error: Clipboard is empty")
        sys.exit(1)
    return text


def strip_markdown(text: str) -> str:
    """Remove markdown formatting but keep the readable text."""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # headings
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)            # bold+italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)                 # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)                     # italic
    text = re.sub(r"_(.+?)_", r"\1", text)                       # underscore italic
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)        # blockquote markers
    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)    # horizontal rules
    text = re.sub(r"[🙏📖]", "", text)                            # emoji
    text = re.sub(r"^— \*.*?\*\s*$", "", text, flags=re.MULTILINE)  # attribution lines like "— *Deut 29:4*"
    return text.strip()


def parse_markdown(text: str) -> list[tuple[str, str, int]]:
    """
    Parse markdown into segments: (voice_key, clean_text, pause_after_ms).

    Rules:
      - Lines starting with # → narrator (heading), longer pause after
      - Lines starting with > → scripture voice
      - Lines with **"quoted speech"** → speaker voice
      - Lines with ***bold italic*** → emphasis voice
      - Horizontal rules (---) → extra pause, no speech
      - Everything else → narrator
    """
    segments = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and horizontal rules
        if not line or re.match(r"^---+$", line):
            i += 1
            continue

        # Skip "Want to continue..." prompts at the end
        if line.startswith("Want to continue"):
            i += 1
            continue

        # Headings → narrator with heading pause
        if re.match(r"^#{1,6}\s+", line):
            clean = strip_markdown(line)
            if clean:
                segments.append(("narrator", clean, PAUSE_AFTER_HEADING_MS))
            i += 1
            continue

        # Blockquotes → scripture voice (collect multi-line quotes)
        if line.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                content = re.sub(r"^>\s*", "", lines[i].strip())
                if content and not re.match(r"^— \*.*\*$", content):
                    quote_lines.append(content)
                i += 1
            if quote_lines:
                clean = strip_markdown(" ".join(quote_lines))
                if clean:
                    segments.append(("scripture", clean, PAUSE_AFTER_SCRIPTURE_MS))
            continue

        # Bold quoted speech **"..."** → speaker voice
        if re.search(r'\*\*"[^"]+"\*\*', line) or re.search(r'\*\*"[^"]+"\*\*', line):
            clean = strip_markdown(line)
            if clean:
                segments.append(("speaker", clean, PAUSE_BETWEEN_SEGMENTS_MS))
            i += 1
            continue

        # Bold italic ***text*** → emphasis
        if re.search(r"\*\*\*.+?\*\*\*", line):
            clean = strip_markdown(line)
            if clean:
                segments.append(("emphasis", clean, PAUSE_BETWEEN_SEGMENTS_MS))
            i += 1
            continue

        # Collect consecutive plain paragraph lines
        para_lines = []
        while i < len(lines):
            l = lines[i].strip()
            if not l or re.match(r"^---+$", l) or re.match(r"^#{1,6}\s+", l) or l.startswith(">"):
                break
            para_lines.append(l)
            i += 1

        if para_lines:
            full = " ".join(para_lines)

            # Check if the paragraph is mostly italic (*...*) → emphasis
            if re.match(r"^\*[^*]+\*$", full.strip()):
                clean = strip_markdown(full)
                if clean:
                    segments.append(("emphasis", clean, PAUSE_BETWEEN_SEGMENTS_MS))
            # Check for bold quoted speech within paragraph
            elif re.search(r'\*\*"[^"]+"\*\*', full):
                clean = strip_markdown(full)
                if clean:
                    segments.append(("speaker", clean, PAUSE_BETWEEN_SEGMENTS_MS))
            else:
                clean = strip_markdown(full)
                if clean:
                    segments.append(("narrator", clean, PAUSE_BETWEEN_SEGMENTS_MS))

    return segments


def generate_audio(client: ElevenLabs, voice_id: str, text: str) -> AudioSegment:
    """Generate audio for a single text segment."""
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
    audio_bytes = b"".join(audio_iter)
    return AudioSegment.from_mp3(io.BytesIO(audio_bytes))


def main():
    parser = argparse.ArgumentParser(
        description="Narrate text/markdown with multiple ElevenLabs voices"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-c", "--clipboard", action="store_true", help="Read from clipboard")
    source.add_argument("file", nargs="?", help="Path to .txt or .md file")
    parser.add_argument("-o", "--output", default="narration_output.mp3", help="Output filename (default: narration_output.mp3)")
    parser.add_argument("--dry-run", action="store_true", help="Parse and show segments without generating audio")
    args = parser.parse_args()

    if not API_KEY and not args.dry_run:
        print("Error: Set ELEVENLABS_API_KEY environment variable")
        print("  export ELEVENLABS_API_KEY='your-key-here'")
        sys.exit(1)

    # Read input
    if args.clipboard:
        print("Reading from clipboard...")
        text = get_clipboard_text()
    else:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)
        print(f"Reading from {filepath}...")
        text = filepath.read_text(encoding="utf-8")

    # Parse into voice segments
    segments = parse_markdown(text)

    if not segments:
        print("Error: No speakable content found")
        sys.exit(1)

    print(f"\nParsed {len(segments)} segments:\n")
    for voice, content, _ in segments:
        label = f"[{voice:>10}]"
        preview = content[:80] + ("..." if len(content) > 80 else "")
        print(f"  {label}  {preview}")

    if args.dry_run:
        print("\n(dry run — no audio generated)")
        return

    # Generate audio
    print(f"\nGenerating audio...\n")
    client = ElevenLabs(api_key=API_KEY)
    combined = AudioSegment.empty()

    for i, (voice, content, pause_ms) in enumerate(segments, 1):
        voice_id = VOICES[voice]
        print(f"  [{i}/{len(segments)}] {voice}: {content[:50]}...")
        segment = generate_audio(client, voice_id, content)
        if len(combined) > 0:
            combined += AudioSegment.silent(duration=pause_ms)
        combined += segment

    # Export — auto-increment filename if it already exists
    base_path = Path(__file__).parent / args.output
    stem = base_path.stem
    suffix = base_path.suffix
    output_path = base_path
    counter = 1
    while output_path.exists():
        output_path = base_path.parent / f"{stem}_{counter}{suffix}"
        counter += 1
    combined.export(output_path, format="mp3")
    print(f"\nDone! Saved to: {output_path}")
    print(f"Duration: {len(combined) / 1000:.1f} seconds")


if __name__ == "__main__":
    main()
