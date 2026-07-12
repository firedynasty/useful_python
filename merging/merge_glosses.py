"""
merge_glosses.py

Walks through lyric pairs (adjusted txt) and gloss rows
(preformatted csv) in order with two pointers.

For each pair:
  - Output english + romanization (2 lines)
  - Consume gloss rows until hitting one whose romanization matches
    the pair's LAST romanization word
  - If no match found, just output the 2 lines and move to next pair
    (CSV pointer stays where it is)

Usage:
  python merge_glosses.py --adjusted celebrity_adjusted.txt --gloss celebrity_preformatted.csv --output celebrity_output.csv
"""

import argparse
import csv
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument("--adjusted", default="korean_table_adjusted.txt", help="Path to adjusted txt (from make_adjusted.py)")
parser.add_argument("--gloss", default="korean -preformatted.csv", help="Path to gloss CSV (from generate_gloss.py)")
parser.add_argument("--output", default="korean_output.csv", help="Path for output CSV")
args = parser.parse_args()

# ── Load lyric pairs ─────────────────────────────────────────────────────────

with open(args.adjusted, "r", encoding="utf-8") as f:
    raw_lines = f.read().strip().split("\n")

lyric_pairs = []
i = 0
while i < len(raw_lines):
    if raw_lines[i].strip() == "":
        i += 1
        continue
    english = raw_lines[i].strip()
    romanization = raw_lines[i + 1].strip() if i + 1 < len(raw_lines) else ""
    words = romanization.split()
    last_word = words[-1].lower() if words else ""
    lyric_pairs.append({"english": english, "romanization": romanization, "last_word": last_word})
    i += 2
    if i < len(raw_lines) and raw_lines[i].strip() == "":
        i += 1

print(f"Loaded {len(lyric_pairs)} lyric pairs")

# ── Load preformatted CSV ────────────────────────────────────────────────────

with open(args.gloss, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))

rows = reader[1:]
section_headers = {"Verse 1", "Verse 2", "Pre-Chorus", "Chorus", "Bridge", "Outro"}

entries = []
for row in rows:
    if all(not c.strip() for c in row):
        continue
    if row[0].strip() in section_headers and not row[1].strip() and not row[2].strip():
        entries.append({"type": "section", "name": row[0].strip()})
    else:
        entries.append({"type": "gloss", "korean": row[0].strip(),
                        "rom": row[1].strip(), "english": row[2].strip()})

print(f"Loaded {sum(1 for e in entries if e['type'] == 'gloss')} gloss rows")

# ── Two-pointer walk ─────────────────────────────────────────────────────────

output_rows = []  # list of [col1, col2, col3]
ei = 0  # entries index (CSV pointer)

for pair in lyric_pairs:
    last_word = pair["last_word"]

    # Emit any section headers at current position
    while ei < len(entries) and entries[ei]["type"] == "section":
        output_rows.append([entries[ei]["name"], "", ""])
        ei += 1

    # Always insert the pair as 2 new rows in column 1
    output_rows.append([pair["english"], "", ""])
    output_rows.append([pair["romanization"], "", ""])

    # Peek ahead: does last_word exist in upcoming gloss rows?
    found_ahead = False
    for j in range(ei, len(entries)):
        if entries[j]["type"] == "gloss" and entries[j]["rom"].lower().strip() == last_word:
            found_ahead = True
            break

    if not found_ahead:
        # No matching glosses — 2 lines inserted, pointer stays, next pair follows
        continue

    # Consume gloss rows until we hit the last word
    while ei < len(entries):
        e = entries[ei]
        if e["type"] == "section":
            output_rows.append([e["name"], "", ""])
            ei += 1
            continue
        output_rows.append([e["korean"], e["rom"], e["english"]])
        ei += 1
        if e["rom"].lower().strip() == last_word:
            break

# Emit any remaining entries
while ei < len(entries):
    e = entries[ei]
    if e["type"] == "section":
        output_rows.append([e["name"], "", ""])
    else:
        output_rows.append([e["korean"], e["rom"], e["english"]])
    ei += 1

# ── Write output CSV ─────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Korean", "Romanization", "English meaning"])
    writer.writerows(output_rows)

print(f"\nDone! Output saved to: {args.output}")
print(f"Total rows: {len(output_rows)}")

# ── Optional: GPT verification ───────────────────────────────────────────────

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("\nNo OPENAI_API_KEY — skipping GPT verification.")
else:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    verify_prompt = f"""You are a Korean lyrics verification assistant.

I matched word gloss groups to lyric lines. Each group starts with an English
translation line and a romanization line, followed by tab-separated word glosses.
Some pairs have no glosses (just 2 lines back to back).

Here is the full output:

{chr(10).join(','.join(r) for r in output_rows)}

Verify: do the gloss words under each lyric line actually belong to that line?
Report mismatches as JSON:
[
  {{"group_english": "...", "issue": "..."}}
]
If all correct, return: []
Only raw JSON, no markdown."""

    print("\nVerifying with GPT...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": verify_prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    try:
        issues = json.loads(raw)
        if not issues:
            print("GPT verified all matches are correct!")
        else:
            print(f"GPT found {len(issues)} issue(s):")
            for iss in issues:
                print(f"  {iss.get('group_english', '?')}: {iss.get('issue', '?')}")
    except json.JSONDecodeError:
        print("GPT returned invalid JSON:")
        print(raw[:500])
