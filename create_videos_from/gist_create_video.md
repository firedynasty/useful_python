# Create Slideshow Videos from Images, Text, and Video Clips

A Python script + system integration that lets you **select files in your file explorer, right-click, and generate a combined slideshow video**. Each image is shown for a configurable duration, text files are rendered as white-on-black slides, and video clips are re-encoded and stitched in seamlessly.

## What it does

1. You select files (images, `.txt`/`.md` files, video clips) in Finder/Explorer
2. Right-click and run the quick action
3. It prompts you for "seconds per image"
4. Outputs a single `.mp4` combining everything in order

**Supported input formats:**
- **Images:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`, `.svg`
- **Text:** `.txt`, `.md` (rendered as white text on black background, auto-paginated)
- **Video:** `.mp4`, `.mov`, `.webm`, `.avi`, `.mkv`, `.m4v`, `.ogg`

**Output:** A single H.264 `.mp4` at 1920x1080, 25fps. Images/text are centered on a black background preserving aspect ratio.

---

## Prerequisites

### 1. Install Python 3

- **Windows:** Download from [python.org](https://www.python.org/downloads/). During install, **check "Add Python to PATH"**.
- **Mac:** `brew install python3` or download from python.org.

### 2. Install ffmpeg

- **Windows:** Download from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) (get the "essentials" build). Extract it and **add the `bin/` folder to your system PATH** ([guide](https://www.wikihow.com/Install-FFmpeg-on-Windows)).
- **Mac:** `brew install ffmpeg`

Verify: open a terminal and run `ffmpeg -version` — you should see version info.

### 3. Install Pillow (Python image library)

```bash
pip install Pillow
```

---

## The Script

Save this as `create_video.py` somewhere permanent (e.g. `C:\Scripts\create_video.py` on Windows or `~/Scripts/create_video.py` on Mac).

```python
"""
create_video.py

Combines a list of image/text/video files into a single slideshow video.

Usage:
  python create_video.py --filelist files.txt --duration 3
  python create_video.py --filelist files.txt --duration 5 --output my_video.mp4
"""

import argparse
import os
import platform
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
    description="Combine files from a list into a slideshow video.")
parser.add_argument("--filelist", required=True,
                    help="Text file with one file path per line")
parser.add_argument("--output", default=None,
                    help="Output video path (auto-generated if omitted)")
parser.add_argument("--duration", type=int, default=6,
                    help="Seconds per still image/text slide (default: 6)")
parser.add_argument("--width", type=int, default=1920,
                    help="Video width (default: 1920)")
parser.add_argument("--height", type=int, default=1080,
                    help="Video height (default: 1080)")
args = parser.parse_args()

# ── Resolve file list ────────────────────────────────────────────────────

file_list = []
with open(args.filelist, "r") as f:
    for line in f:
        line = line.strip()
        if line:
            file_list.append(line)

if not file_list:
    print("Error: no files in filelist")
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

# ── Build output filename ────────────────────────────────────────────────

if args.output:
    output_path = os.path.abspath(args.output)
else:
    first = os.path.splitext(os.path.basename(file_list[0]))[0]
    output_name = first + "_combined.mp4"
    output_path = os.path.abspath(output_name)

print(f"Files to include ({len(steps)}):")
for i, s in enumerate(steps):
    print(f"  {i+1}. [{s['type']}] {s['name']}")
print(f"Output: {output_path}")


# ── Helpers ──────────────────────────────────────────────────────────────

def find_font(size):
    """Find a system font. Works on Mac, Windows, and Linux."""
    font_paths = []
    system = platform.system()
    if system == "Darwin":  # Mac
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
            "/Library/Fonts/Arial Unicode MS.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    elif system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/consola.ttf",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_text_to_images(text_path, width, height):
    """Render a text file as white-on-black slides, auto-paginated."""
    text = None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
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
        if current_page and (len(current_page) >= max_lines_per_page
                             or current_char_count + line_chars > max_chars_per_page):
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
    """Resize and center an image on a black background."""
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((width, height), Image.LANCZOS)
    bg = Image.new("RGB", (width, height), "black")
    x = (width - img.width) // 2
    y = (height - img.height) // 2
    bg.paste(img, (x, y))
    return bg


def image_to_clip(image_path, out_path, duration, width, height):
    """Convert a still image to a video clip of the given duration."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "25",
        "-i", image_path,
        "-t", str(duration),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ffmpeg error (image_to_clip):\n{r.stderr}")
        sys.exit(1)


def reencode_video(video_path, out_path, width, height):
    """Re-encode a video clip to the target resolution and framerate."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
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
            image_to_clip(img_path, clip_path, args.duration,
                          args.width, args.height)
            segment_clips.append(clip_path)
            seg_count += 1
        page_label = f" ({len(pages)} pages)" if len(pages) > 1 else ""
        print(f"  Rendered: {step['name']}{page_label}")
    elif step["type"] == "image":
        img_path = os.path.join(tmpdir, f"seg_{seg_count:03d}.png")
        clip_path = os.path.join(tmpdir, f"seg_{seg_count:03d}.mp4")
        img = prepare_image(step["file"], args.width, args.height)
        img.save(img_path)
        image_to_clip(img_path, clip_path, args.duration,
                      args.width, args.height)
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
```

---

## Setup: Right-Click Integration

### Windows (Send To menu)

This is the simplest approach -- adds a "Create Video" option when you right-click files.

1. Press `Win+R`, type `shell:sendto`, press Enter. This opens your SendTo folder.

2. Create a file called `Create Video.bat` in that folder with this content:

```bat
@echo off
setlocal

:: Prompt for duration
set /p DURATION="Seconds per image (default 3): "
if "%DURATION%"=="" set DURATION=3

:: Write selected files to a temp list
set TMPLIST=%TEMP%\create_video_files.txt
if exist "%TMPLIST%" del "%TMPLIST%"

:loop
if "%~1"=="" goto run
echo %~1>> "%TMPLIST%"
shift
goto loop

:run
:: Get the folder of the first file for output location
python "C:\Scripts\create_video.py" --filelist "%TMPLIST%" --duration %DURATION%
pause
```

3. Update the path `C:\Scripts\create_video.py` to wherever you saved the script.

**Usage:** Select files in Explorer > Right-click > **Send to** > **Create Video**

### Windows (PowerShell context menu -- alternative)

If you want it directly in the right-click menu instead of Send To, you can create a registry entry. This is more advanced -- the Send To approach above is recommended.

### Mac (Automator Quick Action)

1. Open **Automator** > New > **Quick Action**
2. Set "Workflow receives current" to **files or folders** in **Finder**
3. Add a **Run AppleScript** action with this content:

```applescript
on run {input, parameters}
    if (count of input) is 0 then
        display dialog "No files were selected." buttons {"OK"} default button "OK"
        return
    end if

    set dialogResult to display dialog "Seconds per image:" default answer "2" buttons {"Cancel", "OK"} default button "OK"
    set dur to text returned of dialogResult

    set tmpList to "/tmp/create_video_files.txt"
    do shell script "rm -f " & quoted form of tmpList
    repeat with selectedFile in input
        set filePath to POSIX path of selectedFile
        do shell script "echo " & quoted form of filePath & " >> " & quoted form of tmpList
    end repeat

    set firstFile to POSIX path of (item 1 of input)
    set outputFolder to do shell script "dirname " & quoted form of firstFile

    set shellScript to "cd " & quoted form of outputFolder & " && python3 ~/Scripts/create_video.py --filelist /tmp/create_video_files.txt --duration " & dur

    tell application "Terminal"
        activate
        do script shellScript
    end tell
end run
```

4. Save as "Create Video". It will appear in Finder's right-click > **Quick Actions** menu.

---

## Usage (command line)

You can also run it directly from the terminal:

```bash
# 1. Create a text file listing the files you want (one path per line)
echo "C:\Photos\img1.jpg" > files.txt
echo "C:\Photos\img2.png" >> files.txt
echo "C:\Photos\notes.txt" >> files.txt

# 2. Run the script
python create_video.py --filelist files.txt --duration 3

# 3. Output: img1_combined.mp4 in the current directory
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--filelist` | (required) | Path to a text file with one file path per line |
| `--duration` | `6` | Seconds each image/text slide is shown |
| `--output` | auto | Output file path (defaults to `<first_file>_combined.mp4`) |
| `--width` | `1920` | Video width in pixels |
| `--height` | `1080` | Video height in pixels |

---

## How it works under the hood

1. **Reads the file list** and classifies each file as image, text, or video
2. **Converts each file into a video segment:**
   - **Images** are resized (preserving aspect ratio), centered on a black 1920x1080 canvas, and turned into a clip of `--duration` seconds
   - **Text files** are rendered as white text on black background using Pillow. Markdown headers (`#`, `##`) are uppercased, `**bold**` markers are stripped. Long text is automatically split across multiple pages
   - **Videos** are re-encoded to match the target resolution and framerate (25fps)
3. **Concatenates** all segments into a single MP4 using ffmpeg's concat demuxer
4. **Cleans up** all temporary files

---

## Troubleshooting

- **"ffmpeg not found"** -- Make sure ffmpeg is in your PATH. On Windows, you may need to restart your terminal after adding it.
- **"No module named PIL"** -- Run `pip install Pillow`
- **Garbled text** -- The script tries UTF-8 first, then falls back to Latin-1. Save your text files as UTF-8.
- **Black output video** -- Make sure your file paths in the filelist don't have trailing spaces or quotes.
