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


def add_boundary_noise(input_path, duration_sec, noise_dur, noise_amp, output_path):
    """Mix a shaped white noise burst at the start and end of the segment.
    When the segment is looped, every loop seam gets noise on both sides,
    masking any amplitude discontinuity at the join point."""
    tail_start = duration_sec - noise_dur
    fade_in_d  = round(noise_dur * 0.3, 4)
    fade_out_s = round(noise_dur * 0.7, 4)
    fade_out_d = round(noise_dur * 0.3, 4)
    tail_ms    = int(tail_start * 1000)

    # n_start: noise burst shaped at beginning of segment
    # n_end:   same shape but delayed to sit right before the segment ends
    filter_complex = (
        f"anoisesrc=d={noise_dur}:c=white:a={noise_amp},"
        f"afade=t=in:d={fade_in_d},"
        f"afade=t=out:st={fade_out_s}:d={fade_out_d}[n_start];"

        f"anoisesrc=d={noise_dur}:c=white:a={noise_amp},"
        f"afade=t=in:d={fade_in_d},"
        f"afade=t=out:st={fade_out_s}:d={fade_out_d},"
        f"adelay={tail_ms}|{tail_ms}[n_end];"

        f"[0:a][n_start][n_end]amix=inputs=3:duration=first:normalize=0[out]"
    )
    run([
        FFMPEG, "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
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
start_raw  = input("Start time (e.g. 1:30 or 90): ")
end_raw    = input("End time or duration (e.g. 0:22 or 15): ")
repeats    = int(input("Times to repeat: "))
try:
    noise_inp = input("Boundary noise burst duration in seconds (e.g. 0.15, or 0 to skip) [0.15]: ").strip()
    noise_dur = float(noise_inp) if noise_inp else 0.15
    if noise_dur > 0:
        amp_inp   = input("Noise amplitude 0.0–1.0 (e.g. 0.04) [0.04]: ").strip()
        noise_amp = float(amp_inp) if amp_inp else 0.032
    else:
        noise_amp = 0.0
except EOFError:
    noise_dur = 0.15
    noise_amp = 0.032

start_sec = parse_time(start_raw)
duration  = calc_duration(start_raw, end_raw)
total_sec = duration * repeats

start_label = f"{int(start_sec // 60):02d}m{int(start_sec % 60):02d}s"
file_prefix = os.path.splitext(os.path.basename(mp3_file))[0][:10].strip()
out_file = f"{file_prefix}_{start_label}_{int(duration)}s_x{repeats}.mp3"

print(f"\nClip: {start_raw} → {end_raw} ({duration:.2f}s) × {repeats} = {total_sec:.0f}s total")
print(f"Output: {out_file}")

tmpdir = tempfile.mkdtemp()
try:
    raw_seg    = os.path.join(tmpdir, "segment.wav")
    noised_seg = os.path.join(tmpdir, "segment_noised.wav")

    print("Extracting clip...", end=" ", flush=True)
    extract_segment(mp3_file, start_sec, duration, raw_seg)
    print("done")

    seg_to_loop = raw_seg
    if noise_dur > 0:
        print("Adding boundary noise...", end=" ", flush=True)
        add_boundary_noise(raw_seg, duration, noise_dur, noise_amp, noised_seg)
        seg_to_loop = noised_seg
        print("done")

    print(f"Looping {repeats}x...", end=" ", flush=True)
    loop_audio(seg_to_loop, repeats, out_file)
    print("done")

    print(f"\nSaved: {out_file}")
finally:
    shutil.rmtree(tmpdir)
