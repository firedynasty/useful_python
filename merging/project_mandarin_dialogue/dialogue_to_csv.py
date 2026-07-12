"""
dialogue_to_csv.py (Mandarin dialogue)

Reads a .txt file with Mandarin dialogue in the format:
  Speaker:
  Chinese line (may wrap)
  Pinyin line (may wrap)
  English line (may wrap)

No OpenAI needed — translations are already in the input.

Outputs a CSV with 3 columns: Chinese, Pinyin, Translation
Each row = one dialogue turn. Speaker labels are preserved as
section-header rows (e.g. "小红:,,") so downstream scripts can
pass them through.

Usage:
  python dialogue_to_csv.py --input dialogue.txt --output mandarin_dialogue_table.csv
"""

import argparse
import csv
import re

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="dialogue.txt", help="Path to dialogue .txt file")
parser.add_argument("--output", default="mandarin_dialogue_table.csv", help="Path for output CSV")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as f:
    raw_lines = f.read().strip().split("\n")

print(f"Reading: {args.input}")

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def has_pinyin_chars(text):
    """Check for tone-marked Latin vowels typical of pinyin."""
    return bool(re.search(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', text))

def is_speaker_label(text):
    """Speaker labels end with : or ： and are short."""
    return bool(re.match(r'^.{1,10}[：:]$', text.strip()))

# ── Group lines by speaker turn ─────────────────────────────────────────────
# Each turn: speaker label, then Chinese line(s), Pinyin line(s), English line(s)
# Lines may wrap, so we join continuations.

turns = []
current_speaker = ""
current_block = []  # lines between speaker labels

for line in raw_lines:
    stripped = line.strip()
    if not stripped:
        continue
    if is_speaker_label(stripped):
        if current_block:
            turns.append({"speaker": current_speaker, "lines": current_block})
            current_block = []
        current_speaker = stripped
        continue
    current_block.append(stripped)

if current_block:
    turns.append({"speaker": current_speaker, "lines": current_block})

# ── Parse each turn's block into Chinese / Pinyin / English ─────────────────
# Strategy: walk lines, classify each as Chinese, Pinyin, or English,
# joining consecutive lines of the same type.

parsed_turns = []

for turn in turns:
    lines = turn["lines"]
    chinese_parts = []
    pinyin_parts = []
    english_parts = []

    # Fixed order: Chinese → Pinyin → English
    # Each may span multiple lines (wrapping). Detect transitions by content.
    phase = "chinese"
    for line in lines:
        if phase == "chinese":
            if has_chinese(line):
                chinese_parts.append(line)
            else:
                # First non-Chinese line = start of pinyin
                phase = "pinyin"
                pinyin_parts.append(line)
        elif phase == "pinyin":
            # Stay in pinyin until the pinyin is terminated (ends with .?!)
            # AND the next line doesn't look like a pinyin continuation
            if not pinyin_parts:
                pinyin_parts.append(line)
            else:
                prev_ended = re.search(r'[.?!。？！]$', pinyin_parts[-1])
                if prev_ended:
                    # Previous pinyin line ended — this is English
                    phase = "english"
                    english_parts.append(line)
                else:
                    # Previous pinyin didn't end — this is a wrapped pinyin line
                    pinyin_parts.append(line)
        elif phase == "english":
            english_parts.append(line)

    parsed_turns.append({
        "speaker": turn["speaker"],
        "chinese": " ".join(chinese_parts),
        "pinyin": " ".join(pinyin_parts),
        "english": " ".join(english_parts),
    })

print(f"Parsed {len(parsed_turns)} dialogue turns")

# ── Write CSV ────────────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Chinese", "Pinyin", "Translation"])
    for turn in parsed_turns:
        # Write speaker as a section-header row
        writer.writerow([turn["speaker"], "", ""])
        writer.writerow([turn["chinese"], turn["pinyin"], turn["english"]])

print(f"Done! Wrote {len(parsed_turns)} turns to {args.output}")
