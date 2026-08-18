#!/usr/bin/env python3
"""
Take a .txt file of Korean lines and output either:

  Default (no -g): three-line groups per input line
      Korean text
      Romanization (Revised Romanization of Korean)
      English translation

  With -g: CSV gloss
      Korean,Romanization,English meaning   ← header
      Full sentence,,                        ← sentence row, B and C always empty
      word,romanization,meaning              ← word-by-word rows

Usage:
    python mp3_to_korean_from_text.py -i input.txt
    python mp3_to_korean_from_text.py -i input.txt -o output.txt
    python mp3_to_korean_from_text.py -i input.txt -g
    python mp3_to_korean_from_text.py -i input.txt -g -o output.csv

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
    "Convert these Korean sentence(s) into CSV with 3 columns: Korean, Romanization, English meaning.\n\n"
    "Format rules:\n"
    "- First row: `Korean,Romanization,English meaning`\n"
    "- Each dialogue exchange gets a header row like `Dialogue 1,,` (columns B and C empty)\n"
    "- Each sentence gets its OWN row with the full sentence in column A and columns B and C EMPTY\n"
    "- Immediately after the sentence row, add one row PER WORD OR PARTICLE with all 3 columns filled\n"
    "- Use accurate Revised Romanization of Korean\n\n"
    "CRITICAL: every sentence must appear TWICE — once as a sentence row (B and C empty), "
    "then broken into individual words below it. Do NOT skip the word-by-word breakdown.\n\n"
    "Output should look like:\n\n"
    "Korean,Romanization,English meaning\n"
    "Dialogue 1,,\n"
    "별이라도 그렇게 보였을까,,\n"
    "별,byeol,star\n"
    "이라도,irado,even / at least (particle)\n"
    "그렇게,geureoke,like that / in that way\n"
    "보였을까,boyeosseulkka,would it have appeared / looked?\n\n"
    "Output only the raw CSV text, no code fences or extra explanation."
)


def gloss_to_csv(client, text):
    """Send Korean text to GPT and return raw CSV string."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _GLOSS_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Default mode (line-by-line romanization + translation)
# ---------------------------------------------------------------------------

def translate_batch(client, texts):
    """Return list of (romanization, english) tuples for a batch of Korean lines."""
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Korean-to-English translator. "
                    "For each numbered Korean line, return the Revised Romanization of Korean "
                    "and a natural English translation. "
                    'Return a JSON object with a "segments" array, one entry per input line, in order. '
                    'Each entry must have exactly two keys: "romanization" and "english". '
                    'Example: {"segments": [{"romanization": "annyeonghaseyo", "english": "Hello"}, ...]}'
                ),
            },
            {"role": "user", "content": numbered},
        ],
    )
    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)
    segments = data.get("segments", [])
    return [(seg.get("romanization", ""), seg.get("english", "")) for seg in segments]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert a Korean .txt file — default: triplet txt; -g: CSV gloss"
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

    # --- Default mode: line-by-line romanization + translation ---
    output_path = args.output or str(parent / f"{stem}_romanized.txt")

    with open(input_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    korean_lines = [(i, line) for i, line in enumerate(lines) if line.strip()]
    blank_positions = {i for i, line in enumerate(lines) if not line.strip()}

    print(f"Read {len(lines)} total lines ({len(korean_lines)} non-empty). Translating...")

    results = {}
    texts_only = [line for _, line in korean_lines]
    batch_size = args.batch_size

    for i in range(0, len(texts_only), batch_size):
        batch_texts = texts_only[i : i + batch_size]
        batch_indices = [idx for idx, _ in korean_lines[i : i + batch_size]]
        end = min(i + batch_size, len(texts_only))
        print(f"  Translating lines {i+1}–{end} of {len(texts_only)}...")
        pairs = translate_batch(client, batch_texts)
        while len(pairs) < len(batch_texts):
            pairs.append(("", ""))
        for orig_idx, (romanization, english) in zip(batch_indices, pairs):
            results[orig_idx] = (romanization, english)
        time.sleep(0.2)

    with open(output_path, "w", encoding="utf-8") as out:
        for i, line in enumerate(lines):
            if i in blank_positions:
                out.write("\n")
            else:
                romanization, english = results.get(i, ("", ""))
                out.write(f"{line}\n")
                out.write(f"{romanization}\n")
                out.write(f"{english}\n")
                out.write("\n")

    print(f"Done. Written to {output_path}")


if __name__ == "__main__":
    main()
