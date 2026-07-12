"""
generate_gloss.py

Reads a lyrics CSV and sends each verse to OpenAI GPT-4o
to generate a word-by-word morpheme gloss.

Auto-detects language from CSV headers:
  - Chinese: Chinese, Pinyin, Translation
  - Korean: Romanization, Korean, Translation

Output: a preformatted CSV with columns matching the language.

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_gloss.py --input gem_table.csv --output gem_preformatted.csv
"""

import argparse
import csv
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Path to lyrics CSV")
parser.add_argument("--output", default="preformatted.csv", help="Path for output gloss CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set. Export it first:\n  export OPENAI_API_KEY=sk-...")

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Read lyrics CSV and detect language ──────────────────────────────────────

with open(args.input, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = [h.strip().lower() for h in rows[0]]

if "chinese" in header:
    lang = "chinese"
    native_col = header.index("chinese")
    rom_col = header.index("pinyin") if "pinyin" in header else 1
    native_label = "Chinese"
    rom_label = "Pinyin"
elif "korean" in header:
    lang = "korean"
    native_col = header.index("korean")
    rom_col = header.index("romanization") if "romanization" in header else 0
    native_label = "Korean"
    rom_label = "Romanization"
else:
    lang = "korean"
    native_col = 1
    rom_col = 0
    native_label = "Korean"
    rom_label = "Romanization"

trans_col = header.index("translation") if "translation" in header else len(rows[0]) - 1

verses = []
for row in rows[1:]:
    if len(row) <= max(native_col, rom_col, trans_col):
        continue
    native = row[native_col].strip()
    rom = row[rom_col].strip()
    trans = row[trans_col].strip()
    if native or rom:
        verses.append({"native": native, "romanization": rom, "translation": trans})

print(f"Detected language: {lang}")
print(f"Loaded {len(verses)} verses from {args.input}")

# ── Build prompt based on language ───────────────────────────────────────────

if lang == "chinese":
    SYSTEM_PROMPT = """You are a Chinese linguistics assistant that creates word-by-word glosses.

For each verse you receive, break down EVERY word. Return a JSON array of objects:
[
  {"chinese": "想", "pinyin": "xiǎng", "english": "want to / think"},
  {"chinese": "听", "pinyin": "tīng", "english": "listen"},
  ...
]

Rules:
- Break compound words into meaningful units where helpful for learners
- Use the pinyin provided — do NOT re-romanize differently
- Include grammar notes in parentheses for particles, measure words, and structural words (e.g. 的: possessive/attributive, 了: completion aspect)
- Keep words in the same order as the verse
- For English words, include them as-is
- Return ONLY the JSON array, no markdown, no explanation"""

    def make_prompt(i, verse):
        return f"""Verse {i+1}:

Chinese:
{verse['native']}

Pinyin:
{verse['romanization']}

Translation:
{verse['translation']}"""

    json_keys = ("chinese", "pinyin", "english")
    csv_header = ["Chinese", "Pinyin", "English meaning"]

else:
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

    def make_prompt(i, verse):
        return f"""Verse {i+1}:

Korean:
{verse['native']}

Romanization:
{verse['romanization']}

Translation:
{verse['translation']}"""

    json_keys = ("korean", "romanization", "english")
    csv_header = ["Korean", "Romanization", "English meaning"]

# ── Gloss each verse ─────────────────────────────────────────────────────────

all_glosses = []

for i, verse in enumerate(verses):
    prompt = make_prompt(i, verse)
    print(f"\nVerse {i+1}/{len(verses)}: {verse['native'][:40]}...")

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

    time.sleep(0.5)

# ── Write output CSV ─────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(csv_header)
    for glosses in all_glosses:
        for g in glosses:
            writer.writerow([g.get(k, "") for k in json_keys])

total_words = sum(len(g) for g in all_glosses)
print(f"\nDone! Wrote {total_words} gloss rows to {args.output}")
