#!/bin/bash
# Quick run: Spanish lyrics → output CSV
# Prerequisites: export OPENAI_API_KEY=sk-...

set -e
cd "$(dirname "$0")"

echo "=== Step 1: Lyrics → CSV (translate to English) ==="
python lyrics_to_csv.py --input lyrics.txt --output spanish_table.csv

echo ""
echo "=== Step 2: Flatten CSV → paired txt ==="
python make_adjusted.py --input spanish_table.csv --output spanish_adjusted.txt

echo ""
echo "=== Step 3: Generate word-by-word gloss ==="
python generate_gloss.py --input spanish_table.csv --output spanish_preformatted.csv

echo ""
echo "=== Step 4: Merge glosses → final output ==="
python merge_glosses.py --adjusted spanish_adjusted.txt --gloss spanish_preformatted.csv --output spanish_output.csv

echo ""
echo "=== Done! Output: spanish_output.csv ==="
