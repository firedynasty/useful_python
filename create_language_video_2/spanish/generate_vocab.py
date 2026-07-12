"""
generate_vocab.py

Builds CEFR-level Spanish vocabulary JSONs from a frequency list (es_50k.txt)
and uses OpenAI only for English translations + POS/gender tagging.

1. Parses es_50k.txt (hermitdave/FrequencyWords — OpenSubtitles frequency data)
2. Filters out junk (single letters, numbers)
3. Slices into CEFR tiers by frequency rank
4. Sends batches to OpenAI for translation + POS tagging
5. Saves vocab/A1.json through vocab/C2.json

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_vocab.py
  python generate_vocab.py --levels A1 A2    # just regenerate specific levels
"""

import argparse
import json
import os
import re
import sys
import time

ALL_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# How many words per CEFR level (cumulative slices of the frequency list)
# A1: words 1-300, A2: 301-700, B1: 701-1300, etc.
LEVEL_SIZES = {
    "A1": 300,
    "A2": 400,
    "B1": 600,
    "B2": 800,
    "C1": 1000,
    "C2": 1200,
}

TRANSLATE_BATCH = 50  # words per OpenAI translation call

parser = argparse.ArgumentParser()
parser.add_argument("--freq_file", default="es_50k.txt", help="Frequency list file")
parser.add_argument("--levels", nargs="+", default=ALL_LEVELS)
parser.add_argument("--output_dir", default="vocab")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model for translations")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key)

os.makedirs(args.output_dir, exist_ok=True)

# ── Parse and filter frequency list ───────────────────────────────────────

print(f"Reading {args.freq_file}...")

# Patterns to skip
SKIP_RE = re.compile(
    r"^\d+$"           # pure numbers
    r"|^.$"             # single characters
    r"|^-+$"            # dashes
    r"|[0-9]"           # anything with digits
)

words = []
seen = set()
with open(args.freq_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        word, freq = parts[0], int(parts[1])

        # Skip junk
        if SKIP_RE.match(word):
            continue
        # Skip if already seen (case-insensitive)
        key = word.lower()
        if key in seen:
            continue
        seen.add(key)

        words.append({"spanish": word, "frequency": freq})

print(f"  {len(words)} clean words after filtering")

# ── Slice into CEFR tiers ─────────────────────────────────────────────────

offset = 0
level_slices = {}
for level in ALL_LEVELS:
    size = LEVEL_SIZES[level]
    level_slices[level] = words[offset:offset + size]
    offset += size

print("\nLevel breakdown:")
for level in ALL_LEVELS:
    print(f"  {level}: {len(level_slices[level])} words")


# ── Translate + tag with OpenAI ───────────────────────────────────────────

def translate_batch(spanish_words):
    """Send a batch of Spanish words to OpenAI for translation + POS + gender."""

    word_list = "\n".join(f"  {i+1}. {w}" for i, w in enumerate(spanish_words))

    prompt = f"""For each Spanish word below, provide: English translation, part of speech, and gender (for nouns).

{word_list}

Return ONLY a JSON array in this exact format, one entry per word, same order:
[
  {{"spanish": "casa", "english": "house; home", "pos": "noun", "gender": "f"}},
  {{"spanish": "hablar", "english": "to speak; to talk", "pos": "verb", "gender": null}},
  {{"spanish": "grande", "english": "big; tall; great", "pos": "adjective", "gender": null}}
]

Rules:
- "pos" should be one of: noun, verb, adjective, adverb, pronoun, preposition, conjunction, interjection, determiner, particle
- "gender" is "m" or "f" for nouns, null for everything else
- Keep translations concise (2-3 meanings max, separated by semicolons)
- No markdown fences, no commentary"""

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "system",
                "content": "You are a Spanish-English translator. Return only valid JSON arrays.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0].strip()

    return json.loads(raw)


for level in ALL_LEVELS:
    if level not in args.levels:
        print(f"\nSkipping {level}")
        continue

    path = os.path.join(args.output_dir, f"{level}.json")
    if os.path.exists(path):
        print(f"\nSkipping {level} (already exists — delete {path} to regenerate)")
        continue

    sl = level_slices[level]
    if not sl:
        print(f"\nSkipping {level} (no words)")
        continue

    print(f"\n{'='*40}")
    print(f"  CEFR {level} — translating {len(sl)} words")
    print(f"{'='*40}")

    all_translated = []

    for i in range(0, len(sl), TRANSLATE_BATCH):
        batch = sl[i:i + TRANSLATE_BATCH]
        batch_words = [w["spanish"] for w in batch]
        batch_freqs = {w["spanish"].lower(): w["frequency"] for w in batch}

        print(f"  Translating words {i+1}–{i+len(batch)}...")

        translated = translate_batch(batch_words)

        # Merge frequency back in
        for t in translated:
            t["frequency"] = batch_freqs.get(t["spanish"].lower(), 0)
            all_translated.append(t)

        time.sleep(0.3)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_translated, f, ensure_ascii=False, indent=2)
    print(f"  Wrote: {path} ({len(all_translated)} words)")

print(f"\nDone! Vocab files in {args.output_dir}/")
