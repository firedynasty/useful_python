"""
colorcode_to_csv.py

Parses a saved colorcodedlyrics.com HTML page and extracts
the three columns (Romanization, Korean/Hangul, Translation)
into korean_table.csv.

The site uses a 3-column WordPress layout:
  - Column 1: Romanization (colored spans with <br> between lines)
  - Column 2: Hangul/Korean
  - Column 3: English Translation
  - Each <p> tag = one verse section
  - Lines within a verse separated by <br>

Usage:
  python colorcode_to_csv.py --input celebrity.html --output korean_table.csv
"""

import argparse
import csv
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Path to saved colorcodedlyrics HTML file")
parser.add_argument("--output", default="korean_table.csv", help="Path for output CSV")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Find the 3 wp-block-column divs
columns = soup.find_all("div", class_="wp-block-column")

if len(columns) < 3:
    print(f"WARNING: Expected 3 columns, found {len(columns)}")
    print("Make sure you saved the full page HTML from colorcodedlyrics.com")

# Extract <p> tags from each column's wp-block-group content area
def get_verses(column):
    """Extract verse texts from a column. Each <p> = one verse section."""
    group = column.find("div", class_="wp-block-group__inner-container")
    if not group:
        return []
    # Some pages nest an extra wp-block-group inside
    inner = group.find("div", class_="wp-block-group__inner-container")
    if inner:
        group = inner
    verses = []
    for p in group.find_all("p"):
        # Get text with <br> converted to \n
        text = p.get_text(separator="\n", strip=True)
        if text:
            verses.append(text)
    return verses

rom_verses = get_verses(columns[0])
kor_verses = get_verses(columns[1])
trans_verses = get_verses(columns[2])

print(f"Found {len(rom_verses)} romanization verses")
print(f"Found {len(kor_verses)} korean verses")
print(f"Found {len(trans_verses)} translation verses")

# Pad to same length
max_len = max(len(rom_verses), len(kor_verses), len(trans_verses))
rom_verses += [""] * (max_len - len(rom_verses))
kor_verses += [""] * (max_len - len(kor_verses))
trans_verses += [""] * (max_len - len(trans_verses))

# Write CSV - each row is one verse, newlines preserved within cells
with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Romanization", "Korean", "Translation"])
    for r, k, t in zip(rom_verses, kor_verses, trans_verses):
        writer.writerow([r, k, t])

print(f"\nDone! Wrote {max_len} verse rows to {args.output}")
