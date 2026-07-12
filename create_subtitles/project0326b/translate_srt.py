#!/usr/bin/env python3
"""
Translate a Chinese SRT file to English using OpenAI.
Preserves all timestamps from the source SRT.
Output: english_chinese.txt with timestamp, Chinese, English per line.
translate_srt.py
python translate_srt.py -c chinese.srt -o english_chinese.txt     
"""

import argparse
import os
import re
import time
from openai import OpenAI


def time_to_ms(ts):
    match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", ts)
    h, m, s, ms = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    return h * 3600000 + m * 60000 + s * 1000 + ms


def format_time(ms):
    total_s = ms // 1000
    m = total_s // 60
    s = total_s % 60
    return f"{m}:{s:02d}"


def parse_srt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    entries = []
    blocks = re.split(r"\n\s*\n", content.strip())

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


def translate_batch(client, texts):
    """Translate a batch of Chinese texts to English in one API call."""
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
                )
            },
            {"role": "user", "content": numbered}
        ]
    )
    raw = response.choices[0].message.content.strip()
    translations = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove leading "1. " numbering
        match = re.match(r"^\d+\.\s*(.+)", line)
        if match:
            translations.append(match.group(1).strip())
    return translations


def main():
    parser = argparse.ArgumentParser(description="Translate Chinese SRT to English")
    parser.add_argument("-c", "--chinese", required=True, help="Chinese SRT file")
    parser.add_argument("-o", "--output", default="english_chinese.txt", help="Output file")
    parser.add_argument("--batch-size", type=int, default=20, help="Entries per API call (default: 20)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return

    client = OpenAI(api_key=api_key)
    entries = parse_srt(args.chinese)
    print(f"Loaded {len(entries)} entries from {args.chinese}")

    results = []
    batch_size = args.batch_size

    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]
        texts = [e[1] for e in batch]
        print(f"Translating entries {i+1}–{min(i+batch_size, len(entries))}...")

        translations = translate_batch(client, texts)

        # Pad if translation count doesn't match (shouldn't happen, but just in case)
        while len(translations) < len(texts):
            translations.append("")

        for j, (start, zh_text) in enumerate(batch):
            results.append((start, zh_text, translations[j]))

        time.sleep(0.2)  # small delay to avoid rate limits

    with open(args.output, "w", encoding="utf-8") as f:
        for start, zh_text, en_text in results:
            timestamp = format_time(start)
            f.write(f"{timestamp} {zh_text} {en_text}\n\n")

    print(f"Done. Written {len(results)} entries to {args.output}")


if __name__ == "__main__":
    main()
