"""
Teacher–Student dialogue narration using ElevenLabs.

Parses markdown with **STUDENT:** / **TEACHER:** speaker labels:
  - **STUDENT:** lines  → woman voice (Bella)
  - **TEACHER:** lines  → man voice (Arnold)
  - # / ## headings     → narrator voice (Adam), spoken aloud
  - > blockquotes       → scripture voice (Antoni), e.g. closing prayers
  - Plain paragraphs    → narrator voice

Usage:
    pip install elevenlabs pydub
    brew install ffmpeg

    export ELEVENLABS_API_KEY="your-api-key"

    # From file
    python narrator_teacher_student.py speakthis.md
    python narrator_teacher_student.py speakthis.md -o lesson.mp3

    # From clipboard
    python narrator_teacher_student.py -c

    # Preview segments without generating audio
    python narrator_teacher_student.py speakthis.md --dry-run
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from elevenlabs import ElevenLabs
from pydub import AudioSegment


# --- Configuration ---

API_KEY = os.environ.get("ELEVENLABS_API_KEY")

VOICES = {
    "narrator":  "pNInz6obpgDQGcFmaJgB",  # Adam   — warm, steady narrator
    "student":   "EXAVITQu4vr4xnSDxMaL",  # Bella  — woman, curious student
    "teacher":   "VR6AewLTigWG4xSOukaG",  # Arnold — man, authoritative teacher
    "scripture": "ErXwobaYiN019PkySvjV",  # Antoni — deep, reverent (blockquotes)
}

MODEL_ID = "eleven_multilingual_v2"

PAUSE_BETWEEN_SEGMENTS_MS = 600
PAUSE_AFTER_HEADING_MS = 900
PAUSE_AFTER_SCRIPTURE_MS = 1200


def get_clipboard_text() -> str:
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
    """Remove markdown syntax, keep readable text."""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[🙏📖]", "", text)
    return text.strip()


# Matches: **STUDENT:** or **TEACHER:** at the start of a line (case-insensitive)
SPEAKER_RE = re.compile(r"^\*\*(STUDENT|TEACHER):\*\*\s*(.*)", re.IGNORECASE)


def parse_dialogue(text: str) -> list[tuple[str, str, int]]:
    """
    Parse markdown into (voice_key, clean_text, pause_after_ms) segments.

    Priority order per line:
      1. **STUDENT:** / **TEACHER:** speaker labels
      2. # headings → narrator
      3. > blockquotes → scripture (collected across consecutive lines)
      4. Horizontal rules / empty lines → skipped
      5. Everything else → narrator
    """
    segments = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines, horizontal rules, editorial footnotes
        if not line or re.match(r"^---+$", line):
            i += 1
            continue

        # Skip editorial/footnote italic-only lines at the very end
        if re.match(r"^\*[^*].*\*$", line) and line.startswith("*Editorial"):
            i += 1
            continue

        # --- STUDENT / TEACHER speaker lines ---
        m = SPEAKER_RE.match(line)
        if m:
            speaker_label = m.group(1).lower()   # "student" or "teacher"
            rest = m.group(2).strip()

            # Collect any continuation lines (wrapped text, no new speaker label)
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if (not next_line
                        or re.match(r"^---+$", next_line)
                        or re.match(r"^#{1,6}\s+", next_line)
                        or next_line.startswith(">")
                        or SPEAKER_RE.match(next_line)):
                    break
                rest += " " + next_line
                i += 1

            clean = strip_markdown(rest)
            if clean:
                segments.append((speaker_label, clean, PAUSE_BETWEEN_SEGMENTS_MS))
            continue

        # --- Headings → narrator ---
        if re.match(r"^#{1,6}\s+", line):
            clean = strip_markdown(line)
            if clean:
                segments.append(("narrator", clean, PAUSE_AFTER_HEADING_MS))
            i += 1
            continue

        # --- Blockquotes → scripture (multi-line) ---
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

        # --- Plain paragraphs → narrator ---
        para_lines = []
        while i < len(lines):
            l = lines[i].strip()
            if (not l
                    or re.match(r"^---+$", l)
                    or re.match(r"^#{1,6}\s+", l)
                    or l.startswith(">")
                    or SPEAKER_RE.match(l)):
                break
            para_lines.append(l)
            i += 1

        if para_lines:
            clean = strip_markdown(" ".join(para_lines))
            if clean:
                segments.append(("narrator", clean, PAUSE_BETWEEN_SEGMENTS_MS))

    return segments


MAX_CHUNK_CHARS = 9000


def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            words = sentence.split()
            for word in words:
                if len(current) + len(word) + 1 > max_chars:
                    chunks.append(current.strip())
                    current = word
                else:
                    current = (current + " " + word).strip()
            continue
        if len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip()
    if current:
        chunks.append(current.strip())
    return chunks


def _generate_chunk(client: ElevenLabs, voice_id: str, text: str) -> AudioSegment:
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


def generate_audio(client: ElevenLabs, voice_id: str, text: str) -> AudioSegment:
    chunks = _chunk_text(text)
    if len(chunks) == 1:
        return _generate_chunk(client, voice_id, chunks[0])
    combined = AudioSegment.empty()
    for chunk in chunks:
        combined += _generate_chunk(client, voice_id, chunk)
    return combined


def main():
    parser = argparse.ArgumentParser(
        description="Narrate teacher–student dialogue with ElevenLabs voices"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-c", "--clipboard", action="store_true", help="Read from clipboard")
    source.add_argument("file", nargs="?", help="Path to .md or .txt file")
    parser.add_argument("-o", "--output", default="dialogue_output.mp3",
                        help="Output filename (default: dialogue_output.mp3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show parsed segments without generating audio")
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

    segments = parse_dialogue(text)

    if not segments:
        print("Error: No speakable content found")
        sys.exit(1)

    print(f"\nParsed {len(segments)} segments:\n")
    for voice, content, _ in segments:
        label = f"[{voice:>9}]"
        preview = content[:80] + ("..." if len(content) > 80 else "")
        print(f"  {label}  {preview}")

    if args.dry_run:
        print("\n(dry run — no audio generated)")
        return

    print(f"\nGenerating audio...\n")
    client = ElevenLabs(api_key=API_KEY)
    combined = AudioSegment.empty()
    transcript = []  # [{start_ms, end_ms, voice, text}]

    for i, (voice, content, pause_ms) in enumerate(segments, 1):
        voice_id = VOICES[voice]
        print(f"  [{i}/{len(segments)}] {voice}: {content[:60]}...")

        # Add inter-segment pause before this segment (except the first)
        if len(combined) > 0:
            combined += AudioSegment.silent(duration=pause_ms)

        start_ms = len(combined)
        segment = generate_audio(client, voice_id, content)
        combined += segment
        end_ms = len(combined)

        transcript.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "voice": voice,
            "text": content,
        })

    # Auto-increment filename if it already exists
    base_path = Path(__file__).parent / args.output
    stem, suffix = base_path.stem, base_path.suffix
    output_path = base_path
    counter = 1
    while output_path.exists():
        output_path = base_path.parent / f"{stem}_{counter}{suffix}"
        counter += 1

    combined.export(output_path, format="mp3")

    # Save transcript sidecar JSON alongside the MP3
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"audio_file": output_path.name, "segments": transcript}, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Saved to: {output_path}")
    print(f"Transcript:     {json_path}")
    print(f"Duration: {len(combined) / 1000:.1f} seconds")


if __name__ == "__main__":
    main()
