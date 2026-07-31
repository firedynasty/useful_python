"""
Chinese/English mixed dialogue TTS using ElevenLabs.
Uses eleven_multilingual_v2 which handles Chinese + English in the same utterance.

Parses dialogue in the format:
    小红: 诶，你看到隔壁小王了吗？
     She lost 20 pounds in one month!!!

    小西: 嗯 我看到她了，真的很厉害！

Each speaker gets a consistent voice. Speaker names are auto-detected from
lines starting with Chinese characters followed by a colon.

Usage:
    export ELEVENLABS_API_KEY="your-key"

    # From clipboard (copy dialogue text first)
    python chinese_dialogue.py -c

    # From a .txt or .md file
    python chinese_dialogue.py dialogue.txt

    # Specify output file
    python chinese_dialogue.py -c -o my_dialogue.mp3

    # Choose what to speak: chinese, english, or both (default: both)
    python chinese_dialogue.py -c --lang chinese
    python chinese_dialogue.py -c --lang english
    python chinese_dialogue.py -c --lang both
"""

import os
import sys
import re
import io
import argparse
from pathlib import Path
from elevenlabs import ElevenLabs
from pydub import AudioSegment


# --- Config ---

API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not API_KEY:
    print("Error: Set ELEVENLABS_API_KEY environment variable")
    print("  export ELEVENLABS_API_KEY='your-key-here'")
    sys.exit(1)

MODEL_ID = "eleven_multilingual_v2"

# Voice pool — assign round-robin to new speakers as they appear
# ElevenLabs pre-made voices (free tier)
VOICE_POOL = [
    "EXAVITQu4vr4xnSDxMaL",  # Bella — warm female
    "21m00Tcm4TlvDq8ikWAM",  # Rachel — calm female
    "VR6AewLTigWG4xSOukaG",  # Arnold — strong male
    "pNInz6obpgDQGcFmaJgB",  # Adam — deep male
]

PAUSE_MS = 700          # silence between turns
OUTPUT_FILE = "chinese_dialogue_output.mp3"


# --- Dialogue parser ---

# Matches a speaker prefix like "小红:" or "Xiao Hong:" at the start of a segment
SPEAKER_RE = re.compile(r'^([\u4e00-\u9fffA-Za-z]+[\u4e00-\u9fff\w]*)\s*[:：]\s*', re.UNICODE)


def is_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def is_english(text: str) -> bool:
    return bool(re.search(r'[A-Za-z]', text))


def parse_dialogue(raw: str) -> list[tuple[str, str]]:
    """
    Returns a list of (speaker, text) tuples.
    Consecutive lines belonging to the same speaker turn are merged.
    Pinyin-style speaker tags embedded mid-line (e.g. "...厉害！Xiao Xi: Yeah")
    are split into separate turns.
    """
    turns = []
    current_speaker = None
    current_lines = []

    def flush():
        if current_speaker and current_lines:
            turns.append((current_speaker, " ".join(current_lines).strip()))

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # A line may contain an embedded "SpeakerName: text" mid-way
        # (common when Chinese + English translation share one line with a tag)
        # Split on any speaker tag
        segments = re.split(r'(?<=[^\s])\s+(?=[A-Za-z\u4e00-\u9fff]+\s*[:：])', line)

        for seg in segments:
            m = SPEAKER_RE.match(seg)
            if m:
                flush()
                current_lines = []
                current_speaker = m.group(1)
                rest = seg[m.end():].strip()
                if rest:
                    current_lines.append(rest)
            else:
                if current_speaker is None:
                    current_speaker = "narrator"
                current_lines.append(seg)

    flush()
    return turns


def filter_text(text: str, lang: str) -> str:
    """Return only the requested language portion of text."""
    if lang == "both":
        return text

    parts = []
    for sentence in re.split(r'(?<=[。！？.!?])\s*', text):
        s = sentence.strip()
        if not s:
            continue
        if lang == "chinese" and is_chinese(s):
            parts.append(s)
        elif lang == "english" and is_english(s) and not is_chinese(s):
            parts.append(s)

    return " ".join(parts) if parts else text  # fallback to full text if nothing matched


def generate_segment(client: ElevenLabs, voice_id: str, text: str, speaker: str) -> AudioSegment:
    print(f"  [{speaker}] {text[:80]}{'...' if len(text) > 80 else ''}")
    audio_iter = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.35,
        },
    )
    audio_bytes = b"".join(audio_iter)
    return AudioSegment.from_mp3(io.BytesIO(audio_bytes))


def main():
    parser = argparse.ArgumentParser(description="Chinese/English dialogue TTS via ElevenLabs")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("-c", "--clipboard", action="store_true", help="Read dialogue from clipboard")
    src.add_argument("file", nargs="?", help="Path to dialogue text file")
    parser.add_argument("-o", "--output", default=OUTPUT_FILE, help="Output mp3 path")
    parser.add_argument(
        "--lang",
        choices=["chinese", "english", "both"],
        default="both",
        help="Which language portions to speak (default: both)",
    )
    args = parser.parse_args()

    if args.clipboard:
        import pyperclip
        raw = pyperclip.paste().strip()
        if not raw:
            print("Clipboard is empty.")
            sys.exit(1)
        print(f"Read {len(raw)} chars from clipboard.")
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"File not found: {path}")
            sys.exit(1)
        raw = path.read_text(encoding="utf-8")
        print(f"Read {len(raw)} chars from {path}.")

    turns = parse_dialogue(raw)
    if not turns:
        print("No dialogue turns found. Check your input format.")
        sys.exit(1)

    print(f"\nParsed {len(turns)} turns:")
    speakers_seen = []
    speaker_voices: dict[str, str] = {}
    for spk, txt in turns:
        if spk not in speaker_voices:
            voice = VOICE_POOL[len(speaker_voices) % len(VOICE_POOL)]
            speaker_voices[spk] = voice
            print(f"  → {spk} assigned voice #{len(speaker_voices)}")
    print()

    client = ElevenLabs(api_key=API_KEY)
    pause = AudioSegment.silent(duration=PAUSE_MS)
    combined = AudioSegment.empty()

    for speaker, text in turns:
        spoken = filter_text(text, args.lang)
        if not spoken.strip():
            continue
        segment = generate_segment(client, speaker_voices[speaker], spoken, speaker)
        if len(combined) > 0:
            combined += pause
        combined += segment

    output_path = Path(args.output)
    combined.export(output_path, format="mp3")
    print(f"\nSaved to: {output_path}  ({len(combined)/1000:.1f}s)")


if __name__ == "__main__":
    main()
