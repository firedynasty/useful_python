#!/bin/bash
# step2_video.sh
#
# Burns triple subtitles (Korean top, Romanization middle, English bottom)
# onto a black background with the dialogue audio.
#
# Usage:
#   bash step2_video.sh [output_dir]
#   bash step2_video.sh output/

set -e
DIR="${1:-output}"

LANG_NAME=$(python3 -c "from language import LANGUAGE_NAME; print(LANGUAGE_NAME.lower().replace(' ', '_'))")
TARGET_SRT="${DIR}/${LANG_NAME}.srt"

if [ ! -f "$TARGET_SRT" ]; then
    echo "Error: $TARGET_SRT not found. Run step1_tts.py first."
    exit 1
fi

echo "=== Creating subtitle video from ${DIR}/ ==="
echo "    Target language SRT: ${TARGET_SRT}"
echo "    Romanization SRT: ${DIR}/romanization.srt"
echo "    English SRT: ${DIR}/english.srt"

# Three subtitle tracks: Korean (top), Romanization (middle), English (bottom)
ffmpeg -y \
  -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i "${DIR}/dialogue.mp3" \
  -filter_complex \
  "[0:v]subtitles=filename=${TARGET_SRT}:fontsdir=/Library/Fonts:force_style='FontName=AppleGothic,FontSize=34,PrimaryColour=&H00FFFF,Alignment=8'[v1];\
   [v1]subtitles=filename=${DIR}/romanization.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=26,PrimaryColour=&H00FF00,Alignment=5'[v2];\
   [v2]subtitles=filename=${DIR}/english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v3]" \
  -map "[v3]" -map 1:a \
  -shortest \
  "${DIR}/lesson.mp4"

echo "=== Done! Output: ${DIR}/lesson.mp4 ==="

# === Korean-only test video (no romanization or English) ===
echo ""
echo "=== Creating Korean-only test video ==="

ffmpeg -y \
  -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i "${DIR}/dialogue.mp3" \
  -filter_complex \
  "[0:v]subtitles=filename=${TARGET_SRT}:fontsdir=/Library/Fonts:force_style='FontName=AppleGothic,FontSize=36,PrimaryColour=&H00FFFF,Alignment=5'[v1]" \
  -map "[v1]" -map 1:a \
  -shortest \
  "${DIR}/lesson_test.mp4"

echo "=== Done! Output: ${DIR}/lesson_test.mp4 ==="
