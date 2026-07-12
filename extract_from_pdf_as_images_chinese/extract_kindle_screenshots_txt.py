#!/usr/bin/env python3
"""
Extract text from Kindle screenshot images using OCR and split into chapter files.

Takes a folder of screenshots and:
1. OCRs each image in order
2. Detects chapter boundaries (number + title patterns)
3. Creates {input_folder}_txt/ with individual chapter files

Usage:
    python extract_kindle_screenshots_txt.py -i ./sports_injury
    # Creates: ./sports_injury_txt/
    #   ├── chapter_01_medicine.txt
    #   ├── chapter_02_*.txt
    #   └── ...

    # Interactive mode - manually mark chapter breaks:
    python extract_kindle_screenshots_txt.py -i ./sports_injury --interactive

Requirements:
    pip install Pillow pytesseract
    brew install tesseract  (macOS)
"""

import argparse
import os
import re
from pathlib import Path

from PIL import Image
import pytesseract


def ocr_images(input_path: str) -> str:
    """OCR all images in folder and return combined text."""
    image_extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.webp')

    image_files = sorted([
        f for f in os.listdir(input_path)
        if f.lower().endswith(image_extensions)
    ])

    if not image_files:
        print(f"No image files found in {input_path}")
        return ""

    print(f"Found {len(image_files)} images to OCR")

    all_text = ""
    for i, image_file in enumerate(image_files):
        image_path = os.path.join(input_path, image_file)
        print(f"  OCR ({i+1}/{len(image_files)}): {image_file}")

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            all_text += text + "\n\n"
        except Exception as e:
            print(f"    Error: {e}")

    return all_text


def clean_text(text: str) -> str:
    """Clean OCR artifacts and normalize whitespace."""
    # Remove common Kindle UI artifacts
    text = re.sub(r'\d+ minutes? left in chapter', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\d+%\s*$', '', text, flags=re.MULTILINE)

    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text.strip()


def detect_chapters(text: str) -> list[dict]:
    """
    Detect chapter boundaries in OCR'd text.

    Looks for patterns like:
    - Manual markers: "=== CHAPTER: Title ===" (from make_chapter_marker.py)
    - Standalone number (1, 2, 3...) followed by title
    - "Chapter X" or "CHAPTER X" patterns
    - Roman numerals (I, II, III...)
    - OCR'd decorative dots followed by single-word title (Kindle style)

    Returns list of {chapter_num, title, content, start_pos}
    """
    chapters = []

    # Pattern 0: Manual chapter markers from make_chapter_marker.py
    # Matches: "=== CHAPTER: Free-Range ===" or "===CHAPTER: Title==="
    pattern_manual = re.compile(
        r'={2,}\s*CHAPTER:\s*(.+?)\s*={2,}',
        re.IGNORECASE
    )

    # Pattern 1: Standalone number followed by decorative dots and title
    # Matches: "1\n...\nMedicine" or "2\n• • •\nTitle"
    pattern_num_title = re.compile(
        r'(?:^|\n\n+)'                          # Start or multiple newlines
        r'(\d{1,2})\s*\n'                       # Chapter number alone on line
        r'(?:[•\.\s\-_*]+\n)?'                  # Optional decorative line
        r'([A-Z][A-Za-z\s\-\'\"]+?)\s*\n',      # Title (capitalized)
        re.MULTILINE
    )

    # Pattern 2: "Chapter X: Title" or "CHAPTER X"
    pattern_chapter = re.compile(
        r'(?:^|\n\n+)'
        r'(?:CHAPTER|Chapter)\s+(\d+|[IVXLC]+)'  # Chapter + number/roman
        r'(?::\s*|\s+)'
        r'([A-Z][A-Za-z\s\-\'\"]*)?',            # Optional title
        re.MULTILINE
    )

    # Pattern 3: OCR'd decorative dots (gibberish) followed by single capitalized word
    # Catches Kindle chapter titles when number is lost/mangled by OCR
    # e.g., "eeoeeeeeeeeé\n\nMedicine" or "eoe0oe37e#eee@ee@\n\nWicked"
    # The decorative line often OCRs as repeated e, o, 0, @, or accented chars
    pattern_decorative_title = re.compile(
        r'(?:^|\n\n+)'
        r'[^\nA-Za-z]*[eo0@#]{3,}[^\n]*\s*\n+'  # OCR'd decorative line (3+ e/o/0/@ chars)
        r'([A-Z][a-z]{2,15})\s*\n',              # Single capitalized word (title)
        re.MULTILINE
    )

    # Try pattern 0 first (manual markers - highest priority)
    matches = list(pattern_manual.finditer(text))
    if matches:
        print(f"  Using manual chapter markers")
        # Manual markers only have title (group 1), handle specially
        manual_chapters = []
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start_pos = match.end()

            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            content = text[start_pos:end_pos].strip()
            manual_chapters.append({
                'chapter_num': i + 1,
                'title': title,
                'content': content,
                'start_pos': match.start()
            })
            print(f"    Chapter {i+1}: {title[:40]}... ({len(content):,} chars)")

        return manual_chapters

    # Try pattern 1 (Kindle style with number)
    matches = list(pattern_num_title.finditer(text))

    if not matches:
        # Try pattern 3 (OCR'd decorative + title)
        matches = list(pattern_decorative_title.finditer(text))
        if matches:
            print(f"  Using decorative-title pattern detection")

    if not matches:
        # Fall back to pattern 2
        matches = list(pattern_chapter.finditer(text))

    if not matches:
        # No chapters detected - treat as single document
        print("  No chapter markers detected - treating as single document")
        return [{
            'chapter_num': 1,
            'title': 'Full Text',
            'content': text,
            'start_pos': 0
        }]

    print(f"  Detected {len(matches)} chapter markers")

    # Check if this is a title-only pattern (pattern 3 has only 1 group)
    title_only_pattern = len(matches[0].groups()) == 1

    # Extract chapters
    for i, match in enumerate(matches):
        if title_only_pattern:
            # Pattern 3: only title captured, use sequential numbering
            chapter_num_int = i + 1
            title = match.group(1).strip()
        else:
            # Pattern 1 or 2: number and title captured
            chapter_num = match.group(1)
            title = match.group(2).strip() if match.group(2) else f"Chapter {chapter_num}"

            # Try to convert roman numerals to int
            try:
                chapter_num_int = int(chapter_num)
            except ValueError:
                # Roman numeral conversion
                roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
                chapter_num_int = 0
                prev = 0
                for char in reversed(chapter_num.upper()):
                    val = roman_map.get(char, 0)
                    if val < prev:
                        chapter_num_int -= val
                    else:
                        chapter_num_int += val
                    prev = val

        # Clean title
        title = re.sub(r'\s+', ' ', title).strip()
        title = title.rstrip('.')

        start_pos = match.end()

        # End position is start of next chapter or end of text
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)

        content = text[start_pos:end_pos].strip()

        chapters.append({
            'chapter_num': chapter_num_int,
            'title': title,
            'content': content,
            'start_pos': match.start()
        })

        print(f"    Chapter {chapter_num_int}: {title[:40]}... ({len(content):,} chars)")

    return chapters


def slugify(text: str) -> str:
    """Convert text to filename-safe slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text[:30].strip('_')


def save_chapters(chapters: list[dict], output_dir: str, book_name: str):
    """Save chapters to individual files."""
    os.makedirs(output_dir, exist_ok=True)

    for chapter in chapters:
        num = chapter['chapter_num']
        title = chapter['title']
        content = chapter['content']

        # Create filename
        title_slug = slugify(title)
        filename = f"chapter_{num:02d}_{title_slug}.txt"
        filepath = os.path.join(output_dir, filename)

        # Write chapter file with header
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {book_name}\n")
            f.write(f"# Chapter {num}: {title}\n")
            f.write("# " + "=" * 60 + "\n\n")
            f.write(content)

        print(f"  Saved: {filename}")

    # Write manifest
    manifest_path = os.path.join(output_dir, "manifest.txt")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(f"# {book_name} - Chapter Manifest\n")
        f.write(f"# Extracted from screenshots\n\n")
        for chapter in chapters:
            f.write(f"Chapter {chapter['chapter_num']}: {chapter['title']}\n")

    print(f"  Manifest: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract Kindle screenshots to chapter text files using OCR'
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input folder containing screenshot images')
    parser.add_argument('-o', '--output', default=None,
                        help='Output folder (default: {input}_txt)')
    parser.add_argument('-n', '--name', default=None,
                        help='Book name (default: derived from folder name)')
    parser.add_argument('--single', action='store_true',
                        help='Output single .txt file instead of splitting into chapters')

    args = parser.parse_args()

    input_path = args.input.rstrip('/')

    if not os.path.isdir(input_path):
        print(f"Error: {input_path} is not a directory")
        return

    # Derive output folder and book name
    folder_name = os.path.basename(input_path)
    output_dir = args.output or f"{input_path}_txt"
    book_name = args.name or folder_name.replace('_', ' ').replace('-', ' ').title()

    print(f"Book: {book_name}")
    print(f"Input: {input_path}/")
    print(f"Output: {output_dir}/")
    print()

    # Step 1: OCR all images
    print("Step 1: OCR images...")
    raw_text = ocr_images(input_path)

    if not raw_text:
        return

    # Step 2: Clean text
    print("\nStep 2: Cleaning OCR text...")
    clean = clean_text(raw_text)
    print(f"  Total text: {len(clean):,} characters")

    # Single file mode vs chapter splitting
    if args.single:
        # Output single text file
        output_file = args.output or f"{input_path}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {book_name}\n")
            f.write("# " + "=" * 60 + "\n\n")
            f.write(clean)
        print(f"\nDone! Saved to {output_file}")
        print("\nNext step (interactive chapter splitting):")
        print(f"  python split_chapters.py -i {output_file}")
    else:
        # Step 3: Detect chapters
        print("\nStep 3: Detecting chapters...")
        chapters = detect_chapters(clean)

        # Step 4: Save chapters
        print(f"\nStep 4: Saving {len(chapters)} chapters...")
        save_chapters(chapters, output_dir, book_name)

        print(f"\nDone! Chapters saved to {output_dir}/")
        print("\nNext step:")
        print(f"  python summarize_txt_chapters.py -i {output_dir} -o {folder_name}_summarized.txt")


if __name__ == "__main__":
    main()
