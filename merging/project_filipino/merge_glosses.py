"""
merge_glosses.py (Filipino)

Walks through lyric pairs (adjusted txt) and gloss rows
(preformatted csv) in order with two pointers.

For each pair:
  - Output english + filipino as 2 inserted rows
  - Consume gloss rows until hitting one whose filipino text matches
    the pair's LAST filipino word
  - If no match found, just output the 2 lines and move to next pair

Usage:
  python merge_glosses.py --adjusted filipino_adjusted.txt --gloss filipino_preformatted.csv --output filipino_output.csv
"""

import argparse
import csv
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument("--adjusted", required=True, help="Path to adjusted txt (from make_adjusted.py)")
parser.add_argument("--gloss", required=True, help="Path to gloss CSV (from generate_gloss.py)")
parser.add_argument("--output", default="filipino_output.csv", help="Path for output CSV")
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
    lyric_pairs.append({"english": english, "romanization": romanization, "rom_lower": romanization.lower()})
    i += 2
    if i < len(raw_lines) and raw_lines[i].strip() == "":
        i += 1

print(f"Loaded {len(lyric_pairs)} lyric pairs")

# ── Load preformatted CSV ───────────────────────────────────────────────────

with open(args.gloss, "r", encoding="utf-8-sig") as f:
    reader = list(csv.reader(f))

gloss_header = [h.strip().lower() for h in reader[0]]

native_col = gloss_header.index("filipino") if "filipino" in gloss_header else 0
eng_col = gloss_header.index("english meaning") if "english meaning" in gloss_header else 1
csv_header = ["Filipino", "English meaning"]

print(f"Detected language: Filipino")

rows = reader[1:]
section_headers = {"Verse 1", "Verse 2", "Pre-Chorus", "Chorus", "Bridge", "Outro"}

entries = []
for row in rows:
    if all(not c.strip() for c in row):
        continue
    if row[0].strip() in section_headers and (len(row) < 2 or not row[1].strip()):
        entries.append({"type": "section", "name": row[0].strip()})
    else:
        native = row[native_col].strip() if native_col < len(row) else ""
        eng = row[eng_col].strip() if eng_col < len(row) else ""
        entries.append({"type": "gloss", "native": native, "rom": native, "english": eng})

print(f"Loaded {sum(1 for e in entries if e['type'] == 'gloss')} gloss rows")

# ── Two-pointer walk ─────────────────────────────────────────────────────────

output_rows = []
ei = 0

for pair in lyric_pairs:
    rom_lower = pair["rom_lower"]

    while ei < len(entries) and entries[ei]["type"] == "section":
        output_rows.append([entries[ei]["name"], ""])
        ei += 1

    output_rows.append([pair["english"], ""])
    output_rows.append([pair["romanization"], ""])

    found_ahead = False
    for j in range(ei, len(entries)):
        if entries[j]["type"] == "gloss" and rom_lower.endswith(entries[j]["rom"].lower().strip()):
            found_ahead = True
            break

    if not found_ahead:
        continue

    while ei < len(entries):
        e = entries[ei]
        if e["type"] == "section":
            output_rows.append([e["name"], ""])
            ei += 1
            continue
        output_rows.append([e["native"], e["english"]])
        ei += 1
        if rom_lower.endswith(e["rom"].lower().strip()):
            break

while ei < len(entries):
    e = entries[ei]
    if e["type"] == "section":
        output_rows.append([e["name"], ""])
    else:
        output_rows.append([e["native"], e["english"]])
    ei += 1

# ── Write output CSV ─────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(csv_header)
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

    verify_prompt = f"""You are a Filipino/Tagalog lyrics verification assistant.

I matched word gloss groups to lyric lines. Each group starts with an English
translation line and a Filipino line, followed by word glosses.
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
