#!/bin/bash
# Subtitle pipeline for audio-only files: extract segment, transcribe, generate SRT
#
# Usage: bash audio_subtitle.sh <input.m4a> <segment_number>
#
# Example: bash audio_subtitle.sh "song.m4a" 1
#
# Requires: ffmpeg, OPENAI_API_KEY env var

set -e

INPUT="${1:?Usage: bash audio_subtitle.sh <input.m4a> <segment_number>}"
SEG_NUM="${2:?Usage: bash audio_subtitle.sh <input.m4a> <segment_number>}"
DIR=$(cd "$(dirname "$INPUT")" && pwd)
FILENAME=$(basename "$INPUT")
BASENAME="${FILENAME%.*}"
cd "$DIR"

if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY not set. Run: export OPENAI_API_KEY='sk-...'"
  exit 1
fi

SEGMENT_DURATION=600  # 10 minutes in seconds
START_SEC=$(( (SEG_NUM - 1) * SEGMENT_DURATION ))
OUTPUT_DIR="${BASENAME}_seg${SEG_NUM}"
mkdir -p "$OUTPUT_DIR"

echo "=== Segment ${SEG_NUM}: starting at ${START_SEC}s ==="

echo "=== Step 1: Extract 10-min audio segment ==="
ffmpeg -y -ss "$START_SEC" -i "$FILENAME" -t "$SEGMENT_DURATION" -acodec libmp3lame -b:a 128k "$OUTPUT_DIR/audio.mp3" 2>&1 | tail -3

echo "=== Step 2: Generate English SRT (transcription) ==="
curl -s https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@$OUTPUT_DIR/audio.mp3" \
  -F model="whisper-1" \
  -F language="en" \
  -F prompt="Christian hip hop rap lyrics about faith, God, Jesus, breakthrough, hope, trust." \
  -F response_format="srt" \
  -o "$OUTPUT_DIR/english.srt"
echo "  English SRT generated"

echo ""
echo "=== Done segment ${SEG_NUM}! ==="
echo "SRT: ${DIR}/${OUTPUT_DIR}/english.srt"
