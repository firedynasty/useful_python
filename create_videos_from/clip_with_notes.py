"""
clip_with_notes.py

Takes a source video and a list of timestamp+note lines.
For each entry:
  1. Shows the note as white text on black background (title card)
  2. Extracts a short clip starting at that timestamp
  3. Slows the clip to 0.5x speed

Usage:
  python clip_with_notes.py --input video.mp4 --notes notes.txt --output new_edited.mp4
  python clip_with_notes.py --input video.mp4 --notes notes.txt --clip-duration 7 --speed 0.5

Notes file format (one per line):
  0:34 great opening shot
  1:43 step in after
  5:10 like to back up two steps then shoot
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import shutil

from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(description="Create video with title cards and slowed clips from timestamps.")
parser.add_argument("--input", required=True, help="Source video file")
parser.add_argument("--notes", required=True, help="Text file with 'timestamp note' per line")
parser.add_argument("--output", default=None, help="Output video path (default: new_edited.mp4)")
parser.add_argument("--clip-duration", type=int, default=7, help="Seconds to extract per clip (default: 7)")
parser.add_argument("--card-duration", type=int, default=6, help="Seconds to show each title card (default: 6)")
parser.add_argument("--speed", type=float, default=0.5, help="Playback speed for clips (default: 0.5)")
parser.add_argument("--width", type=int, default=1920, help="Video width (default: 1920)")
parser.add_argument("--height", type=int, default=1080, help="Video height (default: 1080)")
args = parser.parse_args()

SOURCE = os.path.abspath(args.input)
if not os.path.isfile(SOURCE):
    print(f"Error: video not found: {SOURCE}")
    sys.exit(1)

output_path = os.path.abspath(args.output) if args.output else os.path.abspath("new_edited.mp4")


# ── Parse notes file ────────────────────────────────────────────────────

def parse_timestamp(ts):
    """Convert M:SS or H:MM:SS to seconds."""
    parts = ts.strip().split(":")
    parts = [int(p) for p in parts]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


entries = []
with open(args.notes, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # Match: "0:34,0:50 note" (custom range) or "0:34 note" (default duration)
        m = re.match(r'^(\d+:\d{2}(?::\d{2})?)\s*,\s*(\d+:\d{2}(?::\d{2})?)\s+(.*)', line)
        if m:
            ts_start = m.group(1)
            ts_end = m.group(2)
            note = m.group(3).strip()
            start_secs = parse_timestamp(ts_start)
            end_secs = parse_timestamp(ts_end)
            duration = end_secs - start_secs
            entries.append({"timestamp": ts_start, "seconds": start_secs,
                            "duration": duration, "note": note})
        else:
            m2 = re.match(r'^(\d+:\d{2}(?::\d{2})?)\s+(.*)', line)
            if m2:
                ts_str = m2.group(1)
                note = m2.group(2).strip()
                secs = parse_timestamp(ts_str)
                entries.append({"timestamp": ts_str, "seconds": secs,
                                "duration": None, "note": note})
            else:
                print(f"Skipping line (no timestamp): {line}")

if not entries:
    print("Error: no valid entries found in notes file")
    sys.exit(1)

print(f"Found {len(entries)} clips to create:")
for i, e in enumerate(entries):
    dur_label = f"{e['duration']}s" if e['duration'] else f"{args.clip_duration}s (default)"
    print(f"  {i+1}. [{e['timestamp']}] {e['note']} — {dur_label}")


# ── Helpers ──────────────────────────────────────────────────────────────

def find_font(size):
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "/Library/Fonts/Arial Unicode MS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_title_card(text, timestamp, width, height):
    """Render a title card with timestamp and note text."""
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    padding_x = 120
    usable_width = width - padding_x * 2

    # Timestamp in larger font at top area
    ts_font = find_font(60)
    note_font = find_font(44)

    max_chars = usable_width // (44 // 2 + 2)
    wrapped = textwrap.wrap(text, width=max_chars) if len(text) > max_chars else [text]

    # Calculate total height for centering
    line_height_ts = 80
    line_height_note = 58
    total_height = line_height_ts + len(wrapped) * line_height_note + 20
    y_start = (height - total_height) // 2

    # Draw timestamp
    draw.text((padding_x, y_start), timestamp, fill="#FFD700", font=ts_font)

    # Draw note lines
    y = y_start + line_height_ts + 20
    for line in wrapped:
        draw.text((padding_x, y), line, fill="white", font=note_font)
        y += line_height_note

    return img


def image_to_clip(image_path, out_path, duration, width, height):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "25",
        "-i", image_path,
        "-t", str(duration),
        "-vf", f"scale={width}:{height}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ffmpeg error (image_to_clip):\n{r.stderr}")
        sys.exit(1)


def extract_and_slow_clip(source, start_secs, duration, speed, out_path, width, height):
    """Extract a clip from source video and slow it down."""
    # speed 0.5 means setpts=2*PTS (slower), atempo=0.5
    pts_factor = 1.0 / speed
    vf = (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
          f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
          f"setpts={pts_factor}*PTS")

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_secs),
        "-i", source,
        "-t", str(duration),
        "-vf", vf,
        "-af", f"atempo={speed}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", "25",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ffmpeg error (extract_and_slow):\n{r.stderr}")
        sys.exit(1)


# ── Build segments ───────────────────────────────────────────────────────

tmpdir = tempfile.mkdtemp(prefix="clip_notes_")
segment_clips = []
seg_count = 0

for i, entry in enumerate(entries):
    # 1. Title card
    card_img = render_title_card(entry["note"], entry["timestamp"], args.width, args.height)
    card_img_path = os.path.join(tmpdir, f"seg_{seg_count:03d}_card.png")
    card_clip_path = os.path.join(tmpdir, f"seg_{seg_count:03d}_card.mp4")
    card_img.save(card_img_path)
    image_to_clip(card_img_path, card_clip_path, args.card_duration, args.width, args.height)
    segment_clips.append(card_clip_path)
    seg_count += 1

    # 2. Slowed clip (use custom duration if provided, else default)
    clip_dur = entry["duration"] if entry["duration"] else args.clip_duration
    clip_path = os.path.join(tmpdir, f"seg_{seg_count:03d}_clip.mp4")
    extract_and_slow_clip(
        SOURCE, entry["seconds"], clip_dur, args.speed,
        clip_path, args.width, args.height,
    )
    segment_clips.append(clip_path)
    seg_count += 1

    print(f"  [{i+1}/{len(entries)}] {entry['timestamp']} — done")


# ── Concatenate ──────────────────────────────────────────────────────────

concat_path = os.path.join(tmpdir, "concat.txt")
with open(concat_path, "w") as f:
    for clip in segment_clips:
        f.write(f"file '{clip}'\n")

cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_path,
    "-c", "copy",
    output_path,
]

print(f"\nConcatenating {len(segment_clips)} segments...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"ffmpeg error:\n{result.stderr}")
    sys.exit(1)

shutil.rmtree(tmpdir)

print(f"\nDone! Output: {output_path}")
print(f"  {len(entries)} clips, each {args.clip_duration}s at {args.speed}x speed")
