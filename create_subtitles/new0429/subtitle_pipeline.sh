#!/bin/bash
# Full subtitle pipeline: extract audio -> segment -> Whisper API -> merge SRTs -> burn onto extended video
# Usage: bash subtitle_pipeline.sh <input.mp4>
# Requires: ffmpeg, OPENAI_API_KEY env var

set -e

INPUT="${1:?Usage: bash subtitle_pipeline.sh <input.mp4>}"
BASENAME=$(basename "$INPUT" .mp4)
DIR=$(dirname "$INPUT")
cd "$DIR"

# Check API key
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY not set. Run: export OPENAI_API_KEY='sk-...'"
  exit 1
fi

SEGMENT_DURATION=600  # 10 minutes

echo "=== Step 1: Extract audio ==="
ffmpeg -y -i "$INPUT" -vn -acodec libmp3lame -b:a 128k audioStream.mp3

echo "=== Step 2: Split into ${SEGMENT_DURATION}s segments ==="
ffmpeg -y -i audioStream.mp3 -f segment -segment_time "$SEGMENT_DURATION" -c copy segment_%03d.mp3

echo "=== Step 3: Generate Chinese SRT (transcription) ==="
for f in segment_*.mp3; do
  echo "  Transcribing $f -> ${f%.mp3}_zh.srt"
  curl -s https://api.openai.com/v1/audio/transcriptions \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: multipart/form-data" \
    -F file="@$f" \
    -F model="whisper-1" \
    -F language="zh" \
    -F response_format="srt" \
    -o "${f%.mp3}_zh.srt"
done

echo "=== Step 4: Generate English SRT (translation) ==="
for f in segment_*.mp3; do
  echo "  Translating $f -> ${f%.mp3}_en.srt"
  curl -s https://api.openai.com/v1/audio/translations \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: multipart/form-data" \
    -F file="@$f" \
    -F model="whisper-1" \
    -F response_format="srt" \
    -F prompt="Translate the following Chinese audio to English." \
    -o "${f%.mp3}_en.srt"
done

echo "=== Step 5: Merge SRT segments ==="
merge_srt() {
  local LANG_SUFFIX="$1"
  local OUTPUT="$2"
  local COUNTER=1
  > "$OUTPUT"

  for srt in $(ls segment_*_${LANG_SUFFIX}.srt | sort); do
    SEG_NUM=$(echo "$srt" | grep -o '[0-9]\{3\}')
    OFFSET=$((10#$SEG_NUM * SEGMENT_DURATION))

    while IFS= read -r line; do
      if echo "$line" | grep -qE '^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$'; then
        START=$(echo "$line" | awk -F' --> ' '{print $1}')
        END=$(echo "$line" | awk -F' --> ' '{print $2}')

        offset_time() {
          local t="$1" off="$2"
          local h=$(echo "$t" | cut -d: -f1)
          local m=$(echo "$t" | cut -d: -f2)
          local s_ms=$(echo "$t" | cut -d: -f3)
          local s=$(echo "$s_ms" | cut -d, -f1)
          local ms=$(echo "$s_ms" | cut -d, -f2)
          local total=$((10#$h*3600 + 10#$m*60 + 10#$s + off))
          printf "%02d:%02d:%02d,%s" $((total/3600)) $(((total%3600)/60)) $((total%60)) "$ms"
        }

        NEW_START=$(offset_time "$START" "$OFFSET")
        NEW_END=$(offset_time "$END" "$OFFSET")
        echo "$NEW_START --> $NEW_END" >> "$OUTPUT"
      elif echo "$line" | grep -qE '^[0-9]+$'; then
        echo "$COUNTER" >> "$OUTPUT"
        COUNTER=$((COUNTER + 1))
      else
        echo "$line" >> "$OUTPUT"
      fi
    done < "$srt"
  done
  echo "  Merged to $OUTPUT"
}

merge_srt "zh" "chinese.srt"
merge_srt "en" "english.srt"

echo "=== Step 6: Burn subtitles onto extended video ==="
# Original video gets padded with 120px black bar at bottom
# Chinese (cyan) on top row of bar, English (white) below
# Get original dimensions
ORIG_HEIGHT=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$INPUT")
ORIG_WIDTH=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$INPUT")
PAD_HEIGHT=120
NEW_HEIGHT=$((ORIG_HEIGHT + PAD_HEIGHT))

ffmpeg -y -i "$INPUT" \
  -filter_complex \
  "[0:v]pad=${ORIG_WIDTH}:${NEW_HEIGHT}:0:0:black[padded];[padded]subtitles=filename=chinese.srt:fontsdir=/System/Library/Fonts:force_style='FontName=STHeiti,FontSize=22,PrimaryColour=&H00FFFF,Alignment=2,MarginV=65'[v1];[v1]subtitles=filename=english.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=22,PrimaryColour=&HFFFFFF,Alignment=2,MarginV=15'[v2]" \
  -map "[v2]" -map 0:a -c:a copy \
  "${BASENAME}_subtitled.mp4"

echo ""
echo "=== Done! ==="
echo "Output: ${DIR}/${BASENAME}_subtitled.mp4"
echo ""
echo "Cleanup (optional): rm -f segment_*.mp3 segment_*.srt audioStream.mp3"
