"""
Teacher–Student dialogue narration using local Kokoro TTS (no API key needed).

Same markdown parsing as narrator_teacher_student.py but uses kokoro_onnx
instead of ElevenLabs — completely free, runs offline.

Voice mapping:
  - narrator  → am_michael  (American male, steady)
  - student   → af_bella    (American female, curious)
  - teacher   → bm_george   (British male, authoritative)
  - scripture → bf_emma     (British female, reverent)

Other voices to try: am_adam, af_nicole, af_sarah, bm_lewis, bf_isabella

Usage:
    pip install kokoro-onnx sounddevice pydub numpy
    brew install ffmpeg

    python narrator_teacher_student_kokoro.py speakthis.md
    python narrator_teacher_student_kokoro.py speakthis.md -o lesson.mp3
    python narrator_teacher_student_kokoro.py -c
    python narrator_teacher_student_kokoro.py speakthis.md --dry-run
"""

import argparse
import asyncio
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro
from pydub import AudioSegment


# --- Configuration ---

_DIR = Path(__file__).parent
KOKORO_MODEL = _DIR / "kokoro-v1.0.onnx"
VOICES_BIN   = _DIR / "voices-v1.0.bin"

VOICES = {
    "narrator":  "am_michael",  # American male, warm and steady
    "student":   "af_bella",    # American female, curious
    "teacher":   "bm_george",   # British male, authoritative
    "scripture": "bf_emma",     # British female, reverent
}

SPEED = 1.0

PAUSE_BETWEEN_SEGMENTS_MS = 600
PAUSE_AFTER_HEADING_MS    = 900
PAUSE_AFTER_SCRIPTURE_MS  = 1200


# --- Clipboard ---

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


# --- Markdown parsing (same logic as narrator_teacher_student.py) ---

def strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[🙏📖]", "", text)
    return text.strip()


SPEAKER_RE = re.compile(r"^\*\*(STUDENT|TEACHER):\*\*\s*(.*)", re.IGNORECASE)


def parse_dialogue(text: str) -> list[tuple[str, str, int]]:
    """Parse markdown into (voice_key, clean_text, pause_after_ms) segments."""
    segments = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line or re.match(r"^---+$", line):
            i += 1
            continue

        if re.match(r"^\*[^*].*\*$", line) and line.startswith("*Editorial"):
            i += 1
            continue

        # STUDENT / TEACHER speaker lines
        m = SPEAKER_RE.match(line)
        if m:
            speaker_label = m.group(1).lower()
            rest = m.group(2).strip()
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

        # Headings → narrator
        if re.match(r"^#{1,6}\s+", line):
            clean = strip_markdown(line)
            if clean:
                segments.append(("narrator", clean, PAUSE_AFTER_HEADING_MS))
            i += 1
            continue

        # Blockquotes → scripture
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

        # Plain paragraphs → narrator
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


# --- Kokoro audio generation ---

async def _stream_to_segment(kokoro: Kokoro, voice: str, text: str) -> AudioSegment:
    """Run Kokoro stream and collect all chunks into a pydub AudioSegment."""
    all_samples = []
    sample_rate = 24000  # Kokoro default

    stream = kokoro.create_stream(text, voice=voice, speed=SPEED, lang="en-us")
    async for samples, sr in stream:
        all_samples.append(samples)
        sample_rate = sr

    if not all_samples:
        return AudioSegment.silent(duration=100)

    combined_np = np.concatenate(all_samples)
    # Float32 [-1, 1] → int16
    int16_data = (np.clip(combined_np, -1.0, 1.0) * 32767).astype(np.int16)
    return AudioSegment(
        int16_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,  # int16 = 2 bytes
        channels=1,
    )


def generate_audio(kokoro: Kokoro, voice: str, text: str) -> AudioSegment:
    return asyncio.run(_stream_to_segment(kokoro, voice, text))


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Narrate teacher–student dialogue with local Kokoro voices"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-c", "--clipboard", action="store_true", help="Read from clipboard")
    source.add_argument("file", nargs="?", help="Path to .md or .txt file")
    parser.add_argument("-o", "--output", default="dialogue_output.mp3",
                        help="Output filename (default: dialogue_output.mp3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show parsed segments without generating audio")
    parser.add_argument("--speed", type=float, default=SPEED,
                        help=f"Speaking speed multiplier (default: {SPEED})")
    args = parser.parse_args()

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

    if not KOKORO_MODEL.exists() or not VOICES_BIN.exists():
        print(f"Error: Kokoro model files not found in {_DIR}")
        print(f"  Expected: {KOKORO_MODEL.name}, {VOICES_BIN.name}")
        sys.exit(1)

    print(f"\nLoading Kokoro model...")
    kokoro = Kokoro(str(KOKORO_MODEL), str(VOICES_BIN))

    # Resolve output path
    base_path = _DIR / args.output
    stem, suffix = base_path.stem, base_path.suffix
    output_path = base_path
    counter = 1
    while output_path.exists():
        output_path = base_path.parent / f"{stem}_{counter}{suffix}"
        counter += 1

    print(f"\nGenerating audio...\n")
    combined = AudioSegment.empty()
    transcript = []

    for i, (voice, content, pause_ms) in enumerate(segments, 1):
        kokoro_voice = VOICES[voice]
        print(f"  [{i}/{len(segments)}] {voice} ({kokoro_voice}): {content[:60]}...")

        if len(combined) > 0:
            combined += AudioSegment.silent(duration=pause_ms)

        start_ms = len(combined)
        segment = generate_audio(kokoro, kokoro_voice, content)
        combined += segment
        end_ms = len(combined)

        transcript.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "voice": voice,
            "text": content,
        })

    combined.export(output_path, format="mp3")

    json_path = output_path.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"audio_file": output_path.name, "segments": transcript}, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Saved to: {output_path}")
    print(f"Transcript:     {json_path}")
    print(f"Duration: {len(combined) / 1000:.1f} seconds")


if __name__ == "__main__":
    main()
