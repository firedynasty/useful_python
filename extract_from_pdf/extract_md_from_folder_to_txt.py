#!/usr/bin/env python3
"""
Extract markdown files from a folder and combine into a single text file for RAG creation.

Usage:
    python extract_md_from_folder_to_txt.py -i ./06-recipes -o recipes_combined.txt
    python extract_md_from_folder_to_txt.py -i ./06-recipes  # outputs to 06-recipes_combined.txt

This script:
1. Scans folder for .md files
2. Preserves markdown headers (# ## ###) for section detection
3. Adds filename-based headers for files without proper headers
4. Combines all content into a single .txt file

The output file can be used with create_rag_from_text.py:
    python create_rag_from_text.py recipes_combined.txt -o rag_recipes --name "Recipes"
"""

import argparse
import os
import re
from pathlib import Path


def natural_sort_key(s: str) -> list:
    """Sort strings with numbers in natural order (1, 2, 10 instead of 1, 10, 2)."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def filename_to_header(filename: str) -> str:
    """
    Convert filename to a readable header.

    Examples:
        'yam_noodles_recipe.md' -> 'Yam Noodles Recipe'
        'sprouting seeds.md' -> 'Sprouting Seeds'
        '01-breakfast.md' -> 'Breakfast'
    """
    # Remove extension
    name = Path(filename).stem

    # Remove leading numbers and dashes (e.g., "01-", "1-")
    name = re.sub(r'^\d+[-_\s]*', '', name)

    # Replace underscores and dashes with spaces
    name = name.replace('_', ' ').replace('-', ' ')

    # Title case
    name = name.title()

    return name


def has_markdown_header(content: str) -> bool:
    """Check if content starts with a markdown header."""
    lines = content.strip().split('\n')
    for line in lines[:5]:  # Check first 5 non-empty lines
        line = line.strip()
        if line and line.startswith('#'):
            return True
        if line and not line.startswith('#'):
            break
    return False


def get_first_header(content: str) -> str | None:
    """Extract the first markdown header from content."""
    match = re.search(r'^(#{1,3})\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(2).strip()
    return None


def process_markdown_file(filepath: str, filename: str) -> str:
    """
    Process a single markdown file.

    Returns content with proper header formatting for RAG section detection.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read().strip()

    if not content:
        return ""

    # Clean up common artifacts
    content = re.sub(r'^\s*---\s*$', '', content, flags=re.MULTILINE)  # YAML frontmatter markers
    content = re.sub(r'<[^>]+>', '', content)  # HTML tags

    # Check if file has markdown headers
    if has_markdown_header(content):
        # File has headers, use them as-is
        # But ensure first header is ## level for consistency
        first_header = get_first_header(content)
        if first_header:
            # Normalize first header to ## for section detection
            content = re.sub(
                r'^(#{1,3})\s+' + re.escape(first_header),
                f'## {first_header}',
                content,
                count=1,
                flags=re.MULTILINE
            )
        return content
    else:
        # No headers - add filename as header
        header = filename_to_header(filename)
        return f"## {header}\n\n{content}"


def extract_md_from_folder(input_folder: str, output_file: str) -> None:
    """
    Extract all markdown files from folder and combine into single text file.

    Args:
        input_folder: Path to folder containing .md files
        output_file: Path to output .txt file
    """
    if not os.path.isdir(input_folder):
        print(f"Error: Folder not found: {input_folder}")
        return

    # Find all markdown files
    md_files = []
    for f in os.listdir(input_folder):
        if f.lower().endswith('.md') and not f.startswith('~$'):
            md_files.append(f)

    if not md_files:
        print(f"No .md files found in {input_folder}")
        return

    # Sort files naturally
    md_files.sort(key=natural_sort_key)

    print(f"Found {len(md_files)} markdown files:")
    for f in md_files:
        print(f"  - {f}")

    # Process each file
    all_content = []
    total_chars = 0

    for filename in md_files:
        filepath = os.path.join(input_folder, filename)
        content = process_markdown_file(filepath, filename)

        if content:
            all_content.append(content)
            total_chars += len(content)
            print(f"  Processed: {filename} ({len(content):,} chars)")

    # Combine with section separators
    combined = "\n\n" + "\n\n".join(all_content)

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined)

    print(f"\nOutput: {output_file}")
    print(f"Total: {total_chars:,} characters from {len(md_files)} files")

    # Count headers for user info
    header_count = len(re.findall(r'^##\s+.+$', combined, re.MULTILINE))
    print(f"Sections detected: {header_count} (## headers)")


def main():
    parser = argparse.ArgumentParser(
        description='Extract markdown files from folder and combine into single text file for RAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python extract_md_from_folder_to_txt.py -i ./06-recipes -o recipes_combined.txt
    python extract_md_from_folder_to_txt.py -i ./06-recipes

After extraction, create RAG:
    python create_rag_from_text.py recipes_combined.txt -o rag_recipes --name "Recipes"
        """
    )
    parser.add_argument(
        '-i', '--input',
        default='.',
        help='Input folder containing .md files (default: current directory)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output .txt file (default: <foldername>_combined.txt)'
    )

    args = parser.parse_args()

    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        folder_name = os.path.basename(os.path.abspath(args.input))
        output_file = f"{folder_name}_combined.txt"

    print(f"{'=' * 60}")
    print(f"  Extracting Markdown Files")
    print(f"{'=' * 60}")
    print(f"Input folder: {args.input}")
    print(f"Output file:  {output_file}")
    print()

    extract_md_from_folder(args.input, output_file)

    print()
    print("Next step - create RAG:")
    print(f"  python create_rag_from_text.py {output_file} -o rag_recipes --name \"Recipes\"")


if __name__ == "__main__":
    main()
