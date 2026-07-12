"""
Vocabulary teacher recitation using ElevenLabs TTS.

Reads vocabulary from CSV, markdown, or dash-delimited text and generates
audio that sounds like a teacher reciting vocabulary to a class:
  "Address bus... connects the CPU to the MCC and sends over the location
   of the data, but not the data itself."

Supported input formats (auto-detected):
  - CSV:      term,"definition with commas"
  - Markdown: - **Term** — definition text here
              Headings (##, **bold lines**) become spoken section breaks
              from Claude notes if I am asking.. 
              prompt is
              "what are some vocab words I should know based on this so I can form a mental model to be able to explain to someone else what engineering is"
  - Dashes:   Term -- definition text here

Cadence is controlled by:
  - Inserting pauses (commas, ellipses) between term and definition
  - A configurable silence gap between each vocabulary entry
  - Longer silence after section headers
  - Voice settings: lower stability for more expressive/teacher-like delivery

Usage:
    pip install elevenlabs pydub
    brew install ffmpeg

    export ELEVENLABS_API_KEY="your-api-key"

    # CSV input
    python vocab_teacher.py /path/to/vocabulary.csv

    # Markdown input (auto-detected)
    python vocab_teacher.py /path/to/vocab_notes.md

    # Dash-delimited text
    python vocab_teacher.py /path/to/vocab.txt

    # Custom pause between terms (default: 1200ms)
    python vocab_teacher.py vocabulary.csv --pause 1500

    # Custom output filename
    python vocab_teacher.py vocabulary.csv -o vocab_lesson.mp3

    # Read from clipboard (copy vocab from Claude chat, then run)
    python vocab_teacher.py -c
    python vocab_teacher.py -c -o engineering_vocab.mp3
"""

import argparse
import csv
import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from elevenlabs import ElevenLabs
from pydub import AudioSegment


# --- Configuration ---

API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Default voice: Adam — warm, steady, teacher-like
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"
MODEL_ID = "eleven_multilingual_v2"

# Pause between vocabulary entries (ms)
DEFAULT_PAUSE_MS = 1200
# Longer pause after section headers (ms)
SECTION_PAUSE_MS = 2000


# Entry types
ENTRY_TERM = "term"
ENTRY_HEADER = "header"


def format_term_for_speech(term, definition):
    """
    Format a term + definition into natural teacher-style speech.

    Examples:
      "BYOD (Bring Your Own Device)", "Refers to the practice of..."
      => "BYOD, or Bring Your Own Device... refers to the practice of..."

      "CPU", "Central processing unit"
      => "CPU... Central processing unit."

      "Cache", "The assigned stored location for..."
      => "Cache... the assigned stored location for..."
    """
    term = term.strip()
    definition = definition.strip()

    # Extract parenthetical expansion if present: "BYOD (Bring Your Own Device)"
    paren_match = re.match(r'^(.+?)\s*\((.+?)\)$', term)

    if paren_match:
        abbreviation = paren_match.group(1).strip()
        expansion = paren_match.group(2).strip()
        term_part = f"{abbreviation}, or {expansion}"
    else:
        term_part = term

    # Lowercase the first letter of definition if it starts with uppercase
    # (sounds more natural as a continuation), unless it's an acronym
    if definition and definition[0].isupper() and len(definition) > 1 and definition[1].islower():
        definition_speech = definition[0].lower() + definition[1:]
    else:
        definition_speech = definition

    # Ensure definition ends with a period
    if definition_speech and not definition_speech.endswith(('.', '!', '?')):
        definition_speech += '.'

    # Combine with an ellipsis pause for teacher cadence
    speech = f"{term_part}... {definition_speech}"

    return speech


def detect_format(file_path):
    """Auto-detect input format: 'csv', 'markdown', or 'dashes'."""
    suffix = file_path.suffix.lower()
    if suffix == '.csv':
        return 'csv'
    if suffix in ('.md', '.markdown'):
        return 'markdown'

    # Peek at content to decide
    with open(file_path, 'r', encoding='utf-8') as f:
        sample = f.read(2000)

    # Markdown patterns: bullet + bold term, or headings
    if re.search(r'^-\s+\*\*', sample, re.MULTILINE):
        return 'markdown'
    # Dash-delimited: "Term -- definition"
    if re.search(r'^.+\s+--\s+', sample, re.MULTILINE):
        return 'dashes'
    # Comma-separated fallback
    if ',' in sample:
        return 'csv'

    return 'dashes'


def read_csv_vocab(file_path, skip_header=True):
    """Read vocabulary CSV. Returns list of (type, term, definition) tuples."""
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if skip_header and i == 0:
                continue
            if len(row) >= 2:
                term, definition = row[0].strip(), row[1].strip()
                if term and definition:
                    entries.append((ENTRY_TERM, term, definition))
    return entries


def read_markdown_vocab(file_path):
    """
    Read markdown-formatted vocabulary. Supports:
      - ## Headings or **bold lines** as section headers
      - - **Term** — definition  (em dash)
      - - **Term** - definition  (hyphen after bold)
      - - **Term**: definition   (colon)

    Returns list of (type, text, definition_or_None) tuples.
    """
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Markdown headings: ## Header or ### Header
        heading_match = re.match(r'^#{1,6}\s+(.+)$', line)
        if heading_match:
            header_text = heading_match.group(1).strip()
            # Remove markdown formatting from header
            header_text = re.sub(r'\*+', '', header_text).strip()
            if header_text:
                entries.append((ENTRY_HEADER, header_text, None))
            continue

        # Bold-only lines as headers: **The big picture words**
        bold_line_match = re.match(r'^\*\*(.+?)\*\*\s*$', line)
        if bold_line_match:
            entries.append((ENTRY_HEADER, bold_line_match.group(1).strip(), None))
            continue

        # Bullet with bold term: - **Term** — definition
        # Supports em dash (—), double hyphen (--), single hyphen after bold (-), or colon (:)
        bullet_match = re.match(
            r'^[-*]\s+\*\*(.+?)\*\*\s*(?:—|--|-|:)\s*(.+)$', line
        )
        if bullet_match:
            term = bullet_match.group(1).strip()
            definition = bullet_match.group(2).strip()
            # Clean markdown artifacts from definition (italic markers, etc.)
            definition = re.sub(r'\*([^*]+)\*', r'\1', definition)
            entries.append((ENTRY_TERM, term, definition))
            continue

    return entries


def read_dashes_vocab(file_path):
    """Read dash-delimited vocabulary: Term -- definition. Returns entries."""
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Split on -- or —
            parts = re.split(r'\s+--\s+|\s+—\s+', line, maxsplit=1)
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                if term and definition:
                    entries.append((ENTRY_TERM, term, definition))
    return entries


def generate_speech(client, voice_id, text, index, total):
    """Generate audio for a single vocabulary entry or header."""
    display = text[:80] + "..." if len(text) > 80 else text
    print(f"  [{index}/{total}] {display}")

    audio_iter = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.4,        # Lower = more expressive/varied
            "similarity_boost": 0.75,
            "style": 0.5,            # Some style exaggeration for teacher feel
        },
    )

    audio_bytes = b"".join(audio_iter)
    return AudioSegment.from_mp3(io.BytesIO(audio_bytes))


def main():
    parser = argparse.ArgumentParser(
        description="Generate teacher-style vocabulary recitation audio"
    )
    parser.add_argument("input_file", nargs='?', default=None,
                        help="Path to vocabulary file (CSV, markdown, or dash-delimited)")
    parser.add_argument("-c", "--clipboard", action="store_true",
                        help="Read from clipboard (treated as markdown)")
    parser.add_argument("-o", "--output", default=None, help="Output MP3 filename")
    parser.add_argument("--pause", type=int, default=DEFAULT_PAUSE_MS,
                        help=f"Pause between terms in ms (default: {DEFAULT_PAUSE_MS})")
    parser.add_argument("--section-pause", type=int, default=SECTION_PAUSE_MS,
                        help=f"Pause after section headers in ms (default: {SECTION_PAUSE_MS})")
    parser.add_argument("--no-skip-header", action="store_true",
                        help="Don't skip the first row of CSV")
    parser.add_argument("--voice-id", default=DEFAULT_VOICE_ID,
                        help="ElevenLabs voice ID")
    parser.add_argument("--format", choices=['csv', 'markdown', 'dashes'],
                        default=None, help="Force input format (default: auto-detect)")
    args = parser.parse_args()

    api_key = API_KEY
    if not api_key:
        print("Error: Set ELEVENLABS_API_KEY environment variable")
        print("  export ELEVENLABS_API_KEY='your-key-here'")
        sys.exit(1)

    if not args.clipboard and not args.input_file:
        parser.error("either provide an input_file or use -c/--clipboard")

    # Read from clipboard or file
    if args.clipboard:
        clipboard_text = subprocess.run(
            ["pbpaste"], capture_output=True, text=True
        ).stdout
        if not clipboard_text.strip():
            print("Error: Clipboard is empty")
            sys.exit(1)
        print(f"Read {len(clipboard_text)} chars from clipboard")
        # Write to temp file so parsers can read it
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        tmp.write(clipboard_text)
        tmp.close()
        input_path = Path(tmp.name)
        fmt = args.format or 'markdown'
        output_path = Path(args.output) if args.output else Path("vocab_clipboard.mp3")
    else:
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            sys.exit(1)
        output_path = Path(args.output) if args.output else input_path.with_suffix('.mp3')
        fmt = args.format or detect_format(input_path)

    print(f"Detected format: {fmt}")

    if fmt == 'csv':
        entries = read_csv_vocab(input_path, skip_header=not args.no_skip_header)
    elif fmt == 'markdown':
        entries = read_markdown_vocab(input_path)
    else:
        entries = read_dashes_vocab(input_path)

    # Clean up temp file if we created one
    if args.clipboard:
        os.unlink(input_path)

    if not entries:
        print("Error: No vocabulary entries found")
        sys.exit(1)

    term_count = sum(1 for e in entries if e[0] == ENTRY_TERM)
    header_count = sum(1 for e in entries if e[0] == ENTRY_HEADER)
    print(f"Found {term_count} vocabulary terms", end="")
    if header_count:
        print(f" in {header_count} sections")
    else:
        print()
    print(f"Pause between terms: {args.pause}ms")
    if header_count:
        print(f"Pause after sections: {args.section_pause}ms")
    print(f"Output: {output_path}\n")

    # Preview
    print("Preview (first entries):")
    shown = 0
    for entry_type, text, defn in entries:
        if shown >= 5:
            break
        if entry_type == ENTRY_HEADER:
            print(f"  [section] \"{text}\"")
        else:
            print(f"  -> {format_term_for_speech(text, defn)}")
        shown += 1
    print()

    # Generate audio
    client = ElevenLabs(api_key=api_key)
    pause = AudioSegment.silent(duration=args.pause)
    section_pause = AudioSegment.silent(duration=args.section_pause)
    combined = AudioSegment.empty()

    total = len(entries)
    for i, (entry_type, text, defn) in enumerate(entries, 1):
        if entry_type == ENTRY_HEADER:
            speech_text = text
            segment = generate_speech(client, args.voice_id, speech_text, i, total)
            if len(combined) > 0:
                combined += section_pause
            combined += segment
            combined += section_pause
        else:
            speech_text = format_term_for_speech(text, defn)
            segment = generate_speech(client, args.voice_id, speech_text, i, total)
            if len(combined) > 0:
                combined += pause
            combined += segment

    # Export
    combined.export(output_path, format="mp3")
    print(f"\nDone! Output saved to: {output_path}")
    print(f"Duration: {len(combined) / 1000:.1f} seconds")
    print(f"Terms covered: {term_count}")
    if header_count:
        print(f"Sections: {header_count}")


if __name__ == "__main__":
    main()
