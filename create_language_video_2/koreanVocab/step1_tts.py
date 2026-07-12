"""
step1_tts.py

Reads a dialogue.txt (A: Korean, P: Romanization, B: English triplets),
generates per-line audio via OpenAI TTS, stitches with pydub,
and generates korean.srt + romanization.srt + english.srt with timestamps.

Language settings imported from language.py.

Usage:
  export OPENAI_API_KEY=sk-...
  python step1_tts.py --input dialogue.txt --output_dir output/
"""

import argparse
import io
import os
import re
import sys
import time

from language import LANGUAGE_NAME, TTS_VOICE, TARGET_FIELD

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="dialogue.txt", help="Path to dialogue txt")
parser.add_argument("--output_dir", default="output", help="Output directory")
parser.add_argument("--model", default="gpt-4o-mini-tts", help="OpenAI TTS model")
parser.add_argument("--voice_target", default=TTS_VOICE, help=f"Voice for {LANGUAGE_NAME} lines")
parser.add_argument("--voice_eng", default="nova", help="Voice for English lines")
parser.add_argument("--pause_ms", type=int, default=800, help="Pause between lines (ms)")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

from openai import OpenAI
from pydub import AudioSegment

client = OpenAI(api_key=api_key)

os.makedirs(args.output_dir, exist_ok=True)

# ── Parse dialogue (A/P/B triplets) ───────────────────────────────────────

with open(args.input, "r", encoding="utf-8") as f:
    raw = f.read().strip().split("\n")

section_pattern = re.compile(r"^\[(.+)\]$")
a_pattern = re.compile(r"^A:\s*(.+)$")
p_pattern = re.compile(r"^P:\s*(.+)$")
b_pattern = re.compile(r"^B:\s*(.+)$")

entries = []
i = 0
while i < len(raw):
    line = raw[i].strip()
    if not line or section_pattern.match(line):
        i += 1
        continue
    ma = a_pattern.match(line)
    if ma:
        # Look for P: and B: lines following A:
        romanization = None
        english = None
        next_idx = i + 1

        # Check for P: line (optional)
        if next_idx < len(raw):
            mp = p_pattern.match(raw[next_idx].strip())
            if mp:
                romanization = mp.group(1)
                next_idx += 1

        # Check for B: line
        if next_idx < len(raw):
            mb = b_pattern.match(raw[next_idx].strip())
            if mb:
                english = mb.group(1)
                entries.append({
                    TARGET_FIELD: ma.group(1),
                    "romanization": romanization or "",
                    "english": english,
                })
                i = next_idx + 1
                continue
    i += 1

print(f"Parsed {len(entries)} dialogue lines ({LANGUAGE_NAME})")

# ── Helpers ─────────────────────────────────────────────────────────────────


def fmt_srt(ms):
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    ms_r = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms_r:03d}"


# ── Generate TTS + stitch ──────────────────────────────────────────────────

silence = AudioSegment.silent(duration=args.pause_ms)
short_pause = AudioSegment.silent(duration=400)
full_audio = AudioSegment.empty()

srt_target = []
srt_romanization = []
srt_english = []
cursor_ms = 0

for i, entry in enumerate(entries):
    print(f"  [{i+1}/{len(entries)}] {entry[TARGET_FIELD][:50]}...")

    # Target language line
    resp_target = client.audio.speech.create(
        model=args.model,
        voice=args.voice_target,
        input=entry[TARGET_FIELD],
        response_format="mp3",
        speed=1,
    )
    seg_target = AudioSegment.from_mp3(io.BytesIO(resp_target.content))

    target_start = cursor_ms
    target_end = cursor_ms + len(seg_target)
    full_audio += seg_target
    cursor_ms = target_end

    # Short pause between target and English
    full_audio += short_pause
    cursor_ms += 400

    # English line
    resp_eng = client.audio.speech.create(
        model=args.model,
        voice=args.voice_eng,
        input=entry["english"],
        response_format="mp3",
        speed=1,
    )
    seg_eng = AudioSegment.from_mp3(io.BytesIO(resp_eng.content))

    eng_start = cursor_ms
    eng_end = cursor_ms + len(seg_eng)
    full_audio += seg_eng
    cursor_ms = eng_end

    # SRT: all tracks show for the full exchange duration
    idx = i + 1
    srt_target.append(f"{idx}\n{fmt_srt(target_start)} --> {fmt_srt(eng_end)}\n{entry[TARGET_FIELD]}\n")
    srt_romanization.append(f"{idx}\n{fmt_srt(target_start)} --> {fmt_srt(eng_end)}\n{entry['romanization']}\n")
    srt_english.append(f"{idx}\n{fmt_srt(target_start)} --> {fmt_srt(eng_end)}\n{entry['english']}\n")

    # Pause between exchanges
    if i < len(entries) - 1:
        full_audio += silence
        cursor_ms += args.pause_ms

    time.sleep(0.3)

print(f"\nTotal duration: {cursor_ms / 1000:.1f}s")

# ── Write files ─────────────────────────────────────────────────────────────

mp3_path = os.path.join(args.output_dir, "dialogue.mp3")
full_audio.export(mp3_path, format="mp3")
print(f"Wrote: {mp3_path}")

target_srt_name = LANGUAGE_NAME.lower().replace(" ", "_")
target_path = os.path.join(args.output_dir, f"{target_srt_name}.srt")
with open(target_path, "w", encoding="utf-8") as f:
    f.write("\n".join(srt_target))
print(f"Wrote: {target_path}")

rom_path = os.path.join(args.output_dir, "romanization.srt")
with open(rom_path, "w", encoding="utf-8") as f:
    f.write("\n".join(srt_romanization))
print(f"Wrote: {rom_path}")

eng_path = os.path.join(args.output_dir, "english.srt")
with open(eng_path, "w", encoding="utf-8") as f:
    f.write("\n".join(srt_english))
print(f"Wrote: {eng_path}")

print(f"\nDone! Next: bash step2_video.sh")
