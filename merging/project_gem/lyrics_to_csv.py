"""
lyrics_to_csv.py

Reads a .txt file containing alternating Chinese + Pinyin lines.
Sends each verse to OpenAI to get English translations.
Outputs a CSV with 3 columns: Chinese, Pinyin, Translation.

Input format:
  想听 你听过的音乐
  Xiǎng tīng nǐ tīng guò de yīn yuè
  想看 你看过的小说
  Xiǎng kàn nǐ kàn guò de xiǎo shuō

  想到 你到过的地方
  Hé nǐ céng dù guò de shí guāng
  ...

Usage:
  export OPENAI_API_KEY=sk-...
  python lyrics_to_csv.py --input lyrics.txt --output gem_table.csv
"""

import argparse
import csv
import json
import os
import re
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="lyrics.txt", help="Path to lyrics .txt file")
parser.add_argument("--output", default="gem_table.csv", help="Path for output CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set. Export it first:\n  export OPENAI_API_KEY=sk-...")

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Parse txt file ───────────────────────────────────────────────────────────

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

with open(args.input, "r", encoding="utf-8") as f:
    lines = f.read().strip().split("\n")

print(f"Reading: {args.input}")

# Parse into verses (groups separated by blank lines)
# Each verse = list of {chinese, pinyin}
all_verses = []
current_verse = []
i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        if current_verse:
            all_verses.append(current_verse)
            current_verse = []
        i += 1
        continue

    if has_chinese(line):
        chinese = line
        pinyin = ""
        if i + 1 < len(lines) and not has_chinese(lines[i + 1].strip()) and lines[i + 1].strip():
            pinyin = lines[i + 1].strip()
            i += 2
        else:
            i += 1
        current_verse.append({"chinese": chinese, "pinyin": pinyin})
    else:
        i += 1

if current_verse:
    all_verses.append(current_verse)

total_lines = sum(len(v) for v in all_verses)
print(f"Parsed {len(all_verses)} verses, {total_lines} lines total")

# ── Translate each verse via OpenAI ──────────────────────────────────────────

SYSTEM_PROMPT = """You are a Chinese-English translator. You will receive Chinese lyrics with pinyin.
Translate each line to natural English. Return a JSON array of strings, one translation per line.
Preserve the order. Return ONLY the JSON array, no markdown, no explanation."""

all_translations = []

for vi, verse in enumerate(all_verses):
    chinese_block = "\n".join(f"{p['chinese']}  ({p['pinyin']})" for p in verse)

    print(f"\nVerse {vi+1}/{len(all_verses)}: {verse[0]['chinese'][:30]}...")

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chinese_block},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]

    try:
        translations = json.loads(raw)
        while len(translations) < len(verse):
            translations.append("")
        print(f"  Got {len(translations)} translations")
        all_translations.append(translations)
    except json.JSONDecodeError:
        print(f"  WARNING: Invalid JSON, using empty translations")
        print(f"  {raw[:200]}")
        all_translations.append([""] * len(verse))

    time.sleep(0.5)

# ── Write CSV ────────────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Chinese", "Pinyin", "Translation"])
    for verse, translations in zip(all_verses, all_translations):
        chinese_cell = "\n".join(p["chinese"] for p in verse)
        pinyin_cell = "\n".join(p["pinyin"] for p in verse)
        trans_cell = "\n".join(translations[:len(verse)])
        writer.writerow([chinese_cell, pinyin_cell, trans_cell])

print(f"\nDone! Wrote {len(all_verses)} verse rows to {args.output}")
