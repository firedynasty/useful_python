"""
step3_gloss.py

Reads dialogue.txt, sends each line to OpenAI for word-by-word gloss,
outputs gloss_output.csv.

Language settings (gloss prompt, column names, field keys) imported from language.py.

Usage:
  export OPENAI_API_KEY=sk-...
  python step3_gloss.py --input dialogue.txt --output output/gloss_output.csv
"""

import argparse
import csv
import json
import os
import re
import sys
import time

from language import LANGUAGE_NAME, GLOSS_PROMPT, GLOSS_COLUMNS, TARGET_FIELD

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="dialogue.txt", help="Path to dialogue txt")
parser.add_argument("--output", default="output/gloss_output.csv", help="Path for output CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Parse dialogue ──────────────────────────────────────────────────────────

with open(args.input, "r", encoding="utf-8") as f:
    raw = f.read().strip().split("\n")

section_pattern = re.compile(r"^\[(.+)\]$")
a_pattern = re.compile(r"^A:\s*(.+)$")
b_pattern = re.compile(r"^B:\s*(.+)$")

# A: is always target language, B: is always English translation
entries = []
i = 0
while i < len(raw):
    line = raw[i].strip()
    if not line:
        i += 1
        continue
    m = section_pattern.match(line)
    if m:
        entries.append({"type": "section", "name": m.group(1)})
        i += 1
        continue
    ma = a_pattern.match(line)
    if ma and i + 1 < len(raw):
        mb = b_pattern.match(raw[i + 1].strip())
        if mb:
            entries.append({
                "type": "line",
                TARGET_FIELD: ma.group(1),
                "english": mb.group(1),
            })
            i += 2
            continue
    i += 1

line_count = sum(1 for e in entries if e["type"] == "line")
print(f"Parsed {line_count} dialogue lines ({LANGUAGE_NAME})")

# ── Gloss each line ─────────────────────────────────────────────────────────

output_rows = []
line_num = 0

for entry in entries:
    if entry["type"] == "section":
        output_rows.append([entry["name"]] + [""] * (len(GLOSS_COLUMNS) - 1))
        continue

    line_num += 1
    print(f"  [{line_num}/{line_count}] {entry[TARGET_FIELD][:40]}...")

    # Insert english + target language header rows
    output_rows.append([entry["english"]] + [""] * (len(GLOSS_COLUMNS) - 1))
    output_rows.append([entry[TARGET_FIELD]] + [""] * (len(GLOSS_COLUMNS) - 1))

    prompt = f"""{LANGUAGE_NAME}:
{entry[TARGET_FIELD]}

English:
{entry['english']}"""

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": GLOSS_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    raw_resp = response.choices[0].message.content.strip()
    if raw_resp.startswith("```"):
        raw_resp = raw_resp.split("\n", 1)[-1]
        raw_resp = raw_resp.rsplit("```", 1)[0]

    try:
        glosses = json.loads(raw_resp)
        print(f"    Got {len(glosses)} words")
        for g in glosses:
            # Build row matching GLOSS_COLUMNS order
            # For Mandarin: [Chinese, Pinyin, English meaning]
            # For Cantonese: [Cantonese, Jyutping, English meaning]
            # For Filipino: [Filipino, English meaning]
            row = []
            for col in GLOSS_COLUMNS:
                col_lower = col.lower().replace(" ", "_")
                # Try to match column name to a key in the gloss dict
                matched = False
                for key in g:
                    if key.lower() == col_lower or col_lower.startswith(key.lower()):
                        row.append(g[key])
                        matched = True
                        break
                if not matched:
                    # Fallback: try common mappings
                    if col_lower == "english_meaning":
                        row.append(g.get("english", ""))
                    else:
                        row.append(g.get(col_lower, ""))
            output_rows.append(row)
    except json.JSONDecodeError:
        print(f"    WARNING: Invalid JSON, skipping")
        print(f"    {raw_resp[:200]}")

    time.sleep(0.5)

# ── Write CSV ───────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(GLOSS_COLUMNS)
    writer.writerows(output_rows)

print(f"\nDone! Wrote {len(output_rows)} rows to {args.output}")
