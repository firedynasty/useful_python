"""
make_video.py

Auto-discovers files in an input folder to build a video.
Files are included in natural sorted order by filename.
- Images are shown as-is for a set duration
- Text files are rendered as white text on a black background
- Videos are included at their original duration

Only supported image, text, and video files are included.

Usage:
  python make_video.py --input ./my_folder
  python make_video.py --input ./my_folder --output recipe.mp4 --duration 6
"""

import argparse
import os
import re
import subprocess
import sys
import textwrap
import tempfile

from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(
    description="Auto-discover files in a folder and combine them into a video.")
parser.add_argument("--input", required=True, help="Input folder containing files")
parser.add_argument("--output", default=None, help="Output video path (auto-generated if omitted)")
parser.add_argument("--duration", type=int, default=6, help="Seconds per segment")
parser.add_argument("--width", type=int, default=1920, help="Video width")
parser.add_argument("--height", type=int, default=1080, help="Video height")
args = parser.parse_args()

INPUT_DIR = os.path.abspath(args.input)
if not os.path.isdir(INPUT_DIR):
    print(f"Error: input folder not found: {INPUT_DIR}")
    sys.exit(1)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg"}
TEXT_EXTS = {".txt", ".md"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v", ".ogg"}
ALL_EXTS = IMAGE_EXTS | TEXT_EXTS | VIDEO_EXTS


# ── Natural sort helper ───────────────────────────────────────────────────

def natural_sort_key(filename):
    """Sort filenames naturally so pic2 comes before pic10."""
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', filename)]


# ── Auto-discover files ──────────────────────────────────────────────────

all_files = os.listdir(INPUT_DIR)
candidates = []
for name in all_files:
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALL_EXTS:
        continue
    candidates.append(name)

candidates.sort(key=natural_sort_key)

steps = []
for name in candidates:
    filepath = os.path.join(INPUT_DIR, name)
    ext = os.path.splitext(name)[1].lower()
    if ext in IMAGE_EXTS:
        steps.append({"type": "image", "file": filepath, "name": name})
    elif ext in TEXT_EXTS:
        steps.append({"type": "text", "file": filepath, "name": name})
    elif ext in VIDEO_EXTS:
        steps.append({"type": "video", "file": filepath, "name": name})

if not steps:
    print("Error: no supported files found in directory")
    sys.exit(1)

print(f"Found {len(steps)} files to include:")
for i, s in enumerate(steps):
    print(f"  {i+1}. [{s['type']}] {s['name']}")


# ── Helpers ────────────────────────────────────────────────────────────────

def find_font(size):
    """Try to find a reasonable font, fall back to default."""
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


def render_text_to_images(text_path, width, height):
    """Render a text file as white text on black background, split across multiple frames if needed."""
    # Try encodings in order: utf-8, then mac_roman (common on macOS), then latin-1
    text = None
    for enc in ("utf-8", "mac_roman", "latin-1"):
        try:
            with open(text_path, "r", encoding=enc) as f:
                text = f.read().strip()
            break
        except UnicodeDecodeError:
            continue
    raw_lines = text.split("\n")

    padding_x = 120
    padding_y = 60
    usable_width = width - padding_x * 2
    usable_height = height - padding_y * 2

    # Clean up markdown but preserve line structure
    display_lines = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            display_lines.append("")
            continue
        if stripped.startswith("## "):
            stripped = stripped[3:].upper()
        elif stripped.startswith("# "):
            stripped = stripped[2:].upper()
        stripped = stripped.replace("**", "")
        display_lines.append(stripped)

    # Remove leading/trailing blank lines
    while display_lines and not display_lines[0]:
        display_lines.pop(0)
    while display_lines and not display_lines[-1]:
        display_lines.pop()

    # Word-wrap long lines
    font_size = 40
    font = find_font(font_size)
    max_chars = usable_width // (font_size // 2 + 2)
    line_height = font_size + 12
    max_chars_per_page = 450

    wrapped_lines = []
    for line in display_lines:
        if not line:
            wrapped_lines.append("")
        elif len(line) > max_chars:
            for wl in textwrap.wrap(line, width=max_chars):
                wrapped_lines.append(wl)
        else:
            wrapped_lines.append(line)

    # Split into pages by character count and line count
    max_lines_per_page = usable_height // line_height
    pages = []
    current_page = []
    current_char_count = 0
    for line in wrapped_lines:
        line_chars = len(line)
        if current_page and (len(current_page) >= max_lines_per_page or current_char_count + line_chars > max_chars_per_page):
            pages.append(current_page)
            current_page = []
            current_char_count = 0
        current_page.append(line)
        current_char_count += line_chars
    if current_page:
        pages.append(current_page)

    # Render each page as an image
    images = []
    for page_lines in pages:
        img = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(img)

        # Center vertically
        total_text_height = len(page_lines) * line_height
        y_start = max(padding_y, (height - total_text_height) // 2)

        for i, line in enumerate(page_lines):
            if not line:
                continue
            y = y_start + i * line_height
            draw.text((padding_x, y), line, fill="white", font=font)

        images.append(img)

    return images


def prepare_image(image_path, width, height):
    """Load image, fit into frame with black letterboxing."""
    img = Image.open(image_path).convert("RGB")
    # Scale to fit within dimensions while preserving aspect ratio
    img.thumbnail((width, height), Image.LANCZOS)
    # Place on black background, centered
    bg = Image.new("RGB", (width, height), "black")
    x = (width - img.width) // 2
    y = (height - img.height) // 2
    bg.paste(img, (x, y))
    return bg


# ── Helpers for video segments ─────────────────────────────────────────────

def image_to_clip(image_path, out_path, duration, width, height):
    """Convert a still image to a video clip."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "25",
        "-i", image_path,
        "-t", str(duration),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ffmpeg error (image_to_clip):\n{r.stderr}")
        sys.exit(1)


def reencode_video(video_path, out_path, width, height):
    """Re-encode a video clip to match output format/dimensions."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", "25",
        "-an",  # strip audio for now (keeps concat simple)
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ffmpeg error (reencode_video):\n{r.stderr}")
        sys.exit(1)


# ── Generate video segments ───────────────────────────────────────────────

tmpdir = tempfile.mkdtemp(prefix="recipe_video_")
segment_clips = []
seg_count = 0

for step in steps:
    if step["type"] == "text":
        pages = render_text_to_images(step["file"], args.width, args.height)
        for j, img in enumerate(pages):
            img_path = os.path.join(tmpdir, f"seg_{seg_count:03d}.png")
            clip_path = os.path.join(tmpdir, f"seg_{seg_count:03d}.mp4")
            img.save(img_path)
            image_to_clip(img_path, clip_path, args.duration, args.width, args.height)
            segment_clips.append(clip_path)
            seg_count += 1
        page_label = f" ({len(pages)} pages)" if len(pages) > 1 else ""
        print(f"  Rendered: {step['name']}{page_label}")
    elif step["type"] == "image":
        img_path = os.path.join(tmpdir, f"seg_{seg_count:03d}.png")
        clip_path = os.path.join(tmpdir, f"seg_{seg_count:03d}.mp4")
        img = prepare_image(step["file"], args.width, args.height)
        img.save(img_path)
        image_to_clip(img_path, clip_path, args.duration, args.width, args.height)
        segment_clips.append(clip_path)
        seg_count += 1
        print(f"  Rendered: {step['name']}")
    elif step["type"] == "video":
        clip_path = os.path.join(tmpdir, f"seg_{seg_count:03d}.mp4")
        reencode_video(step["file"], clip_path, args.width, args.height)
        segment_clips.append(clip_path)
        seg_count += 1
        print(f"  Rendered: {step['name']} (video)")


# ── Concatenate all segments ──────────────────────────────────────────────

concat_path = os.path.join(tmpdir, "concat.txt")
with open(concat_path, "w") as f:
    for clip in segment_clips:
        f.write(f"file '{clip}'\n")

if args.output:
    output_path = os.path.abspath(args.output)
else:
    folder_name = os.path.basename(INPUT_DIR.rstrip(os.sep))
    output_path = os.path.abspath(folder_name + ".mp4")


cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", concat_path,
    "-c", "copy",
    output_path,
]

print(f"\nBuilding video...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"ffmpeg error:\n{result.stderr}")
    sys.exit(1)

# Cleanup
import shutil
shutil.rmtree(tmpdir)

print(f"\nDone! Output: {output_path}")
print(f"  {len(segment_clips)} segments")
