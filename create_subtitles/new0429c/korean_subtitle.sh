#!/bin/bash
# Korean subtitle pipeline: extract 10-min segment, transcribe, romanize, burn onto padded video
#
# Usage: bash korean_subtitle.sh <input.mp4> <segment_number>
#   segment_number: 1 = first 10 min, 2 = second 10 min, etc.
#
# Example: bash korean_subtitle.sh "A Stormy Marriage.mp4" 1
#          bash korean_subtitle.sh "A Stormy Marriage.mp4" 2
#
# Requires: ffmpeg, OPENAI_API_KEY env var, korean-romanizer (pip3 install korean-romanizer)

set -e

INPUT="${1:?Usage: bash korean_subtitle.sh <input.mp4> <segment_number>}"
SEG_NUM="${2:?Usage: bash korean_subtitle.sh <input.mp4> <segment_number>}"
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

echo "=== Step 3: Generate Korean SRT (transcription) ==="
curl -s https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@$OUTPUT_DIR/audio.mp3" \
  -F model="whisper-1" \
  -F language="ko" \
  -F response_format="srt" \
  -F prompt="이것은 한국 드라마 대화입니다. 모든 대사를 정확하게 전사해 주세요." \
  -o "$OUTPUT_DIR/korean.srt"
echo "  Korean SRT generated"

echo "=== Step 4: Shift subtitles +1s and extend end times +1s ==="
python3 -c "
import re

def adjust_srt(filepath, shift_ms=1000, extend_ms=1000):
    with open(filepath, 'r') as f:
        content = f.read()

    def adjust_line(match):
        start_str = match.group(1)
        end_str = match.group(2)

        def parse_ms(t):
            h, m, s, ms = map(int, re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', t).groups())
            return h*3600000 + m*60000 + s*1000 + ms

        def fmt_ms(total):
            if total < 0: total = 0
            h = total // 3600000
            m = (total % 3600000) // 60000
            s = (total % 60000) // 1000
            ms = total % 1000
            return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

        new_start = fmt_ms(parse_ms(start_str) + shift_ms)
        new_end = fmt_ms(parse_ms(end_str) + shift_ms + extend_ms)
        return f'{new_start} --> {new_end}'

    adjusted = re.sub(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', adjust_line, content)
    with open(filepath, 'w') as f:
        f.write(adjusted)

adjust_srt('$OUTPUT_DIR/korean.srt')
"
echo "  Timestamps adjusted"

echo "=== Step 5: Romanize Korean SRT ==="
python3 -c "
import re
from korean_romanizer.romanizer import Romanizer

with open('$OUTPUT_DIR/korean.srt', 'r') as f:
    lines = f.readlines()

out = []
for line in lines:
    stripped = line.strip()
    if not stripped or re.match(r'^\d+$', stripped) or re.match(r'^\d{2}:\d{2}:\d{2},\d{3} -->', stripped):
        out.append(line)
    else:
        r = Romanizer(stripped)
        out.append(r.romanize() + '\n')

with open('$OUTPUT_DIR/romanized.srt', 'w') as f:
    f.writelines(out)
"
echo "  Romanization generated"

echo "=== Step 6: Pad video + burn subtitles ==="
# Copy SRTs to simple names to avoid spaces/brackets breaking ffmpeg filter parser
cp "$OUTPUT_DIR/romanized.srt" /tmp/romanized_work.srt
cp "$OUTPUT_DIR/korean.srt" /tmp/korean_work.srt

# Romanization (green) on video, Hangul (cyan) in black bar at bottom
ffmpeg -y -i "$OUTPUT_DIR/segment.mp4" \
  -filter_complex \
  "[0:v]pad=iw:ih+280:0:0:black[padded];[padded]subtitles=filename=/tmp/romanized_work.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=7,PrimaryColour=&H00FF88,Alignment=2,MarginV=130'[v1];[v1]subtitles=filename=/tmp/korean_work.srt:fontsdir=/System/Library/Fonts:force_style='FontName=AppleSDGothicNeo-Regular,FontSize=8,PrimaryColour=&H00FFFF,Alignment=2,MarginV=15'[v2]" \
  -map "[v2]" -map 0:a -c:a copy \
  "$OUTPUT_DIR/${BASENAME}_part${SEG_NUM}.mp4" 2>&1 | tail -3

echo ""
echo "=== Done! ==="
echo "Output: ${DIR}/${OUTPUT_DIR}/${BASENAME}_part${SEG_NUM}.mp4"
echo ""
echo "Cleanup (optional): rm -f $OUTPUT_DIR/audio.mp3 $OUTPUT_DIR/segment.mp4"
