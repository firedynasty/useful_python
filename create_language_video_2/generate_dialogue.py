"""
generate_dialogue.py

Loads HSK vocabulary from JSON files, splits a level into lesson batches,
and calls OpenAI to generate a natural dialogue focusing on those words.

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_dialogue.py --level 3 --lesson 2 --output dialogue.txt
"""

import argparse
import json
import math
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--level", type=int, required=True, help="HSK level (1-7)")
parser.add_argument("--lesson", type=int, required=True, help="Lesson number within level")
parser.add_argument("--lessons_per_level", type=int, default=10, help="How many lessons to split each level into")
parser.add_argument("--vocab_dir", default="complete-hsk-vocabulary/wordlists/exclusive/newest",
                    help="Path to HSK vocab JSONs")
parser.add_argument("--output", default="dialogue.txt", help="Output dialogue file")
parser.add_argument("--model", default="gpt-4o", help="OpenAI model for generation")
args = parser.parse_args()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key)

# ── Load target level vocab ────────────────────────────────────────────────

vocab_file = os.path.join(args.vocab_dir, f"{args.level}.json")
if not os.path.exists(vocab_file):
    print(f"Error: {vocab_file} not found")
    sys.exit(1)

with open(vocab_file, "r", encoding="utf-8") as f:
    level_words = json.load(f)

# Sort by frequency (lower number = more common word)
level_words.sort(key=lambda w: w.get("frequency", 99999))

# ── Split into lesson batches ──────────────────────────────────────────────

total_lessons = min(args.lessons_per_level, len(level_words))
batch_size = math.ceil(len(level_words) / total_lessons)
start = (args.lesson - 1) * batch_size
end = min(start + batch_size, len(level_words))

if start >= len(level_words):
    print(f"Error: Lesson {args.lesson} out of range (level {args.level} has {total_lessons} lessons)")
    sys.exit(1)

batch = level_words[start:end]

# ── Format focus words for the prompt ──────────────────────────────────────

focus_lines = []
for w in batch:
    simplified = w["simplified"]
    form = w["forms"][0]
    pinyin = form["transcriptions"]["pinyin"]
    meanings = "; ".join(form["meanings"][:2]) if form["meanings"] else ""
    focus_lines.append(f"  {simplified} ({pinyin}) — {meanings}")

focus_list = "\n".join(focus_lines)

# ── Generate dialogue ──────────────────────────────────────────────────────

prompt = f"""Write a natural Mandarin Chinese conversation between two people.

The conversation MUST practice these HSK {args.level} vocabulary words (this is lesson {args.lesson} of {total_lessons}):

{focus_list}

Rules:
- Use as many of the listed words as naturally possible (aim for at least 70%)
- Only use vocabulary appropriate for HSK level {args.level} or below
- Format each exchange as an A/P/B triplet:
  A: Chinese characters
  P: Pinyin with tone marks (ā á ǎ à, ē é ě è, etc.)
  B: English translation
- Group into [Scene 1], [Scene 2], etc. with 3-5 scenes
- 15-20 exchanges total
- Keep lines short and conversational
- Make the conversation feel natural — a real situation two people might be in
- Pinyin MUST use tone marks (e.g. māma, not mama)

Example format:
[Scene 1]
A: 你好！今天天气很好。
P: Nǐ hǎo! Jīntiān tiānqì hěn hǎo.
B: Hello! The weather is nice today.

A: 是啊，我们去公园吧。
P: Shì a, wǒmen qù gōngyuán ba.
B: Yeah, let's go to the park."""

print(f"HSK {args.level} · Lesson {args.lesson}/{total_lessons} · {len(batch)} focus words")
print(f"Generating dialogue with {args.model}...")

response = client.chat.completions.create(
    model=args.model,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a Mandarin Chinese language teaching assistant. "
                "Generate natural, realistic dialogues that help learners practice specific vocabulary. "
                "Always output the dialogue directly — no preamble, no commentary, no markdown fences."
            ),
        },
        {"role": "user", "content": prompt},
    ],
    temperature=0.8,
)

dialogue = response.choices[0].message.content.strip()

# Strip markdown fences if the model wraps output
if dialogue.startswith("```"):
    dialogue = dialogue.split("\n", 1)[-1]
    dialogue = dialogue.rsplit("```", 1)[0].strip()

# Prepend title
header = f"# HSK {args.level} — Lesson {args.lesson}/{total_lessons}\n\n---\n"
dialogue = header + "\n" + dialogue + "\n"

os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
with open(args.output, "w", encoding="utf-8") as f:
    f.write(dialogue)

print(f"Wrote: {args.output} ({len(dialogue.splitlines())} lines)")
