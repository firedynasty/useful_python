#!/bin/bash
# run.sh — full pipeline: dialogue.txt → lesson.mp4
# Language is configured in language.py (swap by commenting/uncommenting)
# Prerequisites: export OPENAI_API_KEY=sk-...

set -e
cd "$(dirname "$0")"

echo "=== Step 1: TTS + SRT generation ==="
python step1_tts.py --input dialogue.txt --output_dir output/

echo ""
echo "=== Step 2: Burn subtitles → video ==="
bash step2_video.sh output/

echo ""
echo "=== Step 3: Word-by-word gloss ==="
python step3_gloss.py --input dialogue.txt --output output/gloss_output.csv
