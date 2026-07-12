#!/usr/bin/env python3
"""
Merge two SRT files into a combined text file.
Uses Chinese timestamps. Pairs entries proportionally by position
since Whisper generates different timestamp offsets for each language.
Output: timestamp  Chinese  English
"""

import argparse
import re


def time_to_ms(ts):
    """Convert HH:MM:SS,mmm to milliseconds."""
    match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", ts)
    h, m, s, ms = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    return h * 3600000 + m * 60000 + s * 1000 + ms


def format_time(ms):
    """Convert milliseconds to M:SS format."""
    total_s = ms // 1000
    m = total_s // 60
    s = total_s % 60
    return f"{m}:{s:02d}"


def parse_srt(filepath):
    """Parse SRT file, return list of (start_ms, end_ms, text)."""
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
        end = time_to_ms(ts_match.group(2).strip())
        text = " ".join(lines[2:]).strip()
        entries.append((start, end, text))

    return entries


def main():
    parser = argparse.ArgumentParser(description="Merge two SRT files by timestamp")
    parser.add_argument("-c", "--chinese", required=True, help="Chinese SRT file")
    parser.add_argument("-e", "--english", required=True, help="English SRT file")
    parser.add_argument("-o", "--output", default="english_chinese.txt", help="Output file")
    args = parser.parse_args()

    chinese = parse_srt(args.chinese)
    english = parse_srt(args.english)

    zh_len = len(chinese)
    en_len = len(english)

    with open(args.output, "w", encoding="utf-8") as f:
        for i, (zh_start, zh_end, zh_text) in enumerate(chinese):
            # Map proportionally — always show the English even if it repeats
            en_idx = int(i * en_len / zh_len)
            en_idx = min(en_idx, en_len - 1)
            en_text = english[en_idx][2]

            timestamp = format_time(zh_start)
            f.write(f"{timestamp} {zh_text} {en_text}\n\n")

    print(f"Written {zh_len} entries to {args.output}")


if __name__ == "__main__":
    main()
