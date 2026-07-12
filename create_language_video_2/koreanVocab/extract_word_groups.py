"""
extract_word_groups.py

Generates a CSV showing all Korean words grouped by level and lesson.

Supports both CEFR vocab (vocab/) and TOPIK vocab (topik_vocab/).

Usage:
  python extract_word_groups.py                                          # TOPIK, 20 words/lesson
  python extract_word_groups.py --words_per_lesson 30                    # TOPIK, 30 words/lesson
  python extract_word_groups.py --vocab_dir vocab --levels A1 A2 B1 B2 C1 C2 --lessons_per_level 10 --output cefr_word_groups.csv
"""

import argparse
import csv
import json
import math
import os

parser = argparse.ArgumentParser()
parser.add_argument("--vocab_dir", default="topik_vocab")
parser.add_argument("--levels", nargs="+", default=["A", "B", "C"],
                    help="Levels to include (e.g. A B C or A1 A2 B1 B2 C1 C2)")
parser.add_argument("--output", default="topik_word_groups.csv")
parser.add_argument("--lessons_per_level", type=int, default=None,
                    help="Fixed number of lessons per level (overrides --words_per_lesson)")
parser.add_argument("--words_per_lesson", type=int, default=20,
                    help="Target words per lesson (default: 20)")
args = parser.parse_args()

rows = []

for level in args.levels:
    vocab_file = os.path.join(args.vocab_dir, f"{level}.json")
    if not os.path.exists(vocab_file):
        print(f"Skipping {level} (no vocab file)")
        continue

    with open(vocab_file, "r", encoding="utf-8") as f:
        words = json.load(f)

    if args.lessons_per_level is not None:
        total_lessons = min(args.lessons_per_level, len(words))
        batch_size = math.ceil(len(words) / total_lessons)
    else:
        batch_size = args.words_per_lesson
        total_lessons = math.ceil(len(words) / batch_size)

    print(f"  {level}: {len(words)} words → {total_lessons} lessons ({batch_size} words/lesson)")

    for lesson in range(1, total_lessons + 1):
        start = (lesson - 1) * batch_size
        end = min(start + batch_size, len(words))
        batch = words[start:end]

        for w in batch:
            korean = w["korean"]
            english = w["english"]
            pos = w.get("pos", "")
            romanization = w.get("romanization", "")
            hanja = w.get("hanja", "")
            rows.append([level, lesson, korean, pos, romanization, hanja, english])

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Level", "Lesson", "Korean", "POS", "Romanization", "Hanja", "English"])
    writer.writerows(rows)

print(f"\nWrote {len(rows)} words to {args.output}")
