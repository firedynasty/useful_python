"""
extract_word_groups.py

Generates a CSV showing all French CEFR words grouped by level and lesson.

Usage:
  python extract_word_groups.py
  python extract_word_groups.py --output my_groups.csv
"""

import argparse
import csv
import json
import math
import os

ALL_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

parser = argparse.ArgumentParser()
parser.add_argument("--vocab_dir", default="vocab")
parser.add_argument("--output", default="word_groups.csv")
parser.add_argument("--lessons_per_level", type=int, default=10)
args = parser.parse_args()

rows = []

for level in ALL_LEVELS:
    vocab_file = os.path.join(args.vocab_dir, f"{level}.json")
    if not os.path.exists(vocab_file):
        print(f"Skipping {level} (no vocab file)")
        continue

    with open(vocab_file, "r", encoding="utf-8") as f:
        words = json.load(f)

    total_lessons = min(args.lessons_per_level, len(words))
    batch_size = math.ceil(len(words) / total_lessons)

    for lesson in range(1, total_lessons + 1):
        start = (lesson - 1) * batch_size
        end = min(start + batch_size, len(words))
        batch = words[start:end]

        for w in batch:
            french = w["french"]
            english = w["english"]
            pos = w.get("pos", "")
            gender = w.get("gender", "")
            rows.append([level, lesson, french, pos, gender or "", english])

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["CEFR Level", "Lesson", "French", "POS", "Gender", "English"])
    writer.writerows(rows)

print(f"Wrote {len(rows)} words to {args.output}")
