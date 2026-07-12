#!/bin/bash
# run_topik.sh
#
# Generate Korean TOPIK lesson videos. Words are batched into lessons of
# ~20 words each (configurable via WORDS_PER_LESSON). The number of lessons
# is computed automatically from the vocab size.
#
# First run: python convert_topik.py to create topik_vocab/ JSONs (one-time).
#
# Usage:
#   ./run_topik.sh <level>              # all lessons for that TOPIK level
#   ./run_topik.sh <level> <lesson>     # single lesson
#   ./run_topik.sh <level> 1-5          # lessons 1 through 5
#
# Examples:
#   ./run_topik.sh A          # TOPIK A (beginner), all lessons (~44 lessons of 20 words)
#   ./run_topik.sh B 5        # TOPIK B (intermediate), lesson 5 only
#   ./run_topik.sh A 1-10     # TOPIK A, lessons 1 through 10
#
# Output: output/topik_<level>/lesson_<NN>/
#
# TOPIK Levels / approx lesson counts at 20 words/lesson:
#   A: ~880 words  (beginner / TOPIK I)      → ~44 lessons
#   B: ~1800 words (intermediate / TOPIK II)  → ~90 lessons
#   C: ~2500 words (advanced / TOPIK II)      → ~125 lessons
#
# Requires: OPENAI_API_KEY, python3, ffmpeg

set -e

LEVEL=${1:?"Usage: ./run_topik.sh <level> [lesson|start-end]   (level: A, B, C)"}
LESSON=${2:-all}
WORDS_PER_LESSON=20
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Validate level
case "$LEVEL" in
    A|B|C) ;;
    *) echo "Error: TOPIK level must be A, B, or C"; exit 1 ;;
esac

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set"
    echo "  export OPENAI_API_KEY=sk-..."
    exit 1
fi

VOCAB_FILE="${SCRIPT_DIR}/topik_vocab/${LEVEL}.json"

# Check vocab exists
if [ ! -f "$VOCAB_FILE" ]; then
    echo "Error: topik_vocab/${LEVEL}.json not found"
    echo "  Run first: python convert_topik.py"
    exit 1
fi

# Compute total lessons from vocab size
WORD_COUNT=$(python3 -c "import json; print(len(json.load(open('$VOCAB_FILE'))))")
TOTAL_LESSONS=$(( (WORD_COUNT + WORDS_PER_LESSON - 1) / WORDS_PER_LESSON ))

echo "TOPIK $LEVEL: $WORD_COUNT words → $TOTAL_LESSONS lessons ($WORDS_PER_LESSON words/lesson)"

run_lesson() {
    local lvl=$1
    local les=$2
    local out_dir="${SCRIPT_DIR}/output/topik_${lvl}/lesson_$(printf '%03d' "$les")"

    echo ""
    echo "════════════════════════════════════════════"
    echo "  TOPIK $lvl · Lesson $les/$TOTAL_LESSONS"
    echo "════════════════════════════════════════════"

    mkdir -p "$out_dir"

    # Step 0: Generate dialogue from vocab
    echo ">> Generating dialogue..."
    python3 "${SCRIPT_DIR}/generate_dialogue.py" \
        --level "$lvl" \
        --lesson "$les" \
        --words_per_lesson "$WORDS_PER_LESSON" \
        --vocab_dir "${SCRIPT_DIR}/topik_vocab" \
        --output "$out_dir/dialogue.txt"

    # Step 1: TTS audio + SRT subtitles
    echo ">> Generating TTS audio + subtitles..."
    python3 "${SCRIPT_DIR}/step1_tts.py" \
        --input "$out_dir/dialogue.txt" \
        --output_dir "$out_dir"

    # Step 2: Burn subtitles into video
    echo ">> Rendering video..."
    bash "${SCRIPT_DIR}/step2_video.sh" "$out_dir"

    # Step 3: Word-by-word gloss CSV
    echo ">> Generating gloss..."
    python3 "${SCRIPT_DIR}/step3_gloss.py" \
        --input "$out_dir/dialogue.txt" \
        --output "$out_dir/gloss_output.csv"

    echo ""
    echo "Done: TOPIK $lvl Lesson $les → $out_dir/"
}

# ── Run ────────────────────────────────────────────────────────────────────

if [ "$LESSON" = "all" ]; then
    echo "Generating all $TOTAL_LESSONS lessons for TOPIK $LEVEL"
    for les in $(seq 1 $TOTAL_LESSONS); do
        run_lesson "$LEVEL" "$les"
    done
    echo ""
    echo "════════════════════════════════════════════"
    echo "  All $TOTAL_LESSONS lessons for TOPIK $LEVEL complete!"
    echo "  Output: output/topik_${LEVEL}/"
    echo "════════════════════════════════════════════"
elif echo "$LESSON" | grep -q '^[0-9]\+-[0-9]\+$'; then
    # Range: e.g. 1-10
    START_LES=$(echo "$LESSON" | cut -d- -f1)
    END_LES=$(echo "$LESSON" | cut -d- -f2)
    if [ "$START_LES" -lt 1 ] || [ "$END_LES" -gt "$TOTAL_LESSONS" ] || [ "$START_LES" -gt "$END_LES" ]; then
        echo "Error: Lesson range must be within 1-$TOTAL_LESSONS"
        exit 1
    fi
    echo "Generating lessons $START_LES–$END_LES for TOPIK $LEVEL"
    for les in $(seq "$START_LES" "$END_LES"); do
        run_lesson "$LEVEL" "$les"
    done
else
    if [ "$LESSON" -lt 1 ] || [ "$LESSON" -gt "$TOTAL_LESSONS" ]; then
        echo "Error: Lesson must be 1-$TOTAL_LESSONS"
        exit 1
    fi
    run_lesson "$LEVEL" "$LESSON"
fi
