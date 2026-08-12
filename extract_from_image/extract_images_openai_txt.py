#!/usr/bin/env python3
"""
Extract text from image(s) using OpenAI GPT-4o Vision API.

Accepts a single image file or a folder of images.
Processes images in natural sort order and writes text incrementally.
Optionally saves the images as a concatenated multi-page PDF.

Usage:
    # Single image
    python extract_images_openai_txt.py -i page0.png -o output.txt

    # Folder of screenshots
    python extract_images_openai_txt.py -i ./screenshots -o output.txt

    # Folder → text + also save as PDF
    python extract_images_openai_txt.py -i ./screenshots -o output.txt --pdf combined.pdf

Requirements:
    pip install openai pillow
    export OPENAI_API_KEY=sk-...
"""

import argparse
import base64
import os
import re
import sys
import time
from pathlib import Path


IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.webp')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def natural_sort_key(s: str):
    """Sort key that handles embedded numbers correctly (1, 2, 10 not 1, 10, 2)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def collect_images(input_path: str) -> list[Path]:
    """Return sorted list of image Paths from a file or directory."""
    p = Path(input_path)
    if p.is_file():
        if p.suffix.lower() not in IMAGE_EXTENSIONS:
            print(f"Error: {p} is not a supported image file.", file=sys.stderr)
            sys.exit(1)
        return [p]
    elif p.is_dir():
        files = [
            f for f in p.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        if not files:
            print(f"Error: No image files found in {p}", file=sys.stderr)
            sys.exit(1)
        return sorted(files, key=lambda f: natural_sort_key(f.name))
    else:
        print(f"Error: {input_path} is not a file or directory.", file=sys.stderr)
        sys.exit(1)


def encode_image(image_path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type) for an image file."""
    ext = image_path.suffix.lower()
    media_map = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif',
        '.webp': 'image/webp', '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
    }
    media_type = media_map.get(ext, 'image/png')
    with open(image_path, 'rb') as f:
        data = base64.standard_b64encode(f.read()).decode('utf-8')
    return data, media_type


def save_as_pdf(image_paths: list[Path], pdf_path: str):
    """Concatenate images into a multi-page PDF using Pillow."""
    try:
        from PIL import Image
    except ImportError:
        print("Warning: Pillow not installed — skipping PDF creation. Run: pip install pillow",
              file=sys.stderr)
        return

    images = []
    for p in image_paths:
        try:
            img = Image.open(p).convert('RGB')
            images.append(img)
        except Exception as e:
            print(f"  Warning: could not open {p.name} for PDF: {e}", file=sys.stderr)

    if not images:
        return

    first, rest = images[0], images[1:]
    first.save(pdf_path, save_all=True, append_images=rest)
    print(f"PDF saved: {pdf_path}")


# ---------------------------------------------------------------------------
# OpenAI Vision call
# ---------------------------------------------------------------------------

def extract_text_from_image(client, image_path: Path, prompt: str) -> str:
    """Send one image to GPT-4o and return the extracted text."""
    data, media_type = encode_image(image_path)

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:{media_type};base64,{data}',
                            'detail': 'high',
                        },
                    },
                    {'type': 'text', 'text': prompt},
                ],
            }
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(input_path: str, output_file: str, pdf_path: str | None, prompt: str):
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai is not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    image_paths = collect_images(input_path)
    total = len(image_paths)
    print(f"Found {total} image(s) to process")
    print(f"Output: {output_file}")

    # Optionally build PDF first
    if pdf_path:
        print(f"Building PDF from {total} image(s)...")
        save_as_pdf(image_paths, pdf_path)

    # Ensure output directory exists
    out = Path(output_file)
    if out.parent != Path('.'):
        out.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    error_count = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, img_path in enumerate(image_paths):
            page_start = time.time()
            print(f"[{i+1}/{total}] {img_path.name} ...", end=' ', flush=True)

            try:
                text = extract_text_from_image(client, img_path, prompt)

                # Write page separator (skip leading separator on first page)
                if i > 0:
                    f.write(f"\n{'='*50}\nPAGE {i+1} — {img_path.name}\n{'='*50}\n\n")
                else:
                    f.write(f"PAGE 1 — {img_path.name}\n{'='*50}\n\n")

                f.write(text + '\n')
                f.flush()

                elapsed = time.time() - page_start
                remaining = (time.time() - start_time) / (i + 1) * (total - i - 1)
                print(f"done ({elapsed:.1f}s, ~{int(remaining//60)}m{int(remaining%60)}s left)")

            except Exception as e:
                error_count += 1
                print(f"ERROR: {e}", file=sys.stderr)

    total_time = time.time() - start_time
    print(f"\nComplete: {total - error_count}/{total} pages in "
          f"{int(total_time//60)}m{int(total_time%60)}s")
    if error_count:
        print(f"Errors: {error_count}")
    print(f"Saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract text from image(s) using OpenAI GPT-4o Vision'
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Image file or folder of images')
    parser.add_argument('-o', '--output', default='./extracted_text.txt',
                        help='Output .txt file (default: ./extracted_text.txt)')
    parser.add_argument('--pdf', default=None, metavar='PDF_PATH',
                        help='Also save all images as a multi-page PDF at this path')
    parser.add_argument('--prompt', default=(
        'Please extract and transcribe ALL text visible in this image exactly as it appears. '
        'Preserve line breaks, punctuation, and any Chinese/English mix. '
        'Do not add commentary — output only the transcribed text.'
    ), help='Prompt sent to GPT-4o for each image (override to customise extraction)')

    args = parser.parse_args()
    run(args.input, args.output, args.pdf, args.prompt)


if __name__ == '__main__':
    main()
