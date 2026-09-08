"""
translate_dialogue.py

Takes a plain English dialogue .txt file and calls OpenAI to produce
Chinese characters + Pinyin for each line, outputting the A/P/B triplet
format used by step1_tts.py.

Usage:
  export OPENAI_API_KEY=sk-...
  python translate_dialogue.py -i english_dialogue.txt -o dialogue.txt

Input file format — one English line per line, blank lines separate scenes:
  Thank you. Have a cigarette.
  No thanks, I don't smoke.

  This is Uncle Lee, this is my daughter Lily...

Output format (A/P/B triplets ready for the pipeline):
  [Scene 1]
  A: 谢谢。抽根烟吧。
  P: Xièxiè. Chōu gēn yān ba.
  B: Thank you. Have a cigarette.
"""

import argparse
import json
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="English dialogue .txt file")
parser.add_argument("-o", "--output", default="dialogue.txt", help="Output file (default: dialogue.txt)")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Read input file ────────────────────────────────────────────────────────────

with open(args.input, "r", encoding="utf-8") as f:
    raw = f.read()

# Split into scenes by blank lines; each scene is a list of English lines
raw_scenes = [block.strip() for block in raw.split("\n\n") if block.strip()]
scenes = []
for block in raw_scenes:
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if lines:
        scenes.append(lines)

total_lines = sum(len(s) for s in scenes)
print(f"Loaded {len(scenes)} scene(s), {total_lines} line(s) from {args.input}")

# ── Translate via OpenAI ───────────────────────────────────────────────────────

SYSTEM = (
    "You are a Mandarin Chinese translation assistant for language learners. "
    "You will receive English dialogue lines and return JSON with the translation and pinyin. "
    "Always use standard Simplified Chinese characters. "
    "Pinyin MUST use tone marks (ā á ǎ à, etc.), not numbers."
)

def translate_lines(english_lines: list[str]) -> list[dict]:
    """Translate a list of English lines, return list of {english, chinese, pinyin}."""
    numbered = "\n".join(f"{i+1}. {line}" for i, line in enumerate(english_lines))
    prompt = (
        f"Translate each numbered English line into Mandarin Chinese.\n\n"
        f"{numbered}\n\n"
        f"Return a JSON array with one object per line, in order:\n"
        f'[{{"english": "...", "chinese": "...", "pinyin": "..."}}, ...]\n\n'
        f"Rules:\n"
        f"- Keep the same number of objects as input lines\n"
        f"- chinese: Simplified Chinese characters\n"
        f"- pinyin: full sentence pinyin with tone marks, words separated by spaces\n"
        f"- english: the original English line (unchanged)\n"
        f"- Return ONLY the JSON array, no markdown, no explanation"
    )

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        content = content.rsplit("```", 1)[0].strip()

    return json.loads(content)

# ── Process all scenes ─────────────────────────────────────────────────────────

output_blocks = []

for scene_idx, scene_lines in enumerate(scenes, start=1):
    print(f"Translating scene {scene_idx}/{len(scenes)} ({len(scene_lines)} lines)...")
    translations = translate_lines(scene_lines)

    block_lines = [f"[Scene {scene_idx}]"]
    for t in translations:
        block_lines.append(f"A: {t['chinese']}")
        block_lines.append(f"P: {t['pinyin']}")
        block_lines.append(f"B: {t['english']}")
        block_lines.append("")  # blank line between exchanges

    output_blocks.append("\n".join(block_lines).rstrip())

output = "\n\n".join(output_blocks) + "\n"

# ── Write output ───────────────────────────────────────────────────────────────

with open(args.output, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nWrote: {args.output}")
print("\nPreview:")
print("-" * 40)
print("\n".join(output.splitlines()[:20]))
