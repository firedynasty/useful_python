#!/usr/bin/env python3
"""Convert markdown files in subfolders to MP3 using OpenAI TTS API."""

import os
import re
import sys
import time
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent

# OpenAI TTS caps input at 4096 chars per request; chunk below that.
MAX_CHARS = 3800


# Strip markdown formatting so TTS reads clean prose
def strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # headers
    text = re.sub(r"---+", "", text)  # horizontal rules
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)  # italic
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # links
    text = re.sub(r"`(.+?)`", r"\1", text)  # inline code
    text = re.sub(r"\n{3,}", "\n\n", text)  # excess newlines
    return text.strip()


def chunk_text(text: str, limit: int = MAX_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    # Prefer paragraph boundaries, then sentences, then hard slice.
    paragraphs = re.split(r"\n\n+", text)
    buf = ""
    for para in paragraphs:
        if len(para) > limit:
            if buf:
                chunks.append(buf.strip())
                buf = ""
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sent in sentences:
                if len(sent) > limit:
                    # Hard slice very long sentence
                    for i in range(0, len(sent), limit):
                        chunks.append(sent[i : i + limit])
                    continue
                if len(buf) + len(sent) + 1 > limit:
                    chunks.append(buf.strip())
                    buf = sent
                else:
                    buf = f"{buf} {sent}" if buf else sent
        elif len(buf) + len(para) + 2 > limit:
            chunks.append(buf.strip())
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def synthesize(
    api_key: str, text: str, model: str, voice: str, instructions: str | None
) -> bytes:
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": "mp3",
    }
    # `instructions` is only honored by gpt-4o-mini-tts (and newer steerable models).
    if instructions and model.startswith("gpt-4o"):
        payload["instructions"] = instructions

    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    response.raise_for_status()
    return response.content


def convert_file(
    api_key: str,
    md_path: Path,
    output_dir: Path,
    model: str,
    voice: str,
    instructions: str | None,
):
    mp3_path = output_dir / md_path.with_suffix(".mp3").name
    if mp3_path.exists():
        print(f"  SKIP (exists): {mp3_path.name}")
        return

    text = strip_markdown(md_path.read_text(encoding="utf-8"))
    if not text:
        print(f"  SKIP (empty): {md_path.name}")
        return

    chunks = chunk_text(text)
    print(f"  Converting: {md_path.name} ({len(text)} chars, {len(chunks)} chunk(s))...")

    with open(mp3_path, "wb") as f:
        for i, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                print(f"    chunk {i}/{len(chunks)} ({len(chunk)} chars)")
            f.write(synthesize(api_key, chunk, model, voice, instructions))
    print(f"  Created: {mp3_path.name}")


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)

    model = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    voice = os.environ.get("OPENAI_TTS_VOICE", "onyx")
    instructions = os.environ.get(
        "OPENAI_TTS_INSTRUCTIONS",
        (
            "Voice: warm, unhurried storybook narrator reading a bedtime Bible story "
            "to a child. Tone: gentle, reverent, and reassuring. Pace: slow and "
            "relaxed, with natural pauses at commas and between sentences. Emotion: "
            "calm wonder and affection. Pronounce biblical names clearly. Avoid any "
            "rushed or newsreader delivery."
        ),
    )

    # Process each subfolder in order
    folders = sorted(
        [d for d in BASE_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    if not folders:
        print("No subfolders found.")
        return

    parent_dir = BASE_DIR.parent  # one level up from storytime_output

    for folder in folders:
        md_files = sorted(folder.glob("*.md"))
        if not md_files:
            continue
        output_dir = parent_dir / f"{folder.name}_audio"
        output_dir.mkdir(exist_ok=True)
        print(f"\n=== {folder.name} -> {output_dir.name}/ ({len(md_files)} files) ===")
        for md_file in md_files:
            try:
                convert_file(api_key, md_file, output_dir, model, voice, instructions)
            except Exception as e:
                print(f"  ERROR on {md_file.name}: {e}")
                if "rate" in str(e).lower() or "429" in str(e):
                    print("  Rate limited — waiting 30s...")
                    time.sleep(30)

    print("\nDone!")


if __name__ == "__main__":
    main()
