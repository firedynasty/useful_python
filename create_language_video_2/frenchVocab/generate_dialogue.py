"""
generate_dialogue.py

Loads French CEFR vocabulary from JSON files, splits a level into lesson
batches, and calls OpenAI to generate a natural dialogue focusing on those words.

Usage:
  export OPENAI_API_KEY=sk-...
  python generate_dialogue.py --level A2 --lesson 3 --output dialogue.txt
"""

import argparse
import json
import math
import os
import sys

ALL_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

parser = argparse.ArgumentParser()
parser.add_argument("--level", required=True, choices=ALL_LEVELS, help="CEFR level")
parser.add_argument("--lesson", type=int, required=True, help="Lesson number within level")
parser.add_argument("--lessons_per_level", type=int, default=10)
parser.add_argument("--vocab_dir", default="vocab", help="Path to vocab JSONs")
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
    print(f"Error: {vocab_file} not found. Run generate_vocab.py first.")
    sys.exit(1)

with open(vocab_file, "r", encoding="utf-8") as f:
    level_words = json.load(f)

# Already sorted by frequency from generate_vocab.py

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
    french = w["french"]
    english = w["english"]
    pos = w.get("pos", "")
    gender = w.get("gender")
    gender_str = f" ({gender}.)" if gender else ""
    focus_lines.append(f"  {french}{gender_str} [{pos}] — {english}")

focus_list = "\n".join(focus_lines)

# ── Generate dialogue ──────────────────────────────────────────────────────

prompt = f"""Write a natural French conversation between two people.

The conversation MUST practice these CEFR {args.level} vocabulary words (lesson {args.lesson} of {total_lessons}):

{focus_list}

Rules:
- Use as many of the listed words as naturally possible (aim for at least 70%)
- Only use vocabulary appropriate for CEFR level {args.level} or below
- Format each exchange as an A/B pair:
  A: French sentence
  B: English translation
- Group into [Scene 1], [Scene 2], etc. with 3-5 scenes
- 15-20 exchanges total
- Keep lines short and conversational
- Make the conversation feel natural — a real situation two people might be in
- Use natural spoken French (contractions, informal register where appropriate for the level)

Example format:
[Scene 1]
A: Bonjour ! Comment allez-vous aujourd'hui ?
B: Hello! How are you today?

A: Je vais bien, merci. Et vous ?
B: I'm doing well, thank you. And you?"""

print(f"CEFR {args.level} · Lesson {args.lesson}/{total_lessons} · {len(batch)} focus words")
print(f"Generating dialogue with {args.model}...")

response = client.chat.completions.create(
    model=args.model,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a French language teaching assistant. "
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
header = f"# CEFR {args.level} — Lesson {args.lesson}/{total_lessons}\n\n---\n"
dialogue = header + "\n" + dialogue + "\n"

os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
with open(args.output, "w", encoding="utf-8") as f:
    f.write(dialogue)

print(f"Wrote: {args.output} ({len(dialogue.splitlines())} lines)")
