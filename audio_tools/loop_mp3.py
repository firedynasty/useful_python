#!/usr/bin/env python3
"""
loop_mp3.py  —  Loop an entire audio file N times and export as MP3.

Usage:
    python3 loop_mp3.py <file>
    python3 loop_mp3.py <file> <repeat_count>
"""

import os
import subprocess
import sys

FFMPEG = "/opt/homebrew/bin/ffmpeg"


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def loop_audio(input_path, repeats, output_path):
    inputs = []
    for _ in range(repeats):
        inputs += ["-i", input_path]
    stream_labels = "".join(f"[{i}:a]" for i in range(repeats))
    filter_complex = f"{stream_labels}concat=n={repeats}:v=0:a=1[out]"
    run([
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path
    ])


mp3_file = sys.argv[1]

if len(sys.argv) >= 3:
    repeats = int(sys.argv[2])
else:
    repeats = int(input("Times to loop: ").strip())

file_prefix = os.path.splitext(os.path.basename(mp3_file))[0]
out_file = os.path.join(os.path.dirname(mp3_file), f"{file_prefix}_x{repeats}.mp3")

print(f"Looping {repeats}x: {os.path.basename(mp3_file)}")
loop_audio(mp3_file, repeats, out_file)
print(f"Saved: {out_file}")
