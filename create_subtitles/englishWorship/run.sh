#!/bin/bash
# Full pipeline: segment an MP4, transcribe each segment, merge SRTs, burn onto full video
#
# Usage: bash run.sh <input.mp4>
#
# Example: bash run.sh "Nothing Holding Me Back.mp4"
#
# Automatically determines how many 10-min segments are needed from video duration.

set -e

INPUT="${1:?Usage: bash run.sh <input.mp4>}"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
DIR=$(cd "$(dirname "$INPUT")" && pwd)
FILENAME=$(basename "$INPUT")
BASENAME="${FILENAME%.*}"
cd "$DIR"

SEGMENT_DURATION=600  # 10 minutes

# Get total duration in seconds
TOTAL_SEC=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILENAME" | cut -d. -f1)
NUM_SEGS=$(( (TOTAL_SEC + SEGMENT_DURATION - 1) / SEGMENT_DURATION ))

echo "Video duration: ${TOTAL_SEC}s => ${NUM_SEGS} segment(s) of ${SEGMENT_DURATION}s"
echo ""

# === Step 1: Process each segment (extract, transcribe) ===
for SEG in $(seq 1 "$NUM_SEGS"); do
  echo "=========================================="
  echo "Processing segment $SEG / $NUM_SEGS"
  echo "=========================================="
  if ! bash "$SCRIPT_DIR/english_subtitle.sh" "$FILENAME" "$SEG"; then
    EC=$?
    if [ "$NUM_SEGS" -eq 1 ]; then
      echo "Error: english_subtitle.sh failed with exit code $EC on the only segment"
      exit $EC
    fi
    echo "Warning: segment $SEG failed with exit code $EC, continuing..."
  fi
done

# === Step 2: Merge all segment SRTs into one ===
echo ""
echo "=== Merging SRTs into full english.srt ==="
python3 -c "
import re, os

segment_duration = $SEGMENT_DURATION
basename = '''$BASENAME'''
num_segs = $NUM_SEGS

counter = 1
merged = []

for seg in range(1, num_segs + 1):
    srt_path = f'{basename}_seg{seg}/english.srt'
    if not os.path.exists(srt_path):
        print(f'  Warning: {srt_path} not found, skipping')
        continue

    offset_ms = (seg - 1) * segment_duration * 1000

    with open(srt_path, 'r') as f:
        content = f.read()

    blocks = re.split(r'\n\n+', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue

        # Find the timestamp line
        ts_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', block)
        if not ts_match:
            continue

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

        new_start = fmt_ms(parse_ms(ts_match.group(1)) + offset_ms)
        new_end = fmt_ms(parse_ms(ts_match.group(2)) + offset_ms)

        # Get text lines (everything after the timestamp line)
        ts_line_idx = next(i for i, l in enumerate(lines) if '-->' in l)
        text_lines = lines[ts_line_idx + 1:]

        merged.append(f'{counter}\n{new_start} --> {new_end}\n' + '\n'.join(text_lines))
        counter += 1

with open('english.srt', 'w') as f:
    f.write('\n\n'.join(merged) + '\n')

print(f'  Merged {counter - 1} subtitle entries from {num_segs} segments')
"

# === Step 3: Burn merged SRT onto the full original video ===
echo ""
echo "=== Burning subtitles onto full video ==="
cp english.srt /tmp/english_work.srt

ffmpeg -y -i "$FILENAME" \
  -filter_complex \
  "[0:v]pad=iw:ih+140:0:0:black[padded];[padded]subtitles=filename=/tmp/english_work.srt:fontsdir=/Library/Fonts:force_style='FontName=Arial Unicode MS,FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=15'[v1]" \
  -map "[v1]" -map 0:a -c:a copy \
  "${BASENAME}_subtitled.mp4" 2>&1 | tail -5

echo ""
echo "=== All done! ==="
echo "Full SRT:       ${DIR}/english.srt"
echo "Subtitled video: ${DIR}/${BASENAME}_subtitled.mp4"
