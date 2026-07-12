"""
make_adjusted.py (Mandarin dialogue)

Reads a dialogue CSV, pairs translation + pinyin line by line.
Speaker-label rows (e.g. "小红:,,") are passed through.

Output format:
  Translation line
  Pinyin line
  (blank)

Usage:
  python make_adjusted.py --input mandarin_dialogue_table.csv --output mandarin_dialogue_adjusted.txt
"""

import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="mandarin_dialogue_table.csv", help="Path to dialogue CSV")
parser.add_argument("--output", default="mandarin_dialogue_adjusted.txt", help="Path for output txt")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = [h.strip().lower() for h in rows[0]]

if "translation" in header:
    trans_col = header.index("translation")
else:
    trans_col = len(rows[0]) - 1

if "pinyin" in header:
    rom_col = header.index("pinyin")
elif "jyutping" in header:
    rom_col = header.index("jyutping")
elif "romanization" in header:
    rom_col = header.index("romanization")
else:
    rom_col = 1

data_start = 1
while data_start < len(rows) and all(not c.strip() for c in rows[data_start]):
    data_start += 1

lines = []
for row in rows[data_start:]:
    if len(row) <= max(rom_col, trans_col):
        continue
    # Pass through speaker-label rows (pinyin and translation are empty)
    if not row[rom_col].strip() and not row[trans_col].strip():
        speaker = row[0].strip() if row[0].strip() else ""
        if speaker:
            lines.append(speaker)
            lines.append("")
        continue
    rom_cell = row[rom_col].strip()
    trans_cell = row[trans_col].strip()
    if not rom_cell and not trans_cell:
        continue

    rom_lines = rom_cell.split("\n")
    trans_lines = trans_cell.split("\n")

    max_len = max(len(rom_lines), len(trans_lines))
    rom_lines += [""] * (max_len - len(rom_lines))
    trans_lines += [""] * (max_len - len(trans_lines))

    for t, r in zip(trans_lines, rom_lines):
        lines.append(t.strip())
        lines.append(r.strip())
        lines.append("")

with open(args.output, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Done! Wrote {len(lines)//3} paired lines to {args.output}")
