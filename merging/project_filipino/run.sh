#!/bin/bash
# Quick run: Filipino lyrics → output CSV
# Prerequisites: export OPENAI_API_KEY=sk-...

set -e
cd "$(dirname "$0")"

echo "=== Step 1: Lyrics → CSV (translate to English) ==="
python lyrics_to_csv.py --input lyrics.txt --output filipino_table.csv

echo ""
echo "=== Step 2: Flatten CSV → paired txt ==="
python make_adjusted.py --input filipino_table.csv --output filipino_adjusted.txt

echo ""
echo "=== Step 3: Generate word-by-word gloss ==="
python generate_gloss.py --input filipino_table.csv --output filipino_preformatted.csv

echo ""
echo "=== Step 4: Merge glosses → final output ==="
python merge_glosses.py --adjusted filipino_adjusted.txt --gloss filipino_preformatted.csv --output filipino_output.csv

echo ""
echo "=== Done! Output: filipino_output.csv ==="
