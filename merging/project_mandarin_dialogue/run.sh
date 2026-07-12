#!/bin/bash
# Quick run: Mandarin dialogue → output CSV
# Step 1 does NOT need OpenAI (translations already in dialogue.txt)
# Steps 3-4: export OPENAI_API_KEY=sk-...
#
# Usage:
#   ./run.sh          # full run (all turns)
#   ./run.sh 3        # debug: only gloss first 3 turns

set -e
cd "$(dirname "$0")"

LIMIT_ARG=""
if [ -n "$1" ]; then
    LIMIT_ARG="--limit $1"
    echo "(Debug mode: glossing only first $1 turns)"
    echo ""
fi

echo "=== Step 1: Dialogue → CSV (parse triplets, no OpenAI needed) ==="
python dialogue_to_csv.py --input dialogue.txt --output mandarin_dialogue_table.csv

echo ""
echo "=== Step 2: Flatten CSV → paired txt ==="
python make_adjusted.py --input mandarin_dialogue_table.csv --output mandarin_dialogue_adjusted.txt

echo ""
echo "=== Step 3: Generate word-by-word gloss ==="
python generate_gloss.py --input mandarin_dialogue_table.csv --output mandarin_dialogue_preformatted.csv $LIMIT_ARG

echo ""
echo "=== Step 4: Merge glosses → final output ==="
python merge_glosses.py --adjusted mandarin_dialogue_adjusted.txt --gloss mandarin_dialogue_preformatted.csv --output mandarin_dialogue_output.csv

echo ""
echo "=== Done! Output: mandarin_dialogue_output.csv ==="
