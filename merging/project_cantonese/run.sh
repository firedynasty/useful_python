#!/bin/bash
# Quick run: Cantonese lyrics → output CSV
# Step 1 does NOT need OpenAI (translations already in lyrics.txt)
# Steps 2-4: export OPENAI_API_KEY=sk-...

set -e
cd "$(dirname "$0")"

echo "=== Step 1: Lyrics → CSV (parse triplets, no OpenAI needed) ==="
python lyrics_to_csv.py --input lyrics.txt --output cantonese_table.csv

echo ""
echo "=== Step 2: Flatten CSV → paired txt ==="
python make_adjusted.py --input cantonese_table.csv --output cantonese_adjusted.txt

echo ""
echo "=== Step 3: Generate word-by-word gloss ==="
python generate_gloss.py --input cantonese_table.csv --output cantonese_preformatted.csv

echo ""
echo "=== Step 4: Merge glosses → final output ==="
python merge_glosses.py --adjusted cantonese_adjusted.txt --gloss cantonese_preformatted.csv --output cantonese_output.csv

echo ""
echo "=== Done! Output: cantonese_output.csv ==="
