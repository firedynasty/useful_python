"""
lyrics_to_csv.py (Spanish)

Reads a .txt file with Spanish lyrics (+ section headers like [Verso 1]).
Sends each verse to OpenAI to get English translation.

Outputs a CSV with 2 columns: Spanish, Translation

Usage:
  export OPENAI_API_KEY=sk-...
  python lyrics_to_csv.py --input lyrics.txt --output spanish_table.csv
"""

import argparse
import csv
import json
import os
import re
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="lyrics.txt", help="Path to lyrics .txt file")
parser.add_argument("--output", default="spanish_table.csv", help="Path for output CSV")
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

all_verses = []
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

# ── Translate each verse via OpenAI ──────────────────────────────────────────

SYSTEM_PROMPT = """You are a Spanish-to-English translation assistant. You will receive Spanish song lyrics.

For each line, provide an English translation.

Return a JSON array of objects, one per line:
[
  {"english": "I know that you have a new love"},
  ...
]

Preserve the order. Return ONLY the JSON array, no markdown, no explanation."""

all_results = []

for vi, verse in enumerate(all_verses):
    spanish_block = "\n".join(verse["lines"])
    print(f"\n{verse['section']} ({vi+1}/{len(all_verses)}): {verse['lines'][0][:40]}...")

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": spanish_block},
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
            results.append({"english": ""})
        print(f"  Got {len(results)} lines")
        all_results.append(results)
    except json.JSONDecodeError:
        print(f"  WARNING: Invalid JSON")
        print(f"  {raw[:200]}")
        all_results.append([{"english": ""}] * len(verse["lines"]))

    time.sleep(0.5)

# ── Write CSV ────────────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Spanish", "Translation"])
    for verse, results in zip(all_verses, all_results):
        spanish_cell = "\n".join(verse["lines"])
        trans_cell = "\n".join(r.get("english", "") for r in results[:len(verse["lines"])])
        writer.writerow([spanish_cell, trans_cell])

print(f"\nDone! Wrote {len(all_verses)} verse rows to {args.output}")
