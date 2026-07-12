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

echo "=== Creating subtitle video from ${DIR}/ ==="
echo "    Target language SRT: ${TARGET_SRT}"
echo "    English SRT: ${DIR}/english.srt"

ffmpeg -y \
  -f lavfi -i color=c=black:size=1920x1080:rate=25 \
  -i "${DIR}/dialogue.mp3" \
  -filter_complex \
  "[0:v]subtitles=filename=${TARGET_SRT}:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=32,PrimaryColour=&H00FFFF,Alignment=8'[v1];\
   [v1]subtitles=filename=${DIR}/english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=28,PrimaryColour=&HFFFFFF,Alignment=2'[v2]" \
  -map "[v2]" -map 1:a \
  -shortest \
  "${DIR}/lesson.mp4"

echo "=== Done! Output: ${DIR}/lesson.mp4 ==="
