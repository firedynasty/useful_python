#!/bin/bash
# Extract clips around each note in add_titles.md, burn subtitles on just those
# short clips, then concatenate into one highlights video.
# Much faster than re-encoding the full video.
#
# Usage: bash add_titles.sh <input.mp4>
#
# add_titles.md format (one per line):
#   M:SS, caption text
#   e.g.  1:17, need to pass at an angle
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

echo "=== Step 1: Parse add_titles.md ==="
export TITLES_FILE WORK FILENAME
TITLES_FILE="$TITLES_FILE" WORK="$WORK" FILENAME="$FILENAME" python3 << 'PYEOF'
import re, sys, json, os

HOLD_SECONDS = 5
LEAD_IN = 3

titles_file = os.environ["TITLES_FILE"]
work = os.environ["WORK"]

lines = []
with open(titles_file, "r") as f:
    for raw in f:
        raw = raw.strip()
        if not raw:
            continue
        m = re.match(r"^(\d+(?::\d{2}){1,2})\s*,\s*(.+)$", raw)
        if not m:
            continue
        parts = m.group(1).split(":")
        if len(parts) == 2:
            total_sec = int(parts[0]) * 60 + int(parts[1])
        else:
            total_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        lines.append((total_sec, m.group(2)))

if not lines:
    print("Error: no valid entries found in add_titles.md", file=sys.stderr)
    sys.exit(1)

lines.sort(key=lambda x: x[0])

clips = []
for i, (ts, text) in enumerate(lines):
    clip_start = max(0, ts - LEAD_IN)
    if i + 1 < len(lines) and lines[i + 1][0] < ts + HOLD_SECONDS:
        note_end = lines[i + 1][0]
    else:
        note_end = ts + HOLD_SECONDS
    clip_duration = note_end - clip_start
    sub_offset = ts - clip_start
    clips.append({
        "start": clip_start,
        "duration": clip_duration,
        "text": text,
        "sub_offset": sub_offset,
        "sub_duration": note_end - ts,
        "orig_sec": ts,
    })

with open(os.path.join(work, "clips.json"), "w") as f:
    json.dump(clips, f)

print(f"  Found {len(clips)} notes")
PYEOF

echo "=== Step 2: Extract and subtitle each clip ==="
python3 << 'PYEOF'
import json, subprocess, os

work = os.environ["WORK"]
filename = os.environ["FILENAME"]

with open(os.path.join(work, "clips.json")) as f:
    clips = json.load(f)

def fmt(sec):
    h = int(sec) // 3600
    m = (int(sec) % 3600) // 60
    s = int(sec) % 60
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

concat_list = []
for i, clip in enumerate(clips):
    print(f"  Clip {i+1}/{len(clips)}: {clip['text'][:50]}")

    # Create a mini SRT for this clip
    srt_path = os.path.join(work, f"sub_{i}.srt")
    # Show original timestamp from add_titles.md alongside the comment
    orig_min = clip["orig_sec"] // 60
    orig_sec = clip["orig_sec"] % 60
    orig_ts = f"{orig_min}:{orig_sec:02d}"
    with open(srt_path, "w") as f:
        start_ts = fmt(clip["sub_offset"])
        end_ts = fmt(clip["sub_offset"] + clip["sub_duration"])
        f.write(f"1\n{start_ts} --> {end_ts}\n{orig_ts}, {clip['text']}\n")

    # Seek into original video, pad, and burn subtitle in one pass.
    # Using -ss before -i with a filter forces re-encoding, so output
    # timestamps start at 0 and the SRT timing aligns correctly.
    out_clip = os.path.join(work, f"clip_{i}.mp4")
    style = "FontName=Arial Unicode MS,FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=15"
    filter_str = (
        f"[0:v]pad=iw:ih+140:0:0:black[padded];"
        f"[padded]subtitles=filename={srt_path}:fontsdir=/Library/Fonts"
        f":force_style='{style}'[v1]"
    )
    result = subprocess.run([
        "ffmpeg", "-y", "-ss", str(clip["start"]),
        "-i", filename, "-t", str(clip["duration"]),
        "-filter_complex", filter_str,
        "-map", "[v1]", "-map", "0:a", "-c:a", "copy",
        out_clip
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ERROR: {result.stderr[-200:]}")

    concat_list.append(f"file '{out_clip}'")

with open(os.path.join(work, "concat.txt"), "w") as f:
    f.write("\n".join(concat_list))
PYEOF

echo "=== Step 3: Concatenate clips ==="
ffmpeg -y -f concat -safe 0 -i "$WORK/concat.txt" \
  -c copy "${BASENAME}_subtitled.mp4" 2>&1 | tail -3

echo ""
echo "=== Done! ==="
echo "Subtitled video: ${DIR}/${BASENAME}_subtitled.mp4"
