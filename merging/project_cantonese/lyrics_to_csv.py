"""
lyrics_to_csv.py (Cantonese)

Reads a .txt file with Cantonese lyrics in triplet format:
  Chinese characters line
  Jyutping romanization line
  (English translation) line

Parses the triplets and outputs a CSV with 3 columns:
  Cantonese, Jyutping, Translation

No OpenAI needed — translations are already in the input.

Usage:
  python lyrics_to_csv.py --input lyrics.txt --output cantonese_table.csv
"""

import argparse
import csv
import re

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="lyrics.txt", help="Path to lyrics .txt file")
parser.add_argument("--output", default="cantonese_table.csv", help="Path for output CSV")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as f:
    lines = f.read().strip().split("\n")

print(f"Reading: {args.input}")

section_pattern = re.compile(r'^\[(.+)\]$')
paren_pattern = re.compile(r'^\((.+)\)$')

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

all_verses = []
current_verse = []
i = 0

# Skip title/metadata lines before the first section header
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if section_pattern.match(line):
        break  # found first section header, stop skipping
    i += 1  # skip non-section lines (title, metadata, etc.)

while i < len(lines):
    line = lines[i].strip()

    # Blank line — end of verse
    if not line:
        if current_verse:
            all_verses.append(current_verse)
            current_verse = []
        i += 1
        continue

    # Section header like [Verse 1]
    if section_pattern.match(line):
        if current_verse:
            all_verses.append(current_verse)
            current_verse = []
        i += 1
        continue

    # Skip reference lines like (重唱 Chorus)
    if paren_pattern.match(line) and not has_chinese(line.replace("重唱", "")):
        i += 1
        continue

    # Parse triplet: Chinese, Jyutping, (English)
    if has_chinese(line):
        chinese = line
        jyutping = ""
        english = ""
        # Next line should be Jyutping
        if i + 1 < len(lines) and not has_chinese(lines[i + 1].strip()) and lines[i + 1].strip() and not paren_pattern.match(lines[i + 1].strip()):
            jyutping = lines[i + 1].strip()
            # Line after that should be (English)
            if i + 2 < len(lines):
                m = paren_pattern.match(lines[i + 2].strip())
                if m:
                    english = m.group(1)
                    i += 3
                else:
                    i += 2
            else:
                i += 2
        else:
            i += 1
        current_verse.append({"cantonese": chinese, "jyutping": jyutping, "english": english})
    else:
        i += 1

if current_verse:
    all_verses.append(current_verse)

total_lines = sum(len(v) for v in all_verses)
print(f"Parsed {len(all_verses)} verses, {total_lines} lines total")

# ── Write CSV ────────────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Cantonese", "Jyutping", "Translation"])
    for verse in all_verses:
        cantonese_cell = "\n".join(p["cantonese"] for p in verse)
        jyutping_cell = "\n".join(p["jyutping"] for p in verse)
        english_cell = "\n".join(p["english"] for p in verse)
        writer.writerow([cantonese_cell, jyutping_cell, english_cell])

print(f"Done! Wrote {len(all_verses)} verse rows to {args.output}")
