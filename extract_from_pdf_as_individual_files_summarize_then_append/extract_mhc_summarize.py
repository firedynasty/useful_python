#!/usr/bin/env python3
"""
Extract Matthew Henry Commentary HTML files, summarize each chapter, and output for RAG.

Two modes:
1. --extract-only: Extract chapters to individual txt files for Claude Code to summarize
2. --summarize: Use Anthropic API to auto-summarize each chapter

Usage:
    # Mode 1: Extract chapters for manual/Claude Code summarization
    python extract_mhc_summarize.py -i ./matthew_henry --extract-only -o ./mhc_chapters/
    # Then Claude Code processes each file and creates summaries

    # Mode 2: Auto-summarize using Anthropic API
    python extract_mhc_summarize.py -i ./matthew_henry --summarize -o mhc_summarized.txt

Output format (compatible with create_rag_from_text.py):
    ================================================================================
    BOOK: Genesis
    ================================================================================

    Chapter 1: [Summary of Genesis chapter 1 commentary]

    Chapter 2: [Summary of Genesis chapter 2 commentary]
    ...
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Book number to name mapping
BOOK_MAP = {
    "01": "Genesis", "02": "Exodus", "03": "Leviticus", "04": "Numbers",
    "05": "Deuteronomy", "06": "Joshua", "07": "Judges", "08": "Ruth",
    "09": "1 Samuel", "10": "2 Samuel", "11": "1 Kings", "12": "2 Kings",
    "13": "1 Chronicles", "14": "2 Chronicles", "15": "Ezra", "16": "Nehemiah",
    "17": "Esther", "18": "Job", "19": "Psalms", "20": "Proverbs",
    "21": "Ecclesiastes", "22": "Song of Solomon", "23": "Isaiah", "24": "Jeremiah",
    "25": "Lamentations", "26": "Ezekiel", "27": "Daniel", "28": "Hosea",
    "29": "Joel", "30": "Amos", "31": "Obadiah", "32": "Jonah",
    "33": "Micah", "34": "Nahum", "35": "Habakkuk", "36": "Zephaniah",
    "37": "Haggai", "38": "Zechariah", "39": "Malachi",
    "40": "Matthew", "41": "Mark", "42": "Luke", "43": "John",
    "44": "Acts", "45": "Romans", "46": "1 Corinthians", "47": "2 Corinthians",
    "48": "Galatians", "49": "Ephesians", "50": "Philippians", "51": "Colossians",
    "52": "1 Thessalonians", "53": "2 Thessalonians", "54": "1 Timothy",
    "55": "2 Timothy", "56": "Titus", "57": "Philemon", "58": "Hebrews",
    "59": "James", "60": "1 Peter", "61": "2 Peter", "62": "1 John",
    "63": "2 John", "64": "3 John", "65": "Jude", "66": "Revelation"
}


def html_to_text(html_content: str) -> str:
    """Convert HTML to plain text."""
    text = html_content

    # Remove script/style
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert block elements
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?div[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?h\d[^>]*>', '\n', text, flags=re.IGNORECASE)

    # Remove remaining tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&mdash;', '—')
    text = text.replace('&ndash;', '–')
    text = text.replace('&ldquo;', '"')
    text = text.replace('&rdquo;', '"')
    text = text.replace('&lsquo;', ''')
    text = text.replace('&rsquo;', ''')

    # Clean whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def parse_mhc_filename(filename: str) -> Optional[tuple[str, int]]:
    """Parse MHC filename: MHC01001.HTM -> ("01", 1)"""
    match = re.match(r'MHC(\d{2})(\d{3})\.HTM?', filename, re.IGNORECASE)
    if match:
        return match.group(1), int(match.group(2))
    return None


def summarize_with_anthropic(text: str, book: str, chapter: int) -> str:
    """Summarize chapter using Anthropic API."""
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic()

    prompt = f"""Summarize this Matthew Henry Commentary on {book} Chapter {chapter}.

Focus on:
1. Main theological themes and interpretations
2. Key practical applications Matthew Henry draws
3. Notable verse-by-verse insights
4. Cross-references to other scripture

Keep the summary concise but comprehensive (300-500 words). Use clear paragraphs.
Preserve important quotes or memorable phrases from the original.

COMMENTARY TEXT:
{text[:15000]}  # Truncate very long chapters
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def extract_chapters(input_dir: str) -> dict:
    """Extract all chapters grouped by book."""
    mhc_files = sorted([
        f for f in os.listdir(input_dir)
        if f.upper().startswith('MHC') and f.upper().endswith(('.HTM', '.HTML'))
    ])

    if not mhc_files:
        print(f"No MHC files found in {input_dir}")
        return {}

    books = {}
    for filename in mhc_files:
        parsed = parse_mhc_filename(filename)
        if parsed:
            book_num, chapter = parsed
            if book_num not in books:
                books[book_num] = []

            filepath = os.path.join(input_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    html = f.read()
                text = html_to_text(html)
                books[book_num].append({
                    'chapter': chapter,
                    'filename': filename,
                    'text': text
                })
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    # Sort chapters within each book
    for book_num in books:
        books[book_num].sort(key=lambda x: x['chapter'])

    return books


def mode_extract_only(input_dir: str, output_dir: str):
    """Extract chapters to individual files for Claude Code processing."""
    books = extract_chapters(input_dir)

    if not books:
        return

    os.makedirs(output_dir, exist_ok=True)

    # Create a manifest file for tracking
    manifest = []

    for book_num in sorted(books.keys()):
        book_name = BOOK_MAP.get(book_num, f"Book{book_num}")
        book_dir = os.path.join(output_dir, f"{book_num}_{book_name.replace(' ', '_')}")
        os.makedirs(book_dir, exist_ok=True)

        for chapter_data in books[book_num]:
            chapter = chapter_data['chapter']
            text = chapter_data['text']

            # Write chapter file
            chapter_file = os.path.join(book_dir, f"ch{chapter:03d}.txt")
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(f"# {book_name} Chapter {chapter}\n")
                f.write(f"# Source: {chapter_data['filename']}\n")
                f.write("# " + "="*70 + "\n\n")
                f.write(text)

            manifest.append({
                'book_num': book_num,
                'book_name': book_name,
                'chapter': chapter,
                'file': chapter_file,
                'chars': len(text)
            })
            print(f"Extracted: {book_name} Chapter {chapter} ({len(text):,} chars)")

    # Write manifest
    manifest_file = os.path.join(output_dir, "manifest.txt")
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write("# MHC Extraction Manifest\n")
        f.write("# Use this to track summarization progress\n\n")
        for entry in manifest:
            f.write(f"{entry['book_name']} Ch.{entry['chapter']}: {entry['file']}\n")

    print(f"\nExtracted {len(manifest)} chapters to {output_dir}/")
    print(f"Manifest: {manifest_file}")
    print("\nNext steps:")
    print("1. Claude Code reads each chapter file")
    print("2. Summarizes and writes to output")
    print("3. Run create_rag_from_text.py on the summarized output")


def get_completed_chapters(output_file: str) -> set[int]:
    """Check which chapters are already summarized in output file."""
    completed = set()
    if not os.path.exists(output_file):
        return completed
    with open(output_file, 'r', encoding='utf-8') as f:
        for match in re.finditer(r'^Chapter (\d+)$', f.read(), re.MULTILINE):
            completed.add(int(match.group(1)))
    return completed


def mode_summarize(input_dir: str, output_file: str, max_chapters: Optional[int] = None):
    """Auto-summarize using Anthropic API. Writes incrementally and can resume."""
    books = extract_chapters(input_dir)

    if not books:
        return

    total_chapters = sum(len(chs) for chs in books.values())
    if max_chapters:
        total_chapters = min(total_chapters, max_chapters)

    # Check for existing progress
    completed = get_completed_chapters(output_file)
    if completed:
        print(f"Found {len(completed)} existing chapters, resuming...")

    processed = 0
    newly_done = 0

    for book_num in sorted(books.keys()):
        book_name = BOOK_MAP.get(book_num, f"Book {book_num}")

        # Write book header if file doesn't exist or is empty
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n")
                f.write("=" * 80 + "\n")
                f.write(f"BOOK: {book_name}\n")
                f.write("=" * 80 + "\n\n")

        for chapter_data in books[book_num]:
            if max_chapters and processed >= max_chapters:
                break

            chapter = chapter_data['chapter']
            text = chapter_data['text']

            # Skip already completed chapters
            if chapter in completed:
                print(f"Skipping ({processed + 1}/{total_chapters}): {book_name} Chapter {chapter} (already done)")
                processed += 1
                continue

            print(f"Summarizing ({processed + 1}/{total_chapters}): {book_name} Chapter {chapter}...")

            try:
                summary = summarize_with_anthropic(text, book_name, chapter)

                # Append immediately to file
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"Chapter {chapter}\n")
                    f.write("-" * 40 + "\n")
                    f.write(summary + "\n\n")

                newly_done += 1

            except Exception as e:
                print(f"  Error: {e}")
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"Chapter {chapter}\n")
                    f.write(f"[Error summarizing: {e}]\n\n")

            processed += 1

        if max_chapters and processed >= max_chapters:
            break

    print(f"\nSaved summarized commentary to: {output_file}")
    print(f"Processed {processed} chapters ({newly_done} new, {len(completed)} resumed)")


def mode_combine_summaries(input_dir: str, output_file: str):
    """Combine individual summary files into one output."""
    # Look for summary files in the structure created by extract_only
    summaries = []

    for book_dir in sorted(Path(input_dir).iterdir()):
        if not book_dir.is_dir():
            continue

        # Look for summary files (*.summary.txt)
        for summary_file in sorted(book_dir.glob("*.summary.txt")):
            with open(summary_file, 'r', encoding='utf-8') as f:
                summaries.append(f.read())

    if not summaries:
        print(f"No summary files found in {input_dir}")
        print("Expected pattern: <book_dir>/*.summary.txt")
        return

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summaries))

    print(f"Combined {len(summaries)} summaries to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract and summarize Matthew Henry Commentary for RAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  --extract-only    Extract chapters to individual files for Claude Code to summarize
  --summarize       Auto-summarize using Anthropic API
  --combine         Combine individual summary files into one output

Workflow with Claude Code:
  1. python extract_mhc_summarize.py -i ./mhc --extract-only -o ./mhc_chapters
  2. Claude Code reads each chapter, summarizes, saves as ch001.summary.txt
  3. python extract_mhc_summarize.py --combine -i ./mhc_chapters -o mhc_summarized.txt
  4. python create_rag_from_text.py mhc_summarized.txt -o rag_mhc
        """
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input directory with MHC*.HTM files (or extracted chapters for --combine)')
    parser.add_argument('-o', '--output', required=True,
                        help='Output path (directory for --extract-only, file for others)')
    parser.add_argument('--extract-only', action='store_true',
                        help='Extract chapters to individual files only')
    parser.add_argument('--summarize', action='store_true',
                        help='Auto-summarize using Anthropic API')
    parser.add_argument('--combine', action='store_true',
                        help='Combine individual summary files')
    parser.add_argument('--max-chapters', type=int, default=None,
                        help='Limit number of chapters to process (for testing)')

    args = parser.parse_args()

    if args.extract_only:
        mode_extract_only(args.input, args.output)
    elif args.summarize:
        mode_summarize(args.input, args.output, args.max_chapters)
    elif args.combine:
        mode_combine_summaries(args.input, args.output)
    else:
        print("Error: Specify --extract-only, --summarize, or --combine")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
