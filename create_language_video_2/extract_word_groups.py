"""
extract_word_groups.py

Generates a CSV showing all HSK words grouped by level and lesson,
sorted by frequency (most common first within each lesson).

Output: word_groups.csv

Usage:
  python extract_word_groups.py
  python extract_word_groups.py --output my_groups.csv
  python extract_word_groups.py --lessons_per_level 5
"""

import argparse
import csv
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument("--vocab_dir", default="complete-hsk-vocabulary/wordlists/exclusive/newest")
parser.add_argument("--output", default="word_groups.csv")
parser.add_argument("--lessons_per_level", type=int, default=10)
args = parser.parse_args()

rows = []

for level in range(1, 8):
    vocab_file = os.path.join(args.vocab_dir, f"{level}.json")
    with open(vocab_file, "r", encoding="utf-8") as f:
        words = json.load(f)

    words.sort(key=lambda w: w.get("frequency", 99999))

    total_lessons = min(args.lessons_per_level, len(words))
    batch_size = math.ceil(len(words) / total_lessons)

    for lesson in range(1, total_lessons + 1):
        start = (lesson - 1) * batch_size
        end = min(start + batch_size, len(words))
        batch = words[start:end]

        for w in batch:
            simplified = w["simplified"]
            form = w["forms"][0]
            pinyin = form["transcriptions"]["pinyin"]
            meanings = "; ".join(form["meanings"][:2]) if form["meanings"] else ""
            freq = w.get("frequency", "")

            rows.append([level, lesson, freq, simplified, pinyin, meanings])

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["HSK Level", "Lesson", "Frequency Rank", "Chinese", "Pinyin", "English"])
    writer.writerows(rows)

print(f"Wrote {len(rows)} words to {args.output}")
