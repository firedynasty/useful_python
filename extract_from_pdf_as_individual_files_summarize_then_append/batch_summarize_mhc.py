#!/usr/bin/env python3
"""
Batch summarize Matthew Henry Commentary chapters - helper script for Claude Code.

This script helps coordinate summarization of extracted chapter text files.
Claude Code does the actual summarization work (no API key needed).

Usage:
    # List all chapters and progress
    python batch_summarize_mhc.py -i ./isaiah_txt/23_Isaiah -o isaiah_mhc_summarized.txt --book Isaiah --list

    # Continue from chapter 50 (for Claude Code to resume after compact)
    python batch_summarize_mhc.py -i ./isaiah_txt/23_Isaiah -o isaiah_mhc_summarized.txt --book Isaiah --continue 50

    # Initialize fresh output file
    python batch_summarize_mhc.py -i ./isaiah_txt/23_Isaiah -o isaiah_mhc_summarized.txt --book Isaiah --fresh

    # Show what chapters are pending
    python batch_summarize_mhc.py -i ./isaiah_txt/23_Isaiah -o isaiah_mhc_summarized.txt --book Isaiah --pending
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional


def get_chapter_number(filename: str) -> Optional[int]:
    """Extract chapter number from filename like ch040.txt -> 40"""
    match = re.match(r'ch(\d+)\.txt', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def get_existing_chapters(output_file: str) -> set[int]:
    """Parse existing output file to find which chapters are already summarized."""
    existing = set()
    if not os.path.exists(output_file):
        return existing

    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all "Chapter N:" patterns
    matches = re.findall(r'Chapter (\d+):', content)
    for m in matches:
        existing.add(int(m))

    return existing


def get_chapter_title(text: str, chapter: int) -> str:
    """Extract or generate a chapter title from the text."""
    lines = text.split('\n')[:10]
    for line in lines:
        line = line.strip()
        if line.startswith('#') or line.startswith('=') or not line:
            continue
        if 'chapter' in line.lower() or len(line) < 100:
            title = re.sub(r'^Chapter\s*\d+[:\s]*', '', line, flags=re.IGNORECASE)
            title = title.strip(' :-')
            if title and len(title) > 5:
                return title[:80]

    return f"Commentary on Chapter {chapter}"


def main():
    parser = argparse.ArgumentParser(
        description='Batch summarize MHC chapters - helper for Claude Code',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input directory with ch*.txt files')
    parser.add_argument('-o', '--output', required=True,
                        help='Output file for summaries')
    parser.add_argument('--book', required=True,
                        help='Book name (e.g., Isaiah, Genesis)')
    parser.add_argument('--continue', type=int, default=None, dest='continue_from',
                        help='Continue from chapter N (for resuming after compact)')
    parser.add_argument('--list', action='store_true',
                        help='List all chapters and their status')
    parser.add_argument('--pending', action='store_true',
                        help='Show pending chapters only')
    parser.add_argument('--fresh', action='store_true',
                        help='Start fresh (overwrite output file with header)')

    args = parser.parse_args()

    # Validate input directory
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input directory not found: {args.input}")
        sys.exit(1)

    # Find all chapter files
    chapter_files = sorted([
        f for f in input_path.glob('ch*.txt')
        if get_chapter_number(f.name) is not None
    ], key=lambda f: get_chapter_number(f.name))

    if not chapter_files:
        print(f"No chapter files found in {args.input}")
        sys.exit(1)

    # Get existing chapters
    existing_chapters = get_existing_chapters(args.output)

    # Fresh start - create new output file with header
    if args.fresh:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"BOOK: {args.book} - Matthew Henry Commentary (Summarized)\n")
            f.write("=" * 80 + "\n\n")
        print(f"Created fresh output file: {args.output}")
        existing_chapters = set()

    # List mode
    if args.list:
        print(f"\n{args.book} - Matthew Henry Commentary")
        print("=" * 50)
        print(f"Total chapters: {len(chapter_files)}")
        print(f"Completed: {len(existing_chapters)}")
        print(f"Pending: {len(chapter_files) - len(existing_chapters)}")
        print()
        for f in chapter_files:
            ch_num = get_chapter_number(f.name)
            status = "[DONE]" if ch_num in existing_chapters else "[    ]"
            print(f"  {status} Chapter {ch_num}: {f.name}")
        return

    # Pending mode
    if args.pending:
        pending = []
        for f in chapter_files:
            ch_num = get_chapter_number(f.name)
            if ch_num not in existing_chapters:
                pending.append(ch_num)

        if not pending:
            print("All chapters completed!")
        else:
            print(f"Pending chapters ({len(pending)}): {', '.join(map(str, pending))}")
            if pending:
                print(f"\nTo continue, run:")
                print(f"  python batch_summarize_mhc.py -i {args.input} -o {args.output} --book {args.book} --continue {pending[0]}")
        return

    # Continue mode - show info for Claude Code
    if args.continue_from is not None:
        chapters_to_do = []
        for f in chapter_files:
            ch_num = get_chapter_number(f.name)
            if ch_num >= args.continue_from and ch_num not in existing_chapters:
                chapters_to_do.append((ch_num, f))

        print(f"\n{args.book} - Continue from Chapter {args.continue_from}")
        print("=" * 50)
        print(f"Chapters to process: {len(chapters_to_do)}")
        print(f"Already completed: {len(existing_chapters)}")
        print()

        if chapters_to_do:
            print("Next chapters to summarize:")
            for ch_num, f in chapters_to_do[:10]:  # Show first 10
                print(f"  Chapter {ch_num}: {f}")
            if len(chapters_to_do) > 10:
                print(f"  ... and {len(chapters_to_do) - 10} more")
        else:
            print("All chapters from this point are done!")
        return

    # Default - show summary
    print(f"\n{args.book} - Matthew Henry Commentary")
    print("=" * 50)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Total chapters: {len(chapter_files)}")
    print(f"Completed: {len(existing_chapters)}")
    print(f"Pending: {len(chapter_files) - len(existing_chapters)}")
    print()
    print("Options:")
    print(f"  --list              Show all chapters and status")
    print(f"  --pending           Show pending chapters")
    print(f"  --fresh             Start fresh (overwrite output)")
    print(f"  --continue N        Continue from chapter N")


if __name__ == "__main__":
    main()
