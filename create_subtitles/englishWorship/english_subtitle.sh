#!/bin/bash
# English subtitle pipeline: extract 10-min segment, transcribe, burn onto padded video
#
# Usage: bash english_subtitle.sh <input.mp4> <segment_number>
#   segment_number: 1 = first 10 min, 2 = second 10 min, etc.
#
# Example: bash english_subtitle.sh "Nothing Holding Me Back.mp4" 1
#          bash english_subtitle.sh "Nothing Holding Me Back.mp4" 2
#
# Requires: ffmpeg, OPENAI_API_KEY env var

set -e

INPUT="${1:?Usage: bash english_subtitle.sh <input.mp4> <segment_number>}"
SEG_NUM="${2:?Usage: bash english_subtitle.sh <input.mp4> <segment_number>}"
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

echo "=== Step 1: Extract 10-min video segment ==="
ffmpeg -y -ss "$START_SEC" -i "$FILENAME" -t "$SEGMENT_DURATION" -c copy "$OUTPUT_DIR/segment.mp4" 2>&1 | tail -3

echo "=== Step 2: Extract audio from segment ==="
ffmpeg -y -i "$OUTPUT_DIR/segment.mp4" -vn -acodec libmp3lame -b:a 128k "$OUTPUT_DIR/audio.mp3" 2>&1 | tail -3

echo "=== Step 3: Generate English SRT (transcription) ==="
curl -s https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@$OUTPUT_DIR/audio.mp3" \
  -F model="whisper-1" \
  -F language="en" \
  -F response_format="srt" \
  -o "$OUTPUT_DIR/english.srt"
echo "  English SRT generated"

echo "=== Step 4: Pad video + burn English subtitles ==="
# Copy SRT to simple name to avoid spaces/brackets breaking ffmpeg filter parser
cp "$OUTPUT_DIR/english.srt" /tmp/english_work.srt

# English subtitles (white with black outline) in black bar at bottom
ffmpeg -y -i "$OUTPUT_DIR/segment.mp4" \
  -filter_complex \
  "[0:v]pad=iw:ih+140:0:0:black[padded];[padded]subtitles=filename=/tmp/english_work.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=15'[v1]" \
  -map "[v1]" -map 0:a -c:a copy \
  "$OUTPUT_DIR/${BASENAME}_part${SEG_NUM}.mp4" 2>&1 | tail -3

echo ""
echo "=== Done! ==="
echo "Output: ${DIR}/${OUTPUT_DIR}/${BASENAME}_part${SEG_NUM}.mp4"
echo ""
echo "Cleanup (optional): rm -f $OUTPUT_DIR/audio.mp3 $OUTPUT_DIR/segment.mp4"
