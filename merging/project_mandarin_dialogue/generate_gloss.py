"""
generate_gloss.py (Mandarin dialogue)

Reads a dialogue CSV and sends each turn to OpenAI GPT-4o
to generate a word-by-word gloss.

Speaker-label rows are skipped.

Output: a preformatted CSV with columns: Chinese, Pinyin, English meaning

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_gloss.py --input mandarin_dialogue_table.csv --output mandarin_dialogue_preformatted.csv
"""

import argparse
import csv
import json
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Path to dialogue CSV")
parser.add_argument("--output", default="mandarin_dialogue_preformatted.csv", help="Path for output gloss CSV")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
parser.add_argument("--limit", type=int, default=0, help="Only gloss first N turns (0 = all, for debugging)")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set. Export it first:\n  export OPENAI_API_KEY=sk-...")

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Read dialogue CSV ───────────────────────────────────────────────────────

with open(args.input, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = [h.strip().lower() for h in rows[0]]

native_col = header.index("chinese") if "chinese" in header else 0
rom_col = header.index("pinyin") if "pinyin" in header else 1
trans_col = header.index("translation") if "translation" in header else len(rows[0]) - 1

turns = []
for row in rows[1:]:
    if len(row) <= max(native_col, rom_col, trans_col):
        continue
    # Preserve speaker-label rows as markers
    if not row[rom_col].strip() and not row[trans_col].strip():
        speaker = row[0].strip()
        if speaker:
            turns.append({"type": "speaker", "name": speaker})
        continue
    native = row[native_col].strip()
    rom = row[rom_col].strip()
    trans = row[trans_col].strip()
    if native or rom:
        turns.append({"type": "turn", "native": native, "romanization": rom, "translation": trans})

actual_turns = [t for t in turns if t["type"] == "turn"]
print(f"Loaded {len(actual_turns)} dialogue turns from {args.input}")

# ── Build prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Mandarin Chinese linguistics assistant that creates word-by-word glosses for language learners.

For each dialogue turn you receive, break down EVERY word. Return a JSON array of objects:
[
  {"chinese": "你", "pinyin": "nǐ", "english": "you"},
  {"chinese": "好", "pinyin": "hǎo", "english": "good / well (greeting)"},
  ...
]

Rules:
- Break compound words into meaningful units where helpful for learners
- Use the pinyin provided — do NOT re-romanize differently
- Include grammar notes in parentheses for particles, measure words, and structural words (e.g. 的: possessive/attributive, 了: completion aspect, 吗: question particle)
- Keep words in the same order as the dialogue
- For filler words (呃, 嗯, 哇, etc.) include them with their meaning
- Return ONLY the JSON array, no markdown, no explanation"""

def make_prompt(i, turn):
    return f"""Turn {i+1}:

Chinese:
{turn['native']}

Pinyin:
{turn['romanization']}

Translation:
{turn['translation']}"""

# ── Gloss each turn ─────────────────────────────────────────────────────────
# all_results stores dicts: either {"type":"speaker","name":...} or {"type":"glosses","glosses":[...]}

all_results = []
turn_num = 0

for item in turns:
    if item["type"] == "speaker":
        all_results.append(item)
        continue

    turn_num += 1
    if args.limit and turn_num > args.limit:
        break
    prompt = make_prompt(turn_num, item)
    print(f"\nTurn {turn_num}/{len(actual_turns)}: {item['native'][:40]}...")

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
        print(f"  WARNING: Invalid JSON, skipping turn")
        print(f"  {raw[:200]}")
        all_results.append({"type": "glosses", "glosses": []})

    time.sleep(0.5)

# ── Write output CSV ─────────────────────────────────────────────────────────

with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer = csv.writer(f)
    writer.writerow(["Chinese", "Pinyin", "English meaning"])
    total_words = 0
    for item in all_results:
        if item["type"] == "speaker":
            writer.writerow([item["name"], "", ""])
        else:
            for g in item["glosses"]:
                writer.writerow([g.get("chinese", ""), g.get("pinyin", ""), g.get("english", "")])
            total_words += len(item["glosses"])

print(f"\nDone! Wrote {total_words} gloss rows to {args.output}")
