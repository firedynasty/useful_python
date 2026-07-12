"""
local_merge.py

1. Flatten the HTML lyrics table into individual lines: (translation, romanization, korean)
2. For each gloss group in the CSV, take the LAST word's romanization
3. Find which lyric line's romanization contains that last word → that's the match

If OPENAI_API_KEY is set, runs a verification pass with GPT to double-check.

Usage:
  python local_merge.py --gloss "korean - Sheet1.csv" --html lyrics_grouped_table.html --output korean_output.csv
"""

import argparse
import csv
import json
import os
import re
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("--gloss", required=True, help="Path to gloss CSV file")
parser.add_argument("--html", required=True, help="Path to HTML lyrics table file")
parser.add_argument("--output", default="korean_output.csv", help="Path for output CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model for verification")
args = parser.parse_args()

# ── Step 1: Flatten HTML into individual lyric lines ─────────────────────────

with open(args.html, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

table = soup.find("table")
lyric_lines = []  # flat list: {translation, romanization, korean}

for tr in table.find("tbody").find_all("tr"):
    cells = tr.find_all("td")
    if len(cells) < 3:
        continue
    rom_lines = cells[0].get_text(separator="\n", strip=True).split("\n")
    kor_lines = cells[1].get_text(separator="\n", strip=True).split("\n")
    trans_lines = cells[2].get_text(separator="\n", strip=True).split("\n")
    max_len = max(len(rom_lines), len(kor_lines), len(trans_lines))
    rom_lines += [""] * (max_len - len(rom_lines))
    kor_lines += [""] * (max_len - len(kor_lines))
    trans_lines += [""] * (max_len - len(trans_lines))
    for r, k, t in zip(rom_lines, kor_lines, trans_lines):
        lyric_lines.append({
            "translation": t.strip(),
            "romanization": r.strip(),
            "korean": k.strip(),
        })

print(f"Step 1: Flattened HTML → {len(lyric_lines)} lyric lines")
print("  Format: translation | romanization")
for i, ll in enumerate(lyric_lines):
    print(f"  [{i:2d}] {ll['translation'][:50]:50s} | {ll['romanization'][:50]}")

# ── Step 2: Parse gloss CSV into groups ──────────────────────────────────────

with open(args.gloss, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))

rows = reader[1:]  # skip header

section_headers = {"Verse 1", "Verse 2", "Pre-Chorus", "Chorus", "Bridge", "Outro"}

def has_korean(text):
    return bool(re.search(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]', text))

def is_section_header(row):
    return row[0].strip() in section_headers and not row[1].strip() and not row[2].strip()

def is_empty_row(row):
    return all(not c.strip() for c in row)

def is_word_gloss(row):
    return has_korean(row[0].strip()) and row[1].strip()

groups = []
i = 0
while i < len(rows):
    row = rows[i]
    if is_empty_row(row) or is_section_header(row):
        if is_section_header(row):
            groups.append({"type": "section", "name": row[0].strip()})
        i += 1
        continue

    col0, col1, col2 = row[0].strip(), row[1].strip(), row[2].strip()

    if not has_korean(col0) and not is_word_gloss(row):
        translation = col0
        romanization_line = ""
        # Check if next row is the romanization line
        if i + 1 < len(rows):
            nr = rows[i + 1]
            if not has_korean(nr[0].strip()) and not nr[1].strip() and not nr[2].strip() and nr[0].strip():
                romanization_line = nr[0].strip()
                i += 2
            else:
                i += 1
        else:
            i += 1
        # Collect word glosses
        words = []
        while i < len(rows) and is_word_gloss(rows[i]):
            w = rows[i]
            words.append({"korean": w[0].strip(), "romanization": w[1].strip(), "english": w[2].strip()})
            i += 1
        if words:
            groups.append({"type": "gloss_group", "translation": translation,
                           "romanization_line": romanization_line, "words": words})
        continue

    if is_word_gloss(row):
        groups.append({"type": "gloss_group", "translation": "", "romanization_line": "",
                       "words": [{"korean": col0, "romanization": col1, "english": col2}]})
        i += 1
        continue
    i += 1

gloss_count = sum(1 for g in groups if g.get("type") == "gloss_group")
print(f"\nStep 2: Parsed CSV → {gloss_count} gloss groups")

# ── Step 3: Match by last romanization word ──────────────────────────────────

def find_by_last_rom(words, lyric_lines):
    """Find the lyric line whose romanization contains the last word's romanization."""
    if not words:
        return None

    last_rom = words[-1]["romanization"].lower().strip()
    if not last_rom:
        return None

    # Search for the lyric line containing the last romanization word
    for ll in lyric_lines:
        rom = ll["romanization"].lower()
        if last_rom in rom:
            return ll

    # Fallback: try matching by first word if last didn't work
    first_rom = words[0]["romanization"].lower().strip()
    if first_rom:
        for ll in lyric_lines:
            rom = ll["romanization"].lower()
            if first_rom in rom:
                return ll

    return None

print("\nStep 3: Matching each group by last romanization word...")
matches = {}  # group_index -> lyric_line
group_idx = 0
for g in groups:
    if g.get("type") != "gloss_group":
        continue
    last_word = g["words"][-1]["romanization"]
    match = find_by_last_rom(g["words"], lyric_lines)
    status = f"→ {match['romanization'][:40]}" if match else "→ NO MATCH"
    print(f"  Group {group_idx}: last_rom=\"{last_word}\" {status}")
    matches[group_idx] = match
    group_idx += 1

# ── Step 4: Build output CSV ─────────────────────────────────────────────────

output_rows = []
group_idx = 0

for g in groups:
    if g["type"] == "section":
        output_rows.append({"Korean": g["name"], "Romanization": "", "English meaning": "",
                            "Matched Lyric (Korean)": "", "Matched Lyric (Romanization)": "",
                            "Matched Lyric (Translation)": ""})
        continue
    if g["type"] != "gloss_group":
        continue

    match = matches.get(group_idx)
    matched_kor = match["korean"] if match else ""
    matched_rom = match["romanization"] if match else ""
    matched_trans = match["translation"] if match else ""

    if g["translation"]:
        output_rows.append({"Korean": "", "Romanization": "", "English meaning": g["translation"],
                            "Matched Lyric (Korean)": matched_kor,
                            "Matched Lyric (Romanization)": matched_rom,
                            "Matched Lyric (Translation)": matched_trans})
    if g["romanization_line"]:
        output_rows.append({"Korean": "", "Romanization": g["romanization_line"], "English meaning": "",
                            "Matched Lyric (Korean)": "", "Matched Lyric (Romanization)": "",
                            "Matched Lyric (Translation)": ""})
    for w in g["words"]:
        output_rows.append({"Korean": w["korean"], "Romanization": w["romanization"],
                            "English meaning": w["english"],
                            "Matched Lyric (Korean)": "", "Matched Lyric (Romanization)": "",
                            "Matched Lyric (Translation)": ""})
    group_idx += 1

fieldnames = ["Korean", "Romanization", "English meaning",
              "Matched Lyric (Korean)", "Matched Lyric (Romanization)", "Matched Lyric (Translation)"]

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"\nLocal matching done! Output saved to: {args.output}")
print(f"Total rows: {len(output_rows)}")

# ── Step 5: Optional GPT verification ────────────────────────────────────────

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("\nNo OPENAI_API_KEY set — skipping GPT verification.")
    print("Set OPENAI_API_KEY to enable double-check of matches.")
else:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # Build summary of local matches
    local_matches = []
    group_idx = 0
    for g in groups:
        if g.get("type") != "gloss_group":
            continue
        match = matches.get(group_idx)
        local_matches.append({
            "group_index": group_idx,
            "translation": g["translation"],
            "last_rom_word": g["words"][-1]["romanization"],
            "all_rom_words": [w["romanization"] for w in g["words"]],
            "matched_lyric_rom": match["romanization"] if match else None,
            "matched_lyric_trans": match["translation"] if match else None,
        })
        group_idx += 1

    verify_prompt = f"""You are a Korean lyrics verification assistant.

I matched gloss word groups to lyric lines by finding the lyric line whose
romanization contains the LAST word's romanization from each group.

Please verify each match is correct. A match is correct if the gloss words
actually belong to that lyric line.

LOCAL MATCHES:
{json.dumps(local_matches, ensure_ascii=False, indent=2)}

ALL LYRIC LINES (for reference):
{json.dumps(lyric_lines, ensure_ascii=False, indent=2)}

Return a JSON array with one object per group:
[
  {{
    "group_index": 0,
    "local_match_correct": true/false,
    "correct_lyric_rom": "..." or null,
    "note": "optional explanation if wrong"
  }},
  ...
]

Only raw JSON, no markdown."""

    print("\nStep 5: Verifying matches with GPT...")
    response = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": verify_prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]

    try:
        verification = json.loads(raw)
    except json.JSONDecodeError:
        print("WARNING: GPT returned invalid JSON for verification.")
        print(raw[:500])
        verification = []

    mismatches = [v for v in verification if not v.get("local_match_correct")]
    if not mismatches:
        print(f"GPT verified all {len(verification)} matches are correct!")
    else:
        print(f"\nGPT found {len(mismatches)} mismatch(es):")
        for m in mismatches:
            print(f"  Group {m['group_index']}: last_rom matched wrong line")
            print(f"    Correct lyric: {m.get('correct_lyric_rom', 'unknown')}")
            if m.get("note"):
                print(f"    Note: {m['note']}")

        # Apply corrections
        corrections = {}
        for m in mismatches:
            idx = m["group_index"]
            correct_rom = m.get("correct_lyric_rom")
            if correct_rom:
                for ll in lyric_lines:
                    if ll["romanization"] == correct_rom:
                        corrections[idx] = ll
                        break

        if corrections:
            print("\nApplying corrections...")
            output_rows = []
            group_idx = 0
            for g in groups:
                if g["type"] == "section":
                    output_rows.append({"Korean": g["name"], "Romanization": "", "English meaning": "",
                                        "Matched Lyric (Korean)": "", "Matched Lyric (Romanization)": "",
                                        "Matched Lyric (Translation)": ""})
                    continue
                if g["type"] != "gloss_group":
                    continue

                match = corrections[group_idx] if group_idx in corrections else matches.get(group_idx)
                if group_idx in corrections:
                    print(f"  Fixed group {group_idx} → {match['romanization'][:40]}")

                matched_kor = match["korean"] if match else ""
                matched_rom = match["romanization"] if match else ""
                matched_trans = match["translation"] if match else ""

                if g["translation"]:
                    output_rows.append({"Korean": "", "Romanization": "", "English meaning": g["translation"],
                                        "Matched Lyric (Korean)": matched_kor,
                                        "Matched Lyric (Romanization)": matched_rom,
                                        "Matched Lyric (Translation)": matched_trans})
                if g["romanization_line"]:
                    output_rows.append({"Korean": "", "Romanization": g["romanization_line"], "English meaning": "",
                                        "Matched Lyric (Korean)": "", "Matched Lyric (Romanization)": "",
                                        "Matched Lyric (Translation)": ""})
                for w in g["words"]:
                    output_rows.append({"Korean": w["korean"], "Romanization": w["romanization"],
                                        "English meaning": w["english"],
                                        "Matched Lyric (Korean)": "", "Matched Lyric (Romanization)": "",
                                        "Matched Lyric (Translation)": ""})
                group_idx += 1

            with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(output_rows)
            print(f"\nCorrected output saved to: {args.output}")

    print("\nVerification complete.")
