#!/usr/bin/env python3
"""
Extract text from a folder of images (e.g. Kindle screenshots) using OpenAI GPT-4o vision,
then compile into a book context document compatible with 06-book_context_scraper.py.

Usage:
    python 07-extract_images_from_folder.py ./kindle_screenshots --title "Book Title"
    python 07-extract_images_from_folder.py ./ch1_imgs ./ch2_imgs --title "Book Title"

Output saved to ./scraped_from_websites/book_context_<title>_<timestamp>.txt
Also copied to clipboard.

Requires:
    export OPENAI_API_KEY="sk-..."
    pip install openai Pillow
"""

import argparse
import base64
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import openai
from PIL import Image


# ─── Configuration ────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif')
OUTPUT_DIR = "./scraped_from_websites"
MODEL = "gpt-4o"


# ─── Image Helpers ────────────────────────────────────────────────────────────

def image_to_base64(image_path: str) -> tuple[str, str]:
    """Convert image file to base64 string + media_type."""
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif',
        '.webp': 'image/webp',
    }

    # Convert unsupported formats to PNG first
    if ext in ('.bmp', '.tiff', '.tif'):
        img = Image.open(image_path)
        buf = BytesIO()
        img.save(buf, format='PNG')
        return base64.standard_b64encode(buf.getvalue()).decode('utf-8'), 'image/png'

    media_type = media_types.get(ext, 'image/jpeg')
    with open(image_path, 'rb') as f:
        return base64.standard_b64encode(f.read()).decode('utf-8'), media_type


def natural_sort_key(name: str):
    """Sort filenames with embedded numbers naturally (1, 2, 10 not 1, 10, 2)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', name)]


def collect_images(folders: list[str]) -> list[tuple[str, str]]:
    """
    Collect all image files from one or more folders, naturally sorted.
    Returns list of (folder_label, full_path) tuples.
    """
    collected = []
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"Warning: {folder} is not a directory, skipping.")
            continue
        files = sorted(
            [f for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTENSIONS)],
            key=natural_sort_key,
        )
        if not files:
            print(f"Warning: no images found in {folder}")
            continue
        label = os.path.basename(folder.rstrip('/'))
        for f in files:
            collected.append((label, os.path.join(folder, f)))
    return collected


# ─── Extraction ───────────────────────────────────────────────────────────────

def extract_text_from_image(client: openai.OpenAI, image_path: str) -> str:
    """Send a single image to GPT-4o and return extracted text."""
    b64_data, media_type = image_to_base64(image_path)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{b64_data}"
                    }
                },
                {
                    "type": "text",
                    "text": (
                        "Extract all the text from this image exactly as written. "
                        "Preserve paragraphs and line breaks. "
                        "Output only the extracted text, nothing else."
                    )
                }
            ]
        }]
    )
    return response.choices[0].message.content


def process_folder_images(client: openai.OpenAI, image_entries: list[tuple[str, str]]) -> list[dict]:
    """
    Extract text from each image. Returns list of result dicts grouped by folder.
    Each dict: {title, url, text, char_count}
    """
    # Group pages by folder label
    from collections import defaultdict
    pages_by_folder: dict[str, list[str]] = defaultdict(list)
    folder_order: list[str] = []

    total = len(image_entries)
    start_time = time.time()

    print(f"Extracting text from {total} image(s)...\n")

    for i, (label, path) in enumerate(image_entries, 1):
        filename = os.path.basename(path)
        page_start = time.time()

        try:
            text = extract_text_from_image(client, path)
            pages_by_folder[label].append(text)
            if label not in folder_order:
                folder_order.append(label)

            elapsed = time.time() - start_time
            avg = elapsed / i
            remaining = avg * (total - i)
            page_time = time.time() - page_start

            print(f"  [{i}/{total}] {label}/{filename} - {page_time:.1f}s "
                  f"(~{int(remaining // 60)}m {int(remaining % 60)}s remaining)")

        except Exception as e:
            print(f"  [{i}/{total}] ERROR {label}/{filename}: {e}")

    total_time = time.time() - start_time
    print(f"\nDone extracting: {total} pages in {int(total_time // 60)}m {int(total_time % 60)}s\n")

    # Build result dicts: one per folder
    results = []
    for label in folder_order:
        pages = pages_by_folder[label]
        combined = "\n\n".join(
            f"--- Page {j + 1} ---\n{page_text}"
            for j, page_text in enumerate(pages)
        )
        results.append({
            'title': f"Kindle Screenshots: {label}",
            'url': f"local folder: {label}/",
            'text': combined,
            'char_count': len(combined),
        })

    return results


# ─── Output Compilation ───────────────────────────────────────────────────────

def compile_context(results: list[dict], book_title: str) -> str:
    """Compile extracted results into a single context document."""
    header = f"# Book Context: {book_title}\n"
    header += f"# Sources: {len(results)} folder(s) of Kindle screenshots\n"
    header += f"# Compiled: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    toc = "## Sources\n"
    for i, r in enumerate(results, 1):
        toc += f"{i}. {r['title']}\n"
    toc += "\n"

    sections = []
    for i, r in enumerate(results, 1):
        section_header = f"\n{'=' * 80}\n"
        section_header += f"## Source {i}: {r['title']}\n"
        section_header += f"Folder: {r['url']}\n"
        section_header += f"{'=' * 80}\n\n"
        sections.append(section_header + r['text'])

    return header + toc + "\n".join(sections)


def create_safe_filename(title: str) -> str:
    safe = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    return safe[:50]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract text from Kindle screenshot folders using GPT-4o vision."
    )
    parser.add_argument(
        'folders', nargs='+',
        help='One or more folders containing Kindle screenshot images'
    )
    parser.add_argument(
        '--title', type=str, default=None,
        help='Book title (used in output filename and header)'
    )
    parser.add_argument(
        '--no-clipboard', action='store_true',
        help='Skip copying output to clipboard'
    )
    args = parser.parse_args()

    # API key check
    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not set.")
        print("Run: export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    client = openai.OpenAI()

    # Collect images
    image_entries = collect_images(args.folders)
    if not image_entries:
        print("No images found in the specified folder(s). Exiting.")
        sys.exit(1)

    print(f"Found {len(image_entries)} image(s) across {len(args.folders)} folder(s).")
    for folder in args.folders:
        count = sum(1 for label, _ in image_entries if label == os.path.basename(folder.rstrip('/')))
        print(f"  {folder}: {count} image(s)")
    print()

    # Extract text
    results = process_folder_images(client, image_entries)

    # Book title
    book_title = args.title
    if not book_title:
        book_title = input("Enter book title (for output filename): ").strip() or "book_context"

    # Compile
    document = compile_context(results, book_title)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_name = create_safe_filename(book_title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"book_context_{safe_name}_{timestamp}.txt")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(document)

    print(f"Saved to:  {filepath}")
    print(f"Size:      {len(document):,} characters")
    print(f"Sources:   {len(results)}")

    # Clipboard
    if not args.no_clipboard:
        try:
            subprocess.run(['pbcopy'], input=document.encode(), check=True)
            print("Copied to clipboard.")
        except Exception:
            print("Could not copy to clipboard.")


if __name__ == "__main__":
    main()
