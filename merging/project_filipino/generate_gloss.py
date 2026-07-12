"""
generate_gloss.py (Filipino)

Reads a lyrics CSV and sends each verse to OpenAI GPT-4o
to generate a word-by-word gloss.

Output: a preformatted CSV with columns: Filipino, English meaning

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_gloss.py --input filipino_table.csv --output filipino_preformatted.csv
"""

import argparse
import csv
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Path to lyrics CSV")
parser.add_argument("--output", default="filipino_preformatted.csv", help="Path for output gloss CSV")
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

if "filipino" in header:
    native_col = header.index("filipino")
else:
    native_col = 0

trans_col = header.index("translation") if "translation" in header else len(rows[0]) - 1

section_headers = {"Verse 1", "Verse 2", "Pre-Chorus", "Chorus", "Bridge", "Outro"}

verses = []
for row in rows[1:]:
    if len(row) <= max(native_col, trans_col):
        continue
    native = row[native_col].strip()
    trans = row[trans_col].strip()
    if native in section_headers and not trans:
        verses.append({"type": "section", "name": native})
    elif native:
        verses.append({"type": "verse", "native": native, "translation": trans})

verse_count = sum(1 for v in verses if v["type"] == "verse")
print(f"Loaded {verse_count} verses from {args.input}")

# ── Build prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Filipino/Tagalog linguistics assistant that creates word-by-word glosses for language learners.

For each verse you receive, break down EVERY word. Return a JSON array of objects:
[
  {"filipino": "Pilit", "english": "forcibly (adverb, from pilit 'force')"},
  {"filipino": "kong", "english": "my + linker (ko + -ng)"},
  {"filipino": "kinakaya", "english": "being endured (contemplative aspect, from kaya 'able')"},
  ...
]

Rules:
- Include grammar notes in parentheses for affixes, aspect, focus/voice, and linkers
- Note Tagalog verbal affixes and their meanings (e.g. mag-, -um-, naka-, in-, -an, i-)
- Note aspect where relevant (completed, contemplative, infinitive)
- Keep contractions/clipped forms together but explain them (e.g. "'Di" = "hindi, not")
- Handle common abbreviations: 'ko = ko, 'di = hindi, na'ng = na + ang, mo'y = mo + ay
- Keep words in the same order as the verse
- For interjections or vocables (e.g. "Woah", "ooh-woah"), include them as-is
- Return ONLY the JSON array, no markdown, no explanation"""

def make_prompt(i, verse):
    return f"""Verse {i+1}:

Filipino:
{verse['native']}

Translation:
{verse['translation']}"""

# ── Gloss each verse ─────────────────────────────────────────────────────────

all_results = []  # mix of {"type": "section"} and {"type": "glosses", "glosses": [...]}
verse_num = 0

for entry in verses:
    if entry["type"] == "section":
        all_results.append({"type": "section", "name": entry["name"]})
        continue

    verse_num += 1
    prompt = make_prompt(verse_num - 1, entry)
    print(f"\nVerse {verse_num}/{verse_count}: {entry['native'][:40]}...")

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
        all_results.append({"type": "glosses", "glosses": glosses})
    except json.JSONDecodeError:
        print(f"  WARNING: Invalid JSON, skipping verse")
        print(f"  {raw[:200]}")
        all_results.append({"type": "glosses", "glosses": []})

    time.sleep(0.5)

# ── Write output CSV ─────────────────────────────────────────────────────────

total_words = 0
with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Filipino", "English meaning"])
    for result in all_results:
        if result["type"] == "section":
            writer.writerow([result["name"], ""])
        else:
            for g in result["glosses"]:
                writer.writerow([g.get("filipino", ""), g.get("english", "")])
                total_words += 1

print(f"\nDone! Wrote {total_words} gloss rows to {args.output}")
