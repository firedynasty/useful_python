#!/bin/bash
# step2_video.sh
#
# Burns dual subtitles (target language top, English bottom) onto
# a black background with the dialogue audio.
#
# Reads LANGUAGE_NAME from language.py to find the correct SRT file.
#
# Usage:
#   bash step2_video.sh [output_dir]
#   bash step2_video.sh output/

set -e
DIR="${1:-output}"

# Read language name from language.py to build SRT filename
LANG_NAME=$(python3 -c "from language import LANGUAGE_NAME; print(LANGUAGE_NAME.lower().replace(' ', '_'))")
TARGET_SRT="${DIR}/${LANG_NAME}.srt"

if [ ! -f "$TARGET_SRT" ]; then
    echo "Error: $TARGET_SRT not found. Run step1_tts.py first."
    exit 1
fi

PINYIN_SRT="${DIR}/pinyin.srt"

echo "=== Creating subtitle video from ${DIR}/ ==="
echo "    Target language SRT: ${TARGET_SRT}"
if [ -f "$PINYIN_SRT" ]; then
    echo "    Pinyin SRT: ${PINYIN_SRT}"
fi
echo "    English SRT: ${DIR}/english.srt"

if [ -f "$PINYIN_SRT" ]; then
    # Three subtitle tracks: Chinese (top), Pinyin (middle), English (bottom)
    ffmpeg -y \
      -f lavfi -i color=c=black:size=1920x1080:rate=25 \
      -i "${DIR}/dialogue.mp3" \
      -filter_complex \
      "[0:v]subtitles=filename=${TARGET_SRT}:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=32,PrimaryColour=&H00FFFF,Alignment=8'[v1];\
       [v1]subtitles=filename=${PINYIN_SRT}:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=26,PrimaryColour=&H00FF00,Alignment=5'[v2];\
       [v2]subtitles=filename=${DIR}/english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v3]" \
      -map "[v3]" -map 1:a \
      -shortest \
      "${DIR}/lesson.mp4"
else
    # Two subtitle tracks: target language (top), English (bottom)
    ffmpeg -y \
      -f lavfi -i color=c=black:size=1920x1080:rate=25 \
      -i "${DIR}/dialogue.mp3" \
      -filter_complex \
      "[0:v]subtitles=filename=${TARGET_SRT}:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=32,PrimaryColour=&H00FFFF,Alignment=8'[v1];\
       [v1]subtitles=filename=${DIR}/english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v2]" \
      -map "[v2]" -map 1:a \
      -shortest \
      "${DIR}/lesson.mp4"
fi

echo "=== Done! Output: ${DIR}/lesson.mp4 ==="

# === Chinese-only test video (no pinyin, no English) ===
echo ""
echo "=== Creating Chinese-only test video ==="

ffmpeg -y \
  -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i "${DIR}/dialogue.mp3" \
  -filter_complex \
  "[0:v]subtitles=filename=${TARGET_SRT}:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=36,PrimaryColour=&H00FFFF,Alignment=5'[v1]" \
  -map "[v1]" -map 1:a \
  -shortest \
  "${DIR}/lesson_test.mp4"

echo "=== Done! Output: ${DIR}/lesson_test.mp4 ==="
