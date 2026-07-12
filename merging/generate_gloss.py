"""
generate_gloss.py

Reads a lyrics CSV (from colorcode_to_csv.py) and sends each verse
to OpenAI GPT-4o to generate a word-by-word morpheme gloss.

Output: a preformatted CSV with columns: Korean, Romanization, English meaning

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_gloss.py --input celebrity_table.csv --output celebrity_preformatted.csv
"""

import argparse
import csv
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Path to lyrics CSV (from colorcode_to_csv.py)")
parser.add_argument("--output", default="preformatted.csv", help="Path for output gloss CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Export it first:\n"
        "  export OPENAI_API_KEY=sk-..."
    )

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Read lyrics CSV ──────────────────────────────────────────────────────────

with open(args.input, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = [h.strip().lower() for h in rows[0]]
rom_col = 0
kor_col = header.index("korean") if "korean" in header else 1
trans_col = header.index("translation") if "translation" in header else len(rows[0]) - 1

verses = []
for row in rows[1:]:
    if len(row) <= max(rom_col, kor_col, trans_col):
        continue
    rom = row[rom_col].strip()
    kor = row[kor_col].strip()
    trans = row[trans_col].strip()
    if rom or kor:
        verses.append({"romanization": rom, "korean": kor, "translation": trans})

print(f"Loaded {len(verses)} verses from {args.input}")

# ── Gloss each verse ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Korean linguistics assistant that creates word-by-word glosses.

For each verse you receive, break down EVERY word and morpheme. Return a JSON array of objects:
[
  {"korean": "세상의", "romanization": "sesange", "english": "world's (의: possessive)"},
  {"korean": "모서리", "romanization": "moseori", "english": "edge / corner"},
  ...
]

Rules:
- Split attached particles into separate rows (e.g. 별이라도 → 별 + 이라도)
- Use the romanization provided — do NOT re-romanize differently
- Include grammar notes in parentheses for particles and endings
- Keep words in the same order as the verse
- For English/code-switch words (e.g. "outsider", "play list"), include them as-is
- Return ONLY the JSON array, no markdown, no explanation"""

all_glosses = []

for i, verse in enumerate(verses):
    prompt = f"""Verse {i+1}:

Korean:
{verse['korean']}

Romanization:
{verse['romanization']}

Translation:
{verse['translation']}"""

    print(f"\nVerse {i+1}/{len(verses)}: {verse['korean'][:40]}...")

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]

    try:
        glosses = json.loads(raw)
        print(f"  Got {len(glosses)} words")
        all_glosses.append(glosses)
    except json.JSONDecodeError:
        print(f"  WARNING: Invalid JSON, skipping verse")
        print(f"  {raw[:200]}")
        all_glosses.append([])

    # Small delay to avoid rate limits
    time.sleep(0.5)

# ── Write output CSV ─────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Korean", "Romanization", "English meaning"])
    for i, glosses in enumerate(all_glosses):
        for g in glosses:
            writer.writerow([
                g.get("korean", ""),
                g.get("romanization", ""),
                g.get("english", ""),
            ])

total_words = sum(len(g) for g in all_glosses)
print(f"\nDone! Wrote {total_words} gloss rows to {args.output}")
