"""
convert_topik.py

Converts the combined_korean_vocabulary_list TSV into per-level JSON files
matching the structure that generate_dialogue.py expects.

Uses OpenAI to add English translations and romanization since the TSV
only has Korean explanations/hints.

Input:  combined_korean_vocabulary_list/results.tsv
Output: topik_vocab/A.json, topik_vocab/B.json, topik_vocab/C.json

Usage:
  export OPENAI_API_KEY=sk-...
  python convert_topik.py
  python convert_topik.py --levels A B    # just specific levels
"""

import argparse
import csv
import json
import os
import re
import sys
import time

ALL_LEVELS = ["A", "B", "C"]

parser = argparse.ArgumentParser()
parser.add_argument("--tsv", default="combined_korean_vocabulary_list/results.tsv",
                    help="Path to results.tsv")
parser.add_argument("--output_dir", default="topik_vocab", help="Output directory for JSONs")
parser.add_argument("--levels", nargs="+", default=ALL_LEVELS,
                    help="Which levels to generate (A, B, C)")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model for translations")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key)

os.makedirs(args.output_dir, exist_ok=True)

# ── Parse TSV ──────────────────────────────────────────────────────────────

print(f"Reading {args.tsv}...")

# Strip numeric suffixes from words (e.g. "가다01" -> "가다")
WORD_SUFFIX_RE = re.compile(r"\d+$")

level_words = {"A": [], "B": [], "C": []}
seen_per_level = {"A": set(), "B": set(), "C": set()}

with open(args.tsv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        topik_level = row.get("topik_level", "").strip()
        if topik_level not in ("A", "B", "C"):
            continue

        word = WORD_SUFFIX_RE.sub("", row["word"].strip())
        if not word:
            continue

        # Deduplicate by word within each level (same word can appear with
        # different POS entries)
        if word in seen_per_level[topik_level]:
            continue
        seen_per_level[topik_level].add(word)

        pos_ko = row.get("part_of_speech", "")
        hanja = row.get("hanja", "")
        explanation = row.get("explanation", "")
        rank = row.get("rank", "")
        rank_int = int(rank) if rank.isdigit() else 99999

        level_words[topik_level].append({
            "korean": word,
            "pos_korean": pos_ko,
            "hanja": hanja,
            "explanation": explanation,
            "frequency": rank_int,
        })

# Sort each level by frequency rank (lower = more common)
for lvl in ALL_LEVELS:
    level_words[lvl].sort(key=lambda w: w["frequency"])

print(f"\nLevel breakdown:")
for lvl in ALL_LEVELS:
    print(f"  TOPIK {lvl}: {len(level_words[lvl])} unique words")

# ── POS mapping (Korean -> English) ───────────────────────────────────────

POS_MAP = {
    "명사": "noun",
    "동사": "verb",
    "형용사": "adjective",
    "부사": "adverb",
    "대명사": "pronoun",
    "관형사": "determiner",
    "감탄사": "interjection",
    "수사": "numeral",
    "조사": "particle",
    "접사": "affix",
    "의존명사": "bound noun",
    "보조 용언": "auxiliary",
    "줄어든 말": "contraction",
    "고유 명사": "proper noun",
}


def translate_pos(pos_ko):
    """Map Korean POS to English. For compound POS like '동사/형용사', take first."""
    first = pos_ko.split("/")[0].strip()
    return POS_MAP.get(first, pos_ko)


# ── Translate with OpenAI ─────────────────────────────────────────────────

BATCH_SIZE = 50


def translate_batch(words):
    """Send a batch of Korean words to OpenAI for translation + romanization."""

    word_list = "\n".join(
        f"  {i+1}. {w['korean']}"
        + (f" ({w['hanja']})" if w["hanja"] else "")
        for i, w in enumerate(words)
    )

    prompt = f"""For each Korean word below, provide: English translation and romanization (Revised Romanization).

{word_list}

Return ONLY a JSON array in this exact format, one entry per word, same order:
[
  {{"korean": "집", "english": "house; home", "romanization": "jip"}},
  {{"korean": "말하다", "english": "to speak; to talk", "romanization": "malhada"}}
]

Rules:
- "romanization" should use Revised Romanization of Korean
- Keep translations concise (2-3 meanings max, separated by semicolons)
- For verbs, include "to" prefix (e.g. "to go; to leave")
- No markdown fences, no commentary"""

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "system",
                "content": "You are a Korean-English translator. Return only valid JSON arrays.",
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


for lvl in ALL_LEVELS:
    if lvl not in args.levels:
        print(f"\nSkipping TOPIK {lvl}")
        continue

    path = os.path.join(args.output_dir, f"{lvl}.json")
    if os.path.exists(path):
        print(f"\nSkipping TOPIK {lvl} (already exists — delete {path} to regenerate)")
        continue

    words = level_words[lvl]
    if not words:
        print(f"\nSkipping TOPIK {lvl} (no words)")
        continue

    print(f"\n{'='*40}")
    print(f"  TOPIK {lvl} — translating {len(words)} words")
    print(f"{'='*40}")

    all_translated = []

    for i in range(0, len(words), BATCH_SIZE):
        batch = words[i:i + BATCH_SIZE]

        print(f"  Translating words {i+1}–{i+len(batch)}...")

        try:
            translated = translate_batch(batch)
        except Exception as e:
            print(f"    ERROR: {e}, retrying in 5s...")
            time.sleep(5)
            translated = translate_batch(batch)

        # Merge original metadata with translations
        for j, t in enumerate(translated):
            orig = batch[j] if j < len(batch) else {}
            entry = {
                "korean": orig.get("korean", t.get("korean", "")),
                "english": t.get("english", ""),
                "romanization": t.get("romanization", ""),
                "pos": translate_pos(orig.get("pos_korean", "")),
                "hanja": orig.get("hanja", ""),
                "frequency": orig.get("frequency", 99999),
            }
            all_translated.append(entry)

        time.sleep(0.3)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_translated, f, ensure_ascii=False, indent=2)
    print(f"  Wrote: {path} ({len(all_translated)} words)")

print(f"\nDone! Vocab files in {args.output_dir}/")
