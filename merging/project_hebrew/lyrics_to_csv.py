"""
lyrics_to_csv.py (Hebrew)

Reads a .txt file with romanized Hebrew lyrics (+ section headers like [Verse 1]).
Sends each verse to OpenAI to get:
  1. Hebrew script
  2. English translation

Outputs a CSV with 3 columns: Romanization, Hebrew, Translation

Input format:
  [Verse 1]
  Bekarov tizrach hashemesh
  Neda yamim yafim me'eleh
  ...

  [Chorus]
  Am Yisrael chai
  ...

Usage:
  export OPENAI_API_KEY=sk-...
  python lyrics_to_csv.py --input lyrics.txt --output hebrew_table.csv
"""

import argparse
import csv
import json
import os
import re
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="lyrics.txt", help="Path to lyrics .txt file")
parser.add_argument("--output", default="hebrew_table.csv", help="Path for output CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set. Export it first:\n  export OPENAI_API_KEY=sk-...")

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Parse txt file ───────────────────────────────────────────────────────────

with open(args.input, "r", encoding="utf-8") as f:
    lines = f.read().strip().split("\n")

print(f"Reading: {args.input}")

section_pattern = re.compile(r'^\[(.+)\]$')

all_verses = []  # list of {section, lines}
current_section = ""
current_lines = []

for line in lines:
    line = line.strip()
    if not line:
        if current_lines:
            all_verses.append({"section": current_section, "lines": current_lines})
            current_lines = []
        continue
    m = section_pattern.match(line)
    if m:
        if current_lines:
            all_verses.append({"section": current_section, "lines": current_lines})
            current_lines = []
        current_section = m.group(1)
        continue
    current_lines.append(line)

if current_lines:
    all_verses.append({"section": current_section, "lines": current_lines})

total_lines = sum(len(v["lines"]) for v in all_verses)
print(f"Parsed {len(all_verses)} verses, {total_lines} lines total")

# ── Translate + transliterate each verse via OpenAI ──────────────────────────

SYSTEM_PROMPT = """You are a Hebrew linguistics assistant. You will receive romanized Hebrew lyrics.

For each line, provide:
1. The Hebrew script (niqqud optional)
2. An English translation

Return a JSON array of objects, one per line:
[
  {"hebrew": "בקרוב תזרח השמש", "english": "Soon the sun will rise"},
  ...
]

Preserve the order. Return ONLY the JSON array, no markdown, no explanation."""

all_results = []

for vi, verse in enumerate(all_verses):
    rom_block = "\n".join(verse["lines"])
    print(f"\n{verse['section']} ({vi+1}/{len(all_verses)}): {verse['lines'][0][:40]}...")

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": rom_block},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]

    try:
        results = json.loads(raw)
        while len(results) < len(verse["lines"]):
            results.append({"hebrew": "", "english": ""})
        print(f"  Got {len(results)} lines")
        all_results.append(results)
    except json.JSONDecodeError:
        print(f"  WARNING: Invalid JSON")
        print(f"  {raw[:200]}")
        all_results.append([{"hebrew": "", "english": ""}] * len(verse["lines"]))

    time.sleep(0.5)

# ── Write CSV ────────────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Romanization", "Hebrew", "Translation"])
    for verse, results in zip(all_verses, all_results):
        rom_cell = "\n".join(verse["lines"])
        heb_cell = "\n".join(r.get("hebrew", "") for r in results[:len(verse["lines"])])
        trans_cell = "\n".join(r.get("english", "") for r in results[:len(verse["lines"])])
        writer.writerow([rom_cell, heb_cell, trans_cell])

print(f"\nDone! Wrote {len(all_verses)} verse rows to {args.output}")
