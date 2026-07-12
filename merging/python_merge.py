"""
gloss_inserter.py

Takes:
  - A gloss CSV  (columns: korean, romanization, gloss_english, line_id or similar)
  - An HTML lyrics table (columns: Romanization, Korean, Translation)

Uses OpenAI GPT to match gloss rows to the correct lyric lines,
then outputs a merged CSV.

Usage:
  python gloss_inserter.py --gloss gloss.csv --html lyrics.html --output output.csv

Requirements:
  pip install openai pandas beautifulsoup4
"""

import argparse
import csv
import json
import os
import pandas as pd
from bs4 import BeautifulSoup
from openai import OpenAI

# ── CLI args ──────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--gloss", required=True, help="Path to gloss CSV file")
parser.add_argument("--html",  required=True, help="Path to HTML lyrics table file")
parser.add_argument("--output", default="output.csv", help="Path for output CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use")
args = parser.parse_args()

# ── OpenAI client ─────────────────────────────────────────────────────────────

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Export it first:\n"
        "  export OPENAI_API_KEY=sk-..."
    )

client = OpenAI(api_key=api_key)

# ── Parse HTML table ──────────────────────────────────────────────────────────

print(f"Reading HTML table from: {args.html}")
with open(args.html, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

rows = []
table = soup.find("table")
if not table:
    raise ValueError("No <table> found in the HTML file.")

headers = [th.get_text(strip=True) for th in table.find_all("th")]
print(f"  Found headers: {headers}")

for tr in table.find("tbody").find_all("tr"):
    cells = tr.find_all("td")
    if len(cells) >= 3:
        rows.append({
            "romanization": cells[0].get_text(separator="\n", strip=True),
            "korean":       cells[1].get_text(separator="\n", strip=True),
            "translation":  cells[2].get_text(separator="\n", strip=True),
        })

print(f"  Found {len(rows)} lyric rows.")

# ── Parse gloss CSV ───────────────────────────────────────────────────────────

print(f"\nReading gloss CSV from: {args.gloss}")
gloss_df = pd.read_csv(args.gloss)
print(f"  Columns: {list(gloss_df.columns)}")
print(f"  Rows: {len(gloss_df)}")

# Serialise the gloss data as a compact JSON string to pass to GPT
gloss_json = gloss_df.to_json(orient="records", force_ascii=False)

# ── Build prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Korean linguistics assistant.
You will be given:
  1. A list of lyric lines (each with romanization, korean, translation).
  2. A list of gloss records (each with a korean word/morpheme, its romanization,
     and its English gloss).

Your task:
  For each lyric line, collect all the gloss records that belong to that line
  and format them as a single readable string in this style:

    별(byeol=star) 이라도(irado=even/at least) 그렇게(geureoke=like that) 보였을까(boyeosseulkka=would it have appeared?)

Rules:
  - Match gloss records to lines by checking if the korean word appears in the
    korean text of that line.
  - Preserve the word order of the lyric line when ordering the glosses.
  - If a gloss record cannot be matched to any line, assign it to line index -1.
  - Return ONLY a JSON array with one object per lyric line, like:
    [
      { "line_index": 0, "gloss_string": "..." },
      { "line_index": 1, "gloss_string": "..." },
      ...
    ]
  - No markdown, no explanation — raw JSON only.
"""

USER_PROMPT = f"""
LYRIC LINES:
{json.dumps(rows, ensure_ascii=False, indent=2)}

GLOSS RECORDS:
{gloss_json}
"""

# ── Call GPT ──────────────────────────────────────────────────────────────────

print(f"\nCalling {args.model} to match glosses to lyric lines...")
response = client.chat.completions.create(
    model=args.model,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_PROMPT},
    ],
    temperature=0,
)

raw = response.choices[0].message.content.strip()

# Strip markdown code fences if GPT adds them
if raw.startswith("```"):
    raw = raw.split("\n", 1)[-1]
    raw = raw.rsplit("```", 1)[0]

try:
    gloss_results = json.loads(raw)
except json.JSONDecodeError as e:
    print("ERROR: GPT returned invalid JSON.")
    print(raw[:500])
    raise e

print(f"  GPT matched glosses for {len(gloss_results)} lines.")

# ── Merge & write output CSV ──────────────────────────────────────────────────

gloss_map = {item["line_index"]: item["gloss_string"] for item in gloss_results}

output_rows = []
for i, row in enumerate(rows):
    output_rows.append({
        "line_index":   i,
        "romanization": row["romanization"],
        "korean":       row["korean"],
        "translation":  row["translation"],
        "gloss":        gloss_map.get(i, ""),
    })

output_df = pd.DataFrame(output_rows)
output_df.to_csv(args.output, index=False, encoding="utf-8-sig")

print(f"\nDone! Output saved to: {args.output}")
print(output_df[["line_index", "translation", "gloss"]].head(3).to_string())
