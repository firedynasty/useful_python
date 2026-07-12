"""
create_video.py

Combines files (images, text, videos) into a single video in the order given.
- Text files are rendered as white text on a black background
- Images are shown as stills for a set duration
- Videos are included at their original duration

Output name is auto-generated from the input filenames.

Usage:
  python create_video.py intro.txt clip.mp4 photo.jpg
  # → outputs: intro_clip_photo.mp4

  python create_video.py --duration 8 notes.txt demo.mp4
  python create_video.py --output custom_name.mp4 file1.txt file2.mp4
"""

import argparse
import os
import subprocess
import sys
import textwrap
import tempfile
import shutil

from PIL import Image, ImageDraw, ImageFont

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg"}
TEXT_EXTS = {".txt", ".md"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v", ".ogg"}

parser = argparse.ArgumentParser(
    description="Combine files into a video in the order given.")
parser.add_argument("files", nargs="*", help="Files to include (images, text, videos)")
parser.add_argument("--filelist", default=None, help="Text file with one file path per line")
parser.add_argument("--output", default=None, help="Output video path (auto-generated if omitted)")
parser.add_argument("--duration", type=int, default=6, help="Seconds per still segment (default: 6)")
parser.add_argument("--width", type=int, default=1920, help="Video width (default: 1920)")
parser.add_argument("--height", type=int, default=1080, help="Video height (default: 1080)")
args = parser.parse_args()

# ── Resolve file list ────────────────────────────────────────────────────

file_list = list(args.files)
if args.filelist:
    with open(args.filelist, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                file_list.append(line)

if not file_list:
    print("Error: no files provided")
    sys.exit(1)

# ── Validate input files ─────────────────────────────────────────────────

steps = []
for filepath in file_list:
    if not os.path.isfile(filepath):
        print(f"Error: file not found: {filepath}")
        sys.exit(1)
    ext = os.path.splitext(filepath)[1].lower()
    if ext in IMAGE_EXTS:
        ftype = "image"
    elif ext in TEXT_EXTS:
        ftype = "text"
    elif ext in VIDEO_EXTS:
        ftype = "video"
    else:
        print(f"Error: unsupported file type: {filepath}")
        sys.exit(1)
    steps.append({"type": ftype, "file": os.path.abspath(filepath),
                   "name": os.path.basename(filepath)})

# ── Build output filename from input names ───────────────────────────────

if args.output:
    output_path = os.path.abspath(args.output)
else:
    parts = [os.path.splitext(os.path.basename(f))[0] for f in file_list]
    output_name = "_".join(parts) + ".mp4"
    output_path = os.path.abspath(output_name)

print(f"Files to include ({len(steps)}):")
for i, s in enumerate(steps):
    print(f"  {i+1}. [{s['type']}] {s['name']}")
print(f"Output: {output_path}")


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


def render_text_to_images(text_path, width, height):
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

    while display_lines and not display_lines[0]:
        display_lines.pop(0)
    while display_lines and not display_lines[-1]:
        display_lines.pop()

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

    images = []
    for page_lines in pages:
        img = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(img)
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
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((width, height), Image.LANCZOS)
    bg = Image.new("RGB", (width, height), "black")
    x = (width - img.width) // 2
    y = (height - img.height) // 2
    bg.paste(img, (x, y))
    return bg


def image_to_clip(image_path, out_path, duration, width, height):
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
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", "25",
        "-an",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ffmpeg error (reencode_video):\n{r.stderr}")
        sys.exit(1)


# ── Generate video segments ──────────────────────────────────────────────

tmpdir = tempfile.mkdtemp(prefix="create_video_")
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


# ── Concatenate all segments ─────────────────────────────────────────────

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

print(f"\nBuilding video...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"ffmpeg error:\n{result.stderr}")
    sys.exit(1)

shutil.rmtree(tmpdir)

print(f"\nDone! Output: {output_path}")
print(f"  {len(segment_clips)} segments")
