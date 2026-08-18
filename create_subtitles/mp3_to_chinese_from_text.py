#!/usr/bin/env python3
"""
Take a .txt file of Chinese lines and output either:

  Default (no -g): three-line groups per input line
      Chinese text
      Pinyin
      English translation

  With -g: CSV gloss
      Chinese,Pinyin,English meaning   ← header
      Full sentence,,                  ← sentence row, B and C always empty
      word,pīnyīn,meaning              ← word-by-word rows

Usage:
    python mp3_to_chinese_from_text.py -i input.txt
    python mp3_to_chinese_from_text.py -i input.txt -o output.txt
    python mp3_to_chinese_from_text.py -i input.txt -g
    python mp3_to_chinese_from_text.py -i input.txt -g -o output.csv

Requires: OPENAI_API_KEY env var
"""

import argparse
import json
import os
import time
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# Gloss mode
# ---------------------------------------------------------------------------

_GLOSS_PROMPT = (
    "Convert Chinese text into a CSV gloss with exactly 3 columns: Chinese, Pinyin, English meaning.\n\n"
    "There are TWO types of rows — follow these rules strictly:\n\n"
    "TYPE 1 — Sentence row (one per sentence):\n"
    "  Column A: the full sentence\n"
    "  Column B: LEAVE EMPTY\n"
    "  Column C: LEAVE EMPTY\n"
    "  Example: 你好吗,,\n\n"
    "TYPE 2 — Word rows (one per word/phrase, immediately after its sentence row):\n"
    "  Column A: the word or phrase\n"
    "  Column B: pinyin WITH tone marks\n"
    "  Column C: English meaning\n"
    "  Example: 你好,nǐ hǎo,hello\n"
    "  Example: 吗,ma,(question particle)\n\n"
    "Rules:\n"
    "- First row must be exactly: Chinese,Pinyin,English meaning\n"
    "- Every word row MUST have pinyin in column B and English in column C — never leave them empty\n"
    "- Only sentence rows have empty B and C\n"
    "- Use accurate pinyin with tone marks for every word row\n\n"
    "Output only the raw CSV, no code fences or extra explanation."
)


def gloss_to_csv(client, text):
    """Send Chinese text to GPT and return raw CSV string."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _GLOSS_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Default mode (line-by-line pinyin + translation)
# ---------------------------------------------------------------------------

def translate_batch(client, texts):
    """Return list of (pinyin, english) tuples for a batch of Chinese lines."""
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Chinese-to-English translator. "
                    "For each numbered Chinese line, return the pinyin (with tone marks) "
                    "and a natural English translation. "
                    'Return a JSON object with a "segments" array, one entry per input line, in order. '
                    'Each entry must have exactly two keys: "pinyin" and "english". '
                    'Example: {"segments": [{"pinyin": "nǐ hǎo", "english": "Hello"}, ...]}'
                ),
            },
            {"role": "user", "content": numbered},
        ],
    )
    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)
    segments = data.get("segments", [])
    return [(seg.get("pinyin", ""), seg.get("english", "")) for seg in segments]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert a Chinese .txt file — default: triplet txt; -g: CSV gloss"
    )
    parser.add_argument("-i", "--input", required=True, help="Input .txt file")
    parser.add_argument("-o", "--output", help="Output file (default name depends on mode)")
    parser.add_argument("-g", "--gloss", action="store_true",
                        help="Gloss mode: output CSV with sentence rows + word-by-word breakdown")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Lines per translation API call, default mode only (default: 20)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set.")
        return

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return

    stem = Path(input_path).stem
    parent = Path(input_path).parent
    client = OpenAI(api_key=api_key)

    # --- Gloss mode (-g) ---
    if args.gloss:
        output_path = args.output or str(parent / f"{stem}_gloss.csv")
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        print(f"Glossing {input_path}...")
        csv_text = gloss_to_csv(client, text)
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(csv_text + "\n")
        print(f"Done. Written to {output_path}")
        return

    # --- Default mode: line-by-line pinyin + translation ---
    output_path = args.output or str(parent / f"{stem}_pinyin.txt")

    with open(input_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    chinese_lines = [(i, line) for i, line in enumerate(lines) if line.strip()]
    blank_positions = {i for i, line in enumerate(lines) if not line.strip()}

    print(f"Read {len(lines)} total lines ({len(chinese_lines)} non-empty). Translating...")

    results = {}
    texts_only = [line for _, line in chinese_lines]
    batch_size = args.batch_size

    for i in range(0, len(texts_only), batch_size):
        batch_texts = texts_only[i : i + batch_size]
        batch_indices = [idx for idx, _ in chinese_lines[i : i + batch_size]]
        end = min(i + batch_size, len(texts_only))
        print(f"  Translating lines {i+1}–{end} of {len(texts_only)}...")
        pairs = translate_batch(client, batch_texts)
        while len(pairs) < len(batch_texts):
            pairs.append(("", ""))
        for orig_idx, (pinyin, english) in zip(batch_indices, pairs):
            results[orig_idx] = (pinyin, english)
        time.sleep(0.2)

    with open(output_path, "w", encoding="utf-8") as out:
        for i, line in enumerate(lines):
            if i in blank_positions:
                out.write("\n")
            else:
                pinyin, english = results.get(i, ("", ""))
                out.write(f"{line}\n")
                out.write(f"{pinyin}\n")
                out.write(f"{english}\n")
                out.write("\n")

    print(f"Done. Written to {output_path}")


if __name__ == "__main__":
    main()
