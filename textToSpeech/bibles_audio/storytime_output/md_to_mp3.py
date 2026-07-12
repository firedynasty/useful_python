#!/usr/bin/env python3
"""Convert markdown files in subfolders to MP3 using NOIZ TTS API."""

import os
import re
import sys
import time
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent


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


def convert_file(api_key: str, md_path: Path, output_dir: Path, voice_id: str):
    mp3_path = output_dir / md_path.with_suffix(".mp3").name
    if mp3_path.exists():
        print(f"  SKIP (exists): {mp3_path.name}")
        return

    text = strip_markdown(md_path.read_text(encoding="utf-8"))
    if not text:
        print(f"  SKIP (empty): {md_path.name}")
        return

    print(f"  Converting: {md_path.name} ({len(text)} chars)...")
    response = requests.post(
        "https://noiz.ai/v1/text-to-speech",
        headers={"Authorization": api_key},
        files={
            "text": (None, text),
            "voice_id": (None, voice_id),
            "output_format": (None, "mp3"),
        },
    )
    response.raise_for_status()

    with open(mp3_path, "wb") as f:
        f.write(response.content)
    print(f"  Created: {mp3_path.name}")


def main():
    api_key = os.environ.get("NOIZ_API_KEY")
    if not api_key:
        print("Error: NOIZ_API_KEY not set")
        sys.exit(1)

    voice_id = "95814add"

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
                convert_file(api_key, md_file, output_dir, voice_id)
            except Exception as e:
                print(f"  ERROR on {md_file.name}: {e}")
                if "rate" in str(e).lower() or "429" in str(e):
                    print("  Rate limited — waiting 30s...")
                    time.sleep(30)

    print("\nDone!")


if __name__ == "__main__":
    main()
