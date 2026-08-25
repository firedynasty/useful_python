"""
Stream a file (or clipboard) aloud with local Kokoro — zero lag.

Instead of generating the full audio then playing it, this script feeds
each Kokoro chunk straight into a sounddevice OutputStream as it arrives.
Playback starts within ~1 second of launch.

Usage:
    pip install kokoro-onnx sounddevice numpy
    python speak_file_kokoro.py myfile.txt
    python speak_file_kokoro.py myfile.md
    python speak_file_kokoro.py myfile.rtf      # RTF supported via macOS textutil
    python speak_file_kokoro.py -c              # from clipboard
    python speak_file_kokoro.py myfile.txt -v af_bella
    python speak_file_kokoro.py myfile.txt --speed 1.2

Available voices (good defaults):
    am_michael  — American male, warm        (default)
    af_bella    — American female, curious
    bm_george   — British male, authoritative
    bf_emma     — British female, clear
    am_adam     — American male, deep
    af_nicole   — American female, smooth
    af_sarah    — American female, bright
    bm_lewis    — British male, calm
"""

import argparse
import asyncio
import queue
import subprocess
import sys
import termios
import threading
import tty
from pathlib import Path

import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro

# --- Config ---

_DIR = Path(__file__).parent
KOKORO_MODEL = _DIR / "kokoro-v1.0.onnx"
VOICES_BIN   = _DIR / "voices-v1.0.bin"

SAMPLE_RATE   = 24000
DEFAULT_VOICE = "am_michael"
DEFAULT_SPEED = 1.0

# How large the playback buffer is (in samples). Bigger = smoother on slow
# machines; smaller = less latency before first sound.
BLOCKSIZE = 4096

# Sentinel that tells the playback thread the stream is done
_DONE = object()


# --- Clipboard ---

def get_clipboard() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: could not read clipboard", file=sys.stderr)
        sys.exit(1)
    text = result.stdout.strip()
    if not text:
        print("Error: clipboard is empty", file=sys.stderr)
        sys.exit(1)
    return text


# --- File reading ---

def read_file(filepath: Path) -> str:
    """Read a file to plain text. RTF is converted via macOS textutil."""
    if filepath.suffix.lower() == ".rtf":
        result = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(filepath)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"Error converting RTF: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        return result.stdout
    return filepath.read_text(encoding="utf-8")


# --- Text splitting ---

def split_paragraphs(text: str) -> list[str]:
    """
    Split text into speakable chunks at blank lines or very long paragraphs.
    Each chunk is fed to Kokoro separately so we can show progress.
    """
    chunks = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        # Collapse internal newlines to spaces
        block = " ".join(line.strip() for line in block.splitlines() if line.strip())
        chunks.append(block)
    return chunks


# --- Key listener ---

def _key_listener(stop_event: threading.Event) -> None:
    """Background thread: set stop_event when the user presses q, Q, or space."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while not stop_event.is_set():
            ch = sys.stdin.read(1)
            if ch in ("q", "Q", " "):
                stop_event.set()
                break
    except Exception:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# --- Streaming playback ---

async def _generate_to_queue(kokoro: Kokoro, voice: str, text: str,
                              speed: float, audio_q: queue.Queue,
                              stop_event: threading.Event) -> None:
    """Async: stream Kokoro chunks into audio_q as float32 numpy arrays."""
    stream = kokoro.create_stream(text, voice=voice, speed=speed, lang="en-us")
    async for samples, _sr in stream:
        if stop_event.is_set():
            break
        audio_q.put(samples.astype(np.float32))


def _playback_thread(audio_q: queue.Queue, done_event: threading.Event,
                     stop_event: threading.Event) -> None:
    """
    Reads float32 chunks from audio_q and plays them through sounddevice.
    Runs in its own thread so it doesn't block the asyncio event loop.
    """
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                         blocksize=BLOCKSIZE) as stream:
        while not stop_event.is_set():
            try:
                chunk = audio_q.get(timeout=0.1)
            except queue.Empty:
                continue
            if chunk is _DONE:
                break
            stream.write(chunk)
    done_event.set()


def speak_chunk(kokoro: Kokoro, voice: str, text: str, speed: float,
                stop_event: threading.Event) -> None:
    """Generate and play one text chunk with zero lag."""
    audio_q: queue.Queue = queue.Queue(maxsize=32)  # bounded to avoid memory runaway
    done_event = threading.Event()

    # Start the playback thread first — it will block waiting for audio
    t = threading.Thread(target=_playback_thread,
                         args=(audio_q, done_event, stop_event), daemon=True)
    t.start()

    # Run async generation in this thread's event loop, feeding the queue
    asyncio.run(_generate_to_queue(kokoro, voice, text, speed, audio_q, stop_event))

    # Signal playback thread that generation is complete
    audio_q.put(_DONE)

    # Wait for all queued audio to finish playing
    done_event.wait()


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Stream a file aloud with local Kokoro — zero lag"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("file", nargs="?", help="Path to .txt, .md, or .rtf file")
    source.add_argument("-c", "--clipboard", action="store_true",
                        help="Read from clipboard instead of a file")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE,
                        help=f"Kokoro voice name (default: {DEFAULT_VOICE})")
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED,
                        help=f"Speaking speed multiplier (default: {DEFAULT_SPEED})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show parsed chunks without speaking")
    args = parser.parse_args()

    # Read input
    if args.clipboard:
        print("Reading from clipboard...")
        text = get_clipboard()
    else:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        print(f"Reading {filepath}...")
        text = read_file(filepath)

    chunks = split_paragraphs(text)
    if not chunks:
        print("Error: no speakable content found", file=sys.stderr)
        sys.exit(1)

    print(f"  {len(chunks)} paragraph(s) | voice: {args.voice} | speed: {args.speed}x")

    if args.dry_run:
        print()
        for i, c in enumerate(chunks, 1):
            print(f"  [{i}] {c[:100]}{'...' if len(c) > 100 else ''}")
        print("\n(dry run — no audio)")
        return

    if not KOKORO_MODEL.exists() or not VOICES_BIN.exists():
        print(f"Error: Kokoro model files not found in {_DIR}", file=sys.stderr)
        print(f"  Expected: {KOKORO_MODEL.name} and {VOICES_BIN.name}", file=sys.stderr)
        sys.exit(1)

    print("Loading Kokoro model...")
    kokoro = Kokoro(str(KOKORO_MODEL), str(VOICES_BIN))

    stop_event = threading.Event()
    listener = threading.Thread(target=_key_listener, args=(stop_event,), daemon=True)
    listener.start()

    print("Speaking... (press q or space to stop)\n")
    try:
        for i, chunk in enumerate(chunks, 1):
            if stop_event.is_set():
                break
            preview = chunk[:80] + ("..." if len(chunk) > 80 else "")
            print(f"  [{i}/{len(chunks)}] {preview}")
            speak_chunk(kokoro, args.voice, chunk, args.speed, stop_event)
    except KeyboardInterrupt:
        stop_event.set()

    if stop_event.is_set():
        print("\nStopped.")


if __name__ == "__main__":
    main()
