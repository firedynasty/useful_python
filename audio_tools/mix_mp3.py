#!/usr/bin/env python3
import os
import subprocess
import tempfile
import shutil
from datetime import datetime

FFMPEG = "/opt/homebrew/bin/ffmpeg"


def parse_time(t):
    t = t.strip()
    if ":" in t:
        parts = t.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(t)


def calc_duration(start_raw, end_raw):
    if ":" in end_raw:
        t1 = datetime.strptime(start_raw.strip(), "%M:%S")
        t2 = datetime.strptime(end_raw.strip(), "%M:%S")
        return (t2 - t1).total_seconds()
    return float(end_raw)


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def extract_segment(input_path, start_sec, duration_sec, output_path):
    # Decode to WAV to avoid MP3 encoder-delay gaps between loops
    run([
        FFMPEG, "-y",
        "-ss", str(start_sec),
        "-i", input_path,
        "-t", str(duration_sec),
        output_path
    ])


def loop_audio(input_path, repeats, output_path):
    # Concat N copies of the same stream — truly gapless, no encoder delay artifacts
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


import sys
mp3_file = sys.argv[1]
start_raw = input("Start time (e.g. 1:30 or 90): ")
end_raw   = input("End time or duration (e.g. 0:22 or 15): ")
repeats   = int(input("Times to repeat: "))

start_sec = parse_time(start_raw)
duration  = calc_duration(start_raw, end_raw)
total_sec = duration * repeats

start_label = f"{int(start_sec // 60):02d}m{int(start_sec % 60):02d}s"
out_file = f"loop_{start_label}_{int(duration)}s_x{repeats}.mp3"

print(f"\nClip: {start_raw} → {end_raw} ({duration:.2f}s) × {repeats} = {total_sec:.0f}s total")
print(f"Output: {out_file}")

tmpdir = tempfile.mkdtemp()
try:
    raw_seg = os.path.join(tmpdir, "segment.wav")

    print("Extracting clip...", end=" ", flush=True)
    extract_segment(mp3_file, start_sec, duration - 0.01, raw_seg)
    print("done")

    print(f"Looping {repeats}x...", end=" ", flush=True)
    loop_audio(raw_seg, repeats, out_file)
    print("done")

    print(f"\nSaved: {out_file}")
finally:
    shutil.rmtree(tmpdir)
