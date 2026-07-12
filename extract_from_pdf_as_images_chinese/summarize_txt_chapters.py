#!/usr/bin/env python3
"""
Summarize chapter text files using Claude API and combine into single output.

Takes a folder of chapter .txt files (from extract_kindle_screenshots_txt.py)
and summarizes each chapter using the Anthropic API.

Usage:
    # Auto-summarize via Anthropic API
    python summarize_txt_chapters.py -i ./sports_injury_txt -o sports_injury_summarized.txt

    # Native mode: Claude Code interactive summarization
    python summarize_txt_chapters.py -i ./sports_injury_txt --native
    # Then Claude Code reads each chapter and saves *.summary.txt files

    # Combine summaries after native mode
    python summarize_txt_chapters.py -i ./sports_injury_txt --combine -o sports_injury_summarized.txt

    # Dry run (show what would be summarized)
    python summarize_txt_chapters.py -i ./sports_injury_txt --dry-run

    # Limit chapters (for testing)
    python summarize_txt_chapters.py -i ./sports_injury_txt -o output.txt --max-chapters 2

Requirements (for API mode only):
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional


def read_chapter_files(input_dir: str) -> list[dict]:
    """Read all chapter files from directory."""
    chapters = []

    # Find chapter files (chapter_XX_*.txt pattern)
    chapter_files = sorted([
        f for f in os.listdir(input_dir)
        if f.startswith('chapter_') and f.endswith('.txt')
    ])

    if not chapter_files:
        # Fall back to any .txt file that's not manifest
        chapter_files = sorted([
            f for f in os.listdir(input_dir)
            if f.endswith('.txt') and f != 'manifest.txt'
        ])

    for filename in chapter_files:
        filepath = os.path.join(input_dir, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to extract chapter number and title from header
        chapter_num = 0
        title = filename.replace('.txt', '').replace('_', ' ')

        # Parse header lines like "# Chapter 1: Medicine"
        header_match = re.search(r'#\s*Chapter\s+(\d+):\s*(.+)', content)
        if header_match:
            chapter_num = int(header_match.group(1))
            title = header_match.group(2).strip()

        # Also check filename pattern "chapter_01_title.txt"
        filename_match = re.match(r'chapter_(\d+)_(.+)\.txt', filename)
        if filename_match:
            chapter_num = int(filename_match.group(1))
            if not header_match:
                title = filename_match.group(2).replace('_', ' ').title()

        # Remove header lines from content for summarization
        content_lines = content.split('\n')
        content_start = 0
        for i, line in enumerate(content_lines):
            if line.startswith('#'):
                content_start = i + 1
            else:
                break
        clean_content = '\n'.join(content_lines[content_start:]).strip()

        chapters.append({
            'chapter_num': chapter_num,
            'title': title,
            'content': clean_content,
            'filename': filename,
            'chars': len(clean_content)
        })

    # Sort by chapter number
    chapters.sort(key=lambda x: x['chapter_num'])

    return chapters


def summarize_with_anthropic(content: str, chapter_num: int, title: str, book_name: str) -> str:
    """Summarize chapter using Anthropic API."""
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic()

    prompt = f"""Summarize this chapter from "{book_name}".

Chapter {chapter_num}: {title}

Focus on:
1. Main concepts and key arguments
2. Important facts, data, or research mentioned
3. Practical takeaways or applications
4. How this connects to the book's overall themes

Keep the summary concise but comprehensive (200-400 words).
Use clear paragraphs. Preserve important quotes or memorable phrases.

CHAPTER TEXT:
{content[:12000]}
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def mode_native(input_dir: str, book_name: str):
    """Native mode: Output chapters for Claude Code to summarize interactively."""
    chapters = read_chapter_files(input_dir)

    if not chapters:
        print("No chapter files found!")
        return

    # Check which chapters already have summaries
    pending = []
    completed = []

    for ch in chapters:
        summary_file = os.path.join(input_dir, ch['filename'].replace('.txt', '.summary.txt'))
        if os.path.exists(summary_file):
            completed.append(ch)
        else:
            pending.append(ch)

    print(f"Book: {book_name}")
    print(f"Total chapters: {len(chapters)}")
    print(f"Completed: {len(completed)}")
    print(f"Pending: {len(pending)}")
    print()

    if completed:
        print("Completed summaries:")
        for ch in completed:
            print(f"  [x] Chapter {ch['chapter_num']}: {ch['title']}")
        print()

    if not pending:
        print("All chapters summarized!")
        print(f"\nNext step:")
        print(f"  python summarize_txt_chapters.py -i {input_dir} --combine -o {book_name.lower().replace(' ', '_')}_summarized.txt")
        return

    print("Pending chapters for Claude Code to summarize:")
    print()

    for ch in pending:
        filepath = os.path.join(input_dir, ch['filename'])
        summary_path = filepath.replace('.txt', '.summary.txt')
        print(f"  Chapter {ch['chapter_num']}: {ch['title']}")
        print(f"    Read:  {filepath}")
        print(f"    Save:  {summary_path}")
        print()

    print("-" * 60)
    print("INSTRUCTIONS FOR CLAUDE CODE:")
    print("-" * 60)
    print(f"1. Read each chapter file listed above")
    print(f"2. Summarize focusing on:")
    print(f"   - Main concepts and key arguments")
    print(f"   - Important facts, data, or research")
    print(f"   - Practical takeaways")
    print(f"3. Save summary to the corresponding .summary.txt file")
    print(f"4. When done, run:")
    print(f"   python summarize_txt_chapters.py -i {input_dir} --combine -o {book_name.lower().replace(' ', '_')}_summarized.txt")


def mode_combine(input_dir: str, output_file: str, book_name: str):
    """Combine individual .summary.txt files into single output."""
    chapters = read_chapter_files(input_dir)

    if not chapters:
        print("No chapter files found!")
        return

    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append(f"BOOK: {book_name}")
    output_lines.append("=" * 80)
    output_lines.append("")

    found = 0
    missing = []

    for ch in chapters:
        summary_file = os.path.join(input_dir, ch['filename'].replace('.txt', '.summary.txt'))

        if os.path.exists(summary_file):
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = f.read().strip()

            output_lines.append(f"Chapter {ch['chapter_num']}: {ch['title']}")
            output_lines.append("-" * 40)
            output_lines.append(summary)
            output_lines.append("")
            found += 1
            print(f"  [x] Chapter {ch['chapter_num']}: {ch['title']}")
        else:
            missing.append(ch)
            print(f"  [ ] Chapter {ch['chapter_num']}: {ch['title']} (missing summary)")

    if missing:
        print(f"\nWarning: {len(missing)} chapters missing summaries")
        print("Run --native mode to see pending chapters")

    if found == 0:
        print("\nNo summaries found to combine!")
        return

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\nCombined {found} summaries to: {output_file}")

    folder_name = os.path.basename(input_dir.rstrip('/')).replace('_txt', '')
    print(f"\nNext step:")
    print(f"  python create_rag_from_text.py {output_file} -o rag_{folder_name}")


def main():
    parser = argparse.ArgumentParser(
        description='Summarize chapter text files using Claude API or Claude Code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  (default)     Auto-summarize using Anthropic API
  --native      Output chapters for Claude Code to summarize interactively
  --combine     Combine individual .summary.txt files into single output
  --dry-run     Show chapters without summarizing

Workflow with Claude Code (--native):
  1. python summarize_txt_chapters.py -i ./book_txt --native
  2. Claude Code reads each chapter, summarizes, saves as *.summary.txt
  3. python summarize_txt_chapters.py -i ./book_txt --combine -o book_summarized.txt
  4. python create_rag_from_text.py book_summarized.txt -o rag_book
        """
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input folder containing chapter .txt files')
    parser.add_argument('-o', '--output', default='summarized.txt',
                        help='Output file for combined summaries')
    parser.add_argument('-n', '--name', default=None,
                        help='Book name (default: derived from folder name)')
    parser.add_argument('--native', action='store_true',
                        help='Native mode: output chapters for Claude Code to summarize')
    parser.add_argument('--combine', action='store_true',
                        help='Combine individual .summary.txt files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show chapters without summarizing')
    parser.add_argument('--max-chapters', type=int, default=None,
                        help='Limit number of chapters to process')

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: {args.input} is not a directory")
        return

    # Derive book name from folder
    folder_name = os.path.basename(args.input.rstrip('/'))
    book_name = args.name or folder_name.replace('_txt', '').replace('_', ' ').title()

    # Handle different modes
    if args.native:
        mode_native(args.input, book_name)
        return

    if args.combine:
        mode_combine(args.input, args.output, book_name)
        return

    # Default: API summarization mode
    print(f"Book: {book_name}")
    print(f"Input: {args.input}/")
    print(f"Output: {args.output}")
    print()

    # Read chapters
    print("Reading chapter files...")
    chapters = read_chapter_files(args.input)

    if not chapters:
        print("No chapter files found!")
        return

    print(f"Found {len(chapters)} chapters:\n")
    for ch in chapters:
        print(f"  {ch['chapter_num']:2d}. {ch['title'][:40]:<40} ({ch['chars']:,} chars)")

    if args.dry_run:
        print("\n[Dry run - no summaries generated]")
        return

    # Apply max chapters limit
    if args.max_chapters:
        chapters = chapters[:args.max_chapters]
        print(f"\nLimiting to first {args.max_chapters} chapters")

    # Summarize each chapter
    print(f"\nSummarizing {len(chapters)} chapters...")

    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append(f"BOOK: {book_name}")
    output_lines.append("=" * 80)
    output_lines.append("")

    for i, ch in enumerate(chapters):
        print(f"\n  ({i+1}/{len(chapters)}) Chapter {ch['chapter_num']}: {ch['title'][:30]}...")

        try:
            summary = summarize_with_anthropic(
                ch['content'],
                ch['chapter_num'],
                ch['title'],
                book_name
            )

            output_lines.append(f"Chapter {ch['chapter_num']}: {ch['title']}")
            output_lines.append("-" * 40)
            output_lines.append(summary)
            output_lines.append("")

            print(f"    Done ({len(summary)} chars)")

        except Exception as e:
            print(f"    Error: {e}")
            output_lines.append(f"Chapter {ch['chapter_num']}: {ch['title']}")
            output_lines.append(f"[Error summarizing: {e}]")
            output_lines.append("")

    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\nSaved summaries to: {args.output}")
    print(f"\nNext step:")
    print(f"  python create_rag_from_text.py {args.output} -o rag_{folder_name.replace('_txt', '')}")


if __name__ == "__main__":
    main()
