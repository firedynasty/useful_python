"""
generate_gloss.py (Spanish)

Reads a lyrics CSV and sends each verse to OpenAI GPT-4o
to generate a word-by-word gloss.

Output: a preformatted CSV with columns: Spanish, English meaning

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_gloss.py --input spanish_table.csv --output spanish_preformatted.csv
"""

import argparse
import csv
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Path to lyrics CSV")
parser.add_argument("--output", default="spanish_preformatted.csv", help="Path for output gloss CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set. Export it first:\n  export OPENAI_API_KEY=sk-...")

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Read lyrics CSV ─────────────────────────────────────────────────────────

with open(args.input, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = [h.strip().lower() for h in rows[0]]

if "spanish" in header:
    native_col = header.index("spanish")
else:
    native_col = 0

trans_col = header.index("translation") if "translation" in header else len(rows[0]) - 1

verses = []
for row in rows[1:]:
    if len(row) <= max(native_col, trans_col):
        continue
    native = row[native_col].strip()
    trans = row[trans_col].strip()
    if native:
        verses.append({"native": native, "translation": trans})

print(f"Loaded {len(verses)} verses from {args.input}")

# ── Build prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Spanish linguistics assistant that creates word-by-word glosses for language learners.

For each verse you receive, break down EVERY word. Return a JSON array of objects:
[
  {"spanish": "Yo", "english": "I"},
  {"spanish": "sé", "english": "know (1st person singular, saber)"},
  {"spanish": "que", "english": "that (conjunction)"},
  ...
]

Rules:
- Include grammar notes in parentheses for conjugations, pronouns, and particles (e.g. verb tense, person, reflexive)
- Keep contractions together (e.g. "del" = "of the")
- Keep words in the same order as the verse
- For interjections or repeated syllables (e.g. "a-a-ay"), include them as-is
- Return ONLY the JSON array, no markdown, no explanation"""

def make_prompt(i, verse):
    return f"""Verse {i+1}:

Spanish:
{verse['native']}

Translation:
{verse['translation']}"""

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
    writer.writerow(["Spanish", "English meaning"])
    for glosses in all_glosses:
        for g in glosses:
            writer.writerow([g.get("spanish", ""), g.get("english", "")])

total_words = sum(len(g) for g in all_glosses)
print(f"\nDone! Wrote {total_words} gloss rows to {args.output}")
