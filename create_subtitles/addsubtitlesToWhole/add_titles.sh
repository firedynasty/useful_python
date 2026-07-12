#!/bin/bash
# Burn subtitles from bullet points in add_titles.md over the original video.
# Each bullet point is displayed for 5 seconds, sequentially from the start.
# Only re-encodes the subtitle portion; the remainder is stream-copied for speed.
#
# Usage: bash add_titles.sh <input.mp4>
#
# add_titles.md format (one per line, starting with *):
#   * subtitle text here
#   * another subtitle
#
# Requires: ffmpeg, python3

set -e

INPUT="${1:?Usage: bash add_titles.sh <input.mp4>}"
DIR=$(cd "$(dirname "$INPUT")" && pwd)
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
FILENAME=$(basename "$INPUT")
BASENAME="${FILENAME%.*}"
cd "$DIR"

TITLES_FILE="$SCRIPT_DIR/add_titles.md"
if [ ! -f "$TITLES_FILE" ]; then
  echo "Error: $TITLES_FILE not found"
  exit 1
fi

WORK=$(mktemp -d)
trap "rm -rf $WORK" EXIT

echo "=== Step 1: Generate SRT and plan splits ==="
SRT_PATH="$WORK/subtitles.srt"
export TITLES_FILE SRT_PATH WORK FILENAME
SPLIT_END=$(python3 << 'PYEOF'
import os, sys

HOLD_SECONDS = 5
titles_file = os.environ["TITLES_FILE"]
srt_path = os.environ["SRT_PATH"]

bullets = []
with open(titles_file, "r") as f:
    for raw in f:
        raw = raw.strip()
        if not raw:
            continue
        if raw.startswith("* "):
            raw = raw[2:]
        elif raw.startswith("- "):
            raw = raw[2:]
        bullets.append(raw.strip())

if not bullets:
    print("Error: no bullet points found in add_titles.md", file=sys.stderr)
    sys.exit(1)

def fmt(sec):
    h = int(sec) // 3600
    m = (int(sec) % 3600) // 60
    s = int(sec) % 60
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

split_end = len(bullets) * HOLD_SECONDS

with open(srt_path, "w") as f:
    for i, text in enumerate(bullets):
        start = i * HOLD_SECONDS
        end = start + HOLD_SECONDS
        f.write(f"{i+1}\n{fmt(start)} --> {fmt(end)}\n{text}\n\n")

print(split_end)
PYEOF
)

echo "  Subtitle portion: 0 – ${SPLIT_END}s"
cat "$SRT_PATH"
echo ""

# Get video duration
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILENAME")
HAS_TAIL=$(python3 -c "print(1 if float('$DURATION') > float('$SPLIT_END') + 0.1 else 0)")

STYLE="FontName=Arial Unicode MS,FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=15"

echo "=== Step 2: Re-encode subtitle portion (0–${SPLIT_END}s) ==="
ffmpeg -y -i "$FILENAME" -t "$SPLIT_END" \
  -vf "pad=iw:ih+140:0:0:black,subtitles=filename=${SRT_PATH}:fontsdir=/Library/Fonts:force_style='${STYLE}'" \
  -c:a copy \
  "$WORK/head.mp4" 2>&1 | tail -3

if [ "$HAS_TAIL" = "1" ]; then
  echo "=== Step 3: Stream-copy remainder (${SPLIT_END}s–end) ==="
  # Pad must match head segment so dimensions are consistent for concat
  ffmpeg -y -ss "$SPLIT_END" -i "$FILENAME" \
    -vf "pad=iw:ih+140:0:0:black" \
    -c:a copy \
    "$WORK/tail.mp4" 2>&1 | tail -3

  echo "=== Step 4: Concatenate ==="
  cat > "$WORK/concat.txt" <<EOF
file '${WORK}/head.mp4'
file '${WORK}/tail.mp4'
EOF
  ffmpeg -y -f concat -safe 0 -i "$WORK/concat.txt" \
    -c copy "${BASENAME}_subtitled.mp4" 2>&1 | tail -3
else
  cp "$WORK/head.mp4" "${BASENAME}_subtitled.mp4"
fi

echo ""
echo "=== Done! ==="
echo "Subtitled video: ${DIR}/${BASENAME}_subtitled.mp4"
