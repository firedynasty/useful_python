#!/usr/bin/env python3
"""
Transcribe a Chinese MP3 and translate to English in one step.

Usage:
    python mp3_to_translated_txt.py -i audio.mp3
    python mp3_to_translated_txt.py -i audio.mp3 -o output.txt

Output: text file with lines like:
    0:00 原来的中文 This is the English translation

Requires: OPENAI_API_KEY env var, ffmpeg in PATH (for splitting large files)
"""

import argparse
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

from openai import OpenAI

WHISPER_SIZE_LIMIT_MB = 24  # Whisper API limit is 25MB; use 24 to be safe
SEGMENT_DURATION = 600      # 10 minutes per segment


def time_to_ms(ts):
    match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", ts)
    h, m, s, ms = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    return h * 3600000 + m * 60000 + s * 1000 + ms


def format_time(ms):
    total_s = ms // 1000
    m = total_s // 60
    s = total_s % 60
    return f"{m}:{s:02d}"


def parse_srt_text(srt_text):
    """Parse SRT string, return list of (start_ms, text)."""
    entries = []
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        ts_match = re.match(r"(.+?)\s*-->\s*(.+)", lines[1])
        if not ts_match:
            continue
        start = time_to_ms(ts_match.group(1).strip())
        text = " ".join(lines[2:]).strip()
        entries.append((start, text))
    return entries


def transcribe_segment(client, mp3_path, offset_ms=0):
    """Transcribe one MP3 segment; offset_ms shifts all timestamps."""
    with open(mp3_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="zh",
            response_format="srt",
        )
    entries = parse_srt_text(response)
    # Apply timestamp offset for segments after the first
    return [(start + offset_ms, text) for start, text in entries]


def split_audio(mp3_path, tmp_dir):
    """Split MP3 into 10-minute segments using ffmpeg. Returns list of (path, offset_ms)."""
    pattern = os.path.join(tmp_dir, "segment_%03d.mp3")
    subprocess.run(
        [
            "ffmpeg", "-i", mp3_path,
            "-f", "segment",
            "-segment_time", str(SEGMENT_DURATION),
            "-c", "copy",
            pattern,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    segments = sorted(Path(tmp_dir).glob("segment_*.mp3"))
    return [(str(seg), i * SEGMENT_DURATION * 1000) for i, seg in enumerate(segments)]


def translate_batch(client, texts):
    """Translate a batch of Chinese lines to English in one API call."""
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Chinese-to-English translator. "
                    "Translate each numbered line from Chinese to natural English. "
                    "Keep the same numbering. Return only the numbered translations, nothing else."
                ),
            },
            {"role": "user", "content": numbered},
        ],
    )
    raw = response.choices[0].message.content.strip()
    translations = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^\d+\.\s*(.+)", line)
        if match:
            translations.append(match.group(1).strip())
    return translations


def main():
    parser = argparse.ArgumentParser(description="Transcribe Chinese MP3 and translate to English")
    parser.add_argument("-i", "--input", required=True, help="Input MP3 file")
    parser.add_argument("-o", "--output", help="Output TXT file (default: same name as input)")
    parser.add_argument("--batch-size", type=int, default=20, help="Lines per translation API call (default: 20)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set.")
        return

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return

    output_path = args.output or Path(input_path).stem + ".txt"
    client = OpenAI(api_key=api_key)

    file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    all_entries = []

    if file_size_mb <= WHISPER_SIZE_LIMIT_MB:
        print(f"Transcribing {input_path} ({file_size_mb:.1f} MB)...")
        all_entries = transcribe_segment(client, input_path, offset_ms=0)
    else:
        print(f"File is {file_size_mb:.1f} MB — splitting into 10-min segments...")
        with tempfile.TemporaryDirectory() as tmp_dir:
            segments = split_audio(input_path, tmp_dir)
            for seg_path, offset_ms in segments:
                seg_name = os.path.basename(seg_path)
                print(f"  Transcribing {seg_name} (offset {offset_ms // 1000 // 60}min)...")
                entries = transcribe_segment(client, seg_path, offset_ms=offset_ms)
                all_entries.extend(entries)

    print(f"Transcribed {len(all_entries)} lines. Translating...")

    results = []
    batch_size = args.batch_size
    for i in range(0, len(all_entries), batch_size):
        batch = all_entries[i : i + batch_size]
        texts = [e[1] for e in batch]
        print(f"  Translating lines {i+1}–{min(i+batch_size, len(all_entries))}...")
        translations = translate_batch(client, texts)
        while len(translations) < len(texts):
            translations.append("")
        for j, (start, zh_text) in enumerate(batch):
            results.append((start, zh_text, translations[j]))
        time.sleep(0.2)

    with open(output_path, "w", encoding="utf-8") as f:
        for start, zh_text, en_text in results:
            timestamp = format_time(start)
            f.write(f"{timestamp} {zh_text} {en_text}\n\n")

    print(f"Done. Written {len(results)} lines to {output_path}")


if __name__ == "__main__":
    main()
