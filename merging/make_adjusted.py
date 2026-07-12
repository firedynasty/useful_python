"""
Reads a lyrics CSV, splits each cell by newlines,
pairs romanization + translation line by line, and outputs
a .txt file in the format:

Translation line
romanization line

Translation line
romanization line
...

Supports both formats:
  - 2-column: Romanization, Translation
  - 3-column: Romanization, Korean, Translation

Usage:
  python make_adjusted.py --input celebrity_table.csv --output celebrity_adjusted.txt
"""

import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="korean_table.csv", help="Path to lyrics CSV")
parser.add_argument("--output", default="korean_table_adjusted.txt", help="Path for output txt")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = list(reader)

# Detect format from header
header = [h.strip().lower() for h in rows[0]]
if "translation" in header:
    trans_col = header.index("translation")
else:
    trans_col = len(rows[0]) - 1  # assume last column

rom_col = 0  # romanization is always first

# Find where data starts (skip empty rows after header)
data_start = 1
while data_start < len(rows) and all(not c.strip() for c in rows[data_start]):
    data_start += 1

lines = []
for row in rows[data_start:]:
    if len(row) <= max(rom_col, trans_col):
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
        lines.append("")  # blank line separator

with open(args.output, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Done! Wrote {len(lines)//3} paired lines to {args.output}")
