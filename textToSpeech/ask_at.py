"""
Ask a question about the dialogue at a specific timestamp.

Looks up the transcript sidecar JSON produced by narrator_teacher_student.py,
finds what was being said at the given time, grabs surrounding context, and
copies a ready-to-paste block to clipboard for Claude chat.

Usage:
    python ask_at.py 3:00
    python ask_at.py 3:00 -q "Why does Jesus stay silent here?"
    python ask_at.py 3:00 canannite_womans_faith.json -q "What does Son of David mean?"
    python ask_at.py 1:45 --context 5

Paste the clipboard into Claude chat (question is already included if you used -q).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Re-use the automator_scripts notification pattern from readQRcode Automator action



def parse_timestamp(ts: str) -> int:
    """Convert M:SS or H:MM:SS or raw seconds string to milliseconds."""
    ts = ts.strip()
    parts = ts.split(":")
    try:
        if len(parts) == 1:
            return int(float(parts[0]) * 1000)
        elif len(parts) == 2:
            minutes, seconds = parts
            return (int(minutes) * 60 + float(seconds)) * 1000
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return (int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1000
    except ValueError:
        pass
    print(f"Error: can't parse timestamp '{ts}'. Use M:SS, H:MM:SS, or raw seconds.")
    sys.exit(1)


def ms_to_ts(ms: int) -> str:
    """Convert milliseconds to M:SS string."""
    total_s = int(ms / 1000)
    m, s = divmod(total_s, 60)
    return f"{m}:{s:02d}"


def find_json(directory: Path) -> Path:
    """Find the most recently modified JSON transcript in a directory."""
    jsons = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jsons:
        print(f"Error: no transcript JSON files found in {directory}")
        sys.exit(1)
    return jsons[0]


def copy_to_clipboard(text: str) -> None:
    proc = subprocess.run(["pbcopy"], input=text.encode("utf-8"))
    if proc.returncode != 0:
        print("Warning: could not copy to clipboard")


def notify(message: str, title: str = "ask_at — Copied to Clipboard") -> None:
    """Show a macOS notification using AppleScript (same pattern as QR code Automator script)."""
    script = (
        f'display notification {json.dumps(message)} with title {json.dumps(title)}'
    )
    subprocess.run(["osascript", "-e", script], capture_output=True)


def main():
    parser = argparse.ArgumentParser(
        description="Lookup transcript at a timestamp and copy context to clipboard"
    )
    parser.add_argument("timestamp", help="Playback position, e.g. 3:00 or 1:45")
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Transcript JSON file (default: most recent *.json in current dir)",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=3,
        metavar="N",
        help="Number of segments before and after the hit to include (default: 3)",
    )
    parser.add_argument(
        "-q", "--question",
        default="",
        help="Your question to include in the clipboard block",
    )
    args = parser.parse_args()

    target_ms = parse_timestamp(args.timestamp)

    # Resolve JSON path
    if args.json_file:
        json_path = Path(args.json_file)
        if not json_path.exists():
            print(f"Error: file not found: {json_path}")
            sys.exit(1)
    else:
        json_path = find_json(Path(__file__).parent)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    segments = data["segments"]
    audio_file = data.get("audio_file", json_path.stem)

    # Find the segment that contains target_ms
    hit_idx = None
    for i, seg in enumerate(segments):
        if seg["start_ms"] <= target_ms <= seg["end_ms"]:
            hit_idx = i
            break

    # If between segments or past the end, find nearest
    if hit_idx is None:
        closest = min(range(len(segments)), key=lambda i: abs(segments[i]["start_ms"] - target_ms))
        hit_idx = closest

    # Gather surrounding context window
    start_idx = max(0, hit_idx - args.context)
    end_idx = min(len(segments) - 1, hit_idx + args.context)
    context_segs = segments[start_idx : end_idx + 1]

    # Format for Claude chat
    title = Path(audio_file).stem.replace("_", " ").title()
    lines = [
        f'[From "{title}" — at {args.timestamp}]',
        "",
    ]

    for i, seg in enumerate(context_segs):
        abs_idx = start_idx + i
        ts_label = ms_to_ts(seg["start_ms"])
        voice = seg["voice"].upper()
        text = seg["text"]

        marker = " ◀ you are here" if abs_idx == hit_idx else ""
        lines.append(f"[{ts_label}] {voice}: {text}{marker}")

    if args.question:
        lines += ["", args.question]
    else:
        lines += ["", "[Your question:]", ""]

    output = "\n".join(lines)

    copy_to_clipboard(output)
    notify(args.question or "Context copied — paste into Claude chat.")
    print(output)
    print("─" * 60)
    print(f"Copied to clipboard. Paste into Claude chat.")
    print(f"(Transcript: {json_path.name}, hit segment {hit_idx + 1}/{len(segments)})")


if __name__ == "__main__":
    main()
