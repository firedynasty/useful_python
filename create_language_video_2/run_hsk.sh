#!/bin/bash
# run_hsk.sh
#
# Generate HSK lesson videos. Each HSK level is split into 10 lessons
# sorted by word frequency (most common words first).
#
# Usage:
#   ./run_hsk.sh <level>              # all 10 lessons for that HSK level
#   ./run_hsk.sh <level> <lesson>     # single lesson within that level
#
# Examples:
#   ./run_hsk.sh 1          # HSK 1, all 10 lessons (294 words / 10 ≈ 30 words each)
#   ./run_hsk.sh 3 5        # HSK 3, lesson 5 only
#
# Output: output/hsk_<level>/lesson_<NN>/
#
# Requires: OPENAI_API_KEY, python3, ffmpeg
#
# HSK Levels:
#   1: 294 words  (~30/lesson)    5: 1547 words (~155/lesson)
#   2: 197 words  (~20/lesson)    6: 1684 words (~168/lesson)
#   3: 487 words  (~49/lesson)    7: 4876 words (~488/lesson)
#   4: 972 words  (~97/lesson)

set -e

LEVEL=${1:?"Usage: ./run_hsk.sh <level> [lesson]   (level: 1-7)"}
LESSON=${2:-all}
LESSONS_PER_LEVEL=10
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$LEVEL" -lt 1 ] || [ "$LEVEL" -gt 7 ]; then
    echo "Error: HSK level must be 1-7"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set"
    echo "  export OPENAI_API_KEY=sk-..."
    exit 1
fi

run_lesson() {
    local lvl=$1
    local les=$2
    local out_dir="${SCRIPT_DIR}/output/hsk_${lvl}/lesson_$(printf '%02d' "$les")"

    echo ""
    echo "════════════════════════════════════════════"
    echo "  HSK $lvl · Lesson $les/$LESSONS_PER_LEVEL"
    echo "════════════════════════════════════════════"

    mkdir -p "$out_dir"

    # Step 0: Generate dialogue from vocab
    echo ">> Generating dialogue..."
    python3 "${SCRIPT_DIR}/generate_dialogue.py" \
        --level "$lvl" \
        --lesson "$les" \
        --lessons_per_level "$LESSONS_PER_LEVEL" \
        --vocab_dir "${SCRIPT_DIR}/complete-hsk-vocabulary/wordlists/exclusive/newest" \
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
    echo "Done: HSK $lvl Lesson $les → $out_dir/"
}

# ── Run ────────────────────────────────────────────────────────────────────

if [ "$LESSON" = "all" ]; then
    echo "Generating all $LESSONS_PER_LEVEL lessons for HSK $LEVEL"
    for les in $(seq 1 $LESSONS_PER_LEVEL); do
        run_lesson "$LEVEL" "$les"
    done
    echo ""
    echo "════════════════════════════════════════════"
    echo "  All $LESSONS_PER_LEVEL lessons for HSK $LEVEL complete!"
    echo "  Output: output/hsk_${LEVEL}/"
    echo "════════════════════════════════════════════"
else
    if [ "$LESSON" -lt 1 ] || [ "$LESSON" -gt "$LESSONS_PER_LEVEL" ]; then
        echo "Error: Lesson must be 1-$LESSONS_PER_LEVEL"
        exit 1
    fi
    run_lesson "$LEVEL" "$LESSON"
fi
