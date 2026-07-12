#!/usr/bin/env python3
"""
Batch convert all TXT files in a directory to Markdown format.
Converts files in-place (creates .md files alongside .txt files).

STANDALONE VERSION - No external dependencies
"""

import argparse
import os
import sys
import re
from pathlib import Path


# ============================================================================
# TXT to Markdown Conversion Functions (embedded)
# ============================================================================

def detect_underline_heading(current_line, next_line):
    """
    Detect if current line is a heading based on next line being underline.

    Returns:
        (is_heading, level) where level is 1 for === and 2 for ---
    """
    if not current_line or not next_line:
        return False, 0

    current = current_line.strip()
    next_stripped = next_line.strip()

    # Check for heading underlines
    if len(current) > 0 and len(next_stripped) > 0:
        # Level 1: ===
        if all(c == '=' for c in next_stripped) and len(next_stripped) >= 3:
            return True, 1
        # Level 2: ---
        if all(c == '-' for c in next_stripped) and len(next_stripped) >= 3:
            return True, 2

    return False, 0


def detect_list_item(line):
    """
    Detect if line is a list item.

    Returns:
        (is_list, formatted_line) - formatted_line has proper markdown bullet/number
    """
    stripped = line.strip()

    # Bulleted list patterns: -, *, •, ○, ▪, ▫
    bullet_pattern = r'^[\-\*\•\○\▪\▫]\s+(.+)$'
    match = re.match(bullet_pattern, stripped)
    if match:
        return True, f"- {match.group(1)}"

    # Numbered list pattern: 1. or 1)
    numbered_pattern = r'^(\d+)[\.\)]\s+(.+)$'
    match = re.match(numbered_pattern, stripped)
    if match:
        return True, f"{match.group(1)}. {match.group(2)}"

    return False, line


def detect_all_caps_heading(line):
    """
    Detect if line is all caps (potential heading).
    Only considers lines with 3+ words.

    Returns:
        (is_heading, level) - level is always 2 for all-caps
    """
    stripped = line.strip()

    # Must have letters
    if not any(c.isalpha() for c in stripped):
        return False, 0

    # Extract alphabetic characters and spaces
    alpha_text = ''.join(c for c in stripped if c.isalpha() or c.isspace())

    # Check if all alphabetic chars are uppercase
    if alpha_text and alpha_text.isupper() and len(alpha_text.split()) >= 3:
        return True, 2

    return False, 0


def txt_to_md(txt_file, output_file=None, encoding='utf-8', smart_format=True):
    """
    Convert TXT file to Markdown (.md) format.

    Args:
        txt_file: Path to input TXT file
        output_file: Path to output MD file (optional, defaults to input name with .md)
        encoding: File encoding (default: utf-8)
        smart_format: Enable smart formatting detection (default: True)

    Returns:
        Path to created MD file
    """
    # Read the text file
    with open(txt_file, 'r', encoding=encoding, errors='replace') as f:
        lines = f.readlines()

    output_lines = []
    i = 0

    while i < len(lines):
        current_line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else None

        # Skip empty lines but preserve them in output
        if not current_line.strip():
            output_lines.append('\n')
            i += 1
            continue

        processed = False

        if smart_format:
            # Check for underlined headings
            is_heading, level = detect_underline_heading(current_line, next_line)
            if is_heading:
                heading_text = current_line.strip()
                output_lines.append(f"{'#' * level} {heading_text}\n\n")
                i += 2  # Skip both the heading and underline
                processed = True

            # Check for all-caps headings
            if not processed:
                is_heading, level = detect_all_caps_heading(current_line)
                if is_heading:
                    heading_text = current_line.strip()
                    output_lines.append(f"{'#' * level} {heading_text}\n\n")
                    i += 1
                    processed = True

            # Check for list items
            if not processed:
                is_list, formatted = detect_list_item(current_line)
                if is_list:
                    output_lines.append(f"{formatted}\n")
                    i += 1
                    processed = True

        # Regular line processing
        if not processed:
            # Preserve the line as-is but ensure proper spacing
            stripped = current_line.strip()
            if stripped:
                output_lines.append(f"{stripped}\n\n")
            i += 1

    # Join all lines
    output_text = "".join(output_lines)

    # Clean up excessive newlines (more than 2 consecutive)
    while "\n\n\n" in output_text:
        output_text = output_text.replace("\n\n\n", "\n\n")

    # Ensure file ends with single newline
    output_text = output_text.rstrip() + '\n'

    # Save to file
    if output_file is None:
        # Replace .txt extension with .md, or add .md if no extension
        base_name = txt_file.rsplit('.', 1)[0] if '.' in txt_file else txt_file
        output_file = base_name + '.md'

    with open(output_file, 'w', encoding=encoding) as f:
        f.write(output_text)

    return output_file


# ============================================================================
# Batch Conversion Functions
# ============================================================================

def find_txt_files(directory):
    """
    Find all .txt files in directory and subdirectories.

    Args:
        directory: Root directory to search

    Returns:
        List of Path objects for .txt files
    """
    txt_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.txt'):
                txt_files.append(Path(root) / file)

    return sorted(txt_files)


def convert_batch(directory, force=False, verbose=True, smart_format=True):
    """
    Convert all TXT files in directory to Markdown.

    Args:
        directory: Directory to search for .txt files
        force: Overwrite existing .md files
        verbose: Print detailed progress
        smart_format: Enable smart formatting detection

    Returns:
        Tuple of (successful_count, skipped_count, error_count)
    """
    # Find all TXT files
    txt_files = find_txt_files(directory)

    if not txt_files:
        print(f"No .txt files found in '{directory}'")
        return 0, 0, 0

    print(f"Found {len(txt_files)} .txt file(s)")
    print("-" * 60)

    successful = 0
    skipped = 0
    errors = 0

    for txt_path in txt_files:
        # Determine output path (same location, .md extension)
        md_path = txt_path.with_suffix('.md')

        # Check if MD file already exists
        if md_path.exists() and not force:
            if verbose:
                print(f"⏭  Skipping (MD exists): {txt_path.relative_to(directory)}")
            skipped += 1
            continue

        try:
            if verbose:
                print(f"🔄 Converting: {txt_path.relative_to(directory)}")

            txt_to_md(str(txt_path), str(md_path), smart_format=smart_format)
            successful += 1

            if verbose:
                print(f"✅ Created: {md_path.relative_to(directory)}")
                print()

        except Exception as e:
            errors += 1
            print(f"❌ Error converting '{txt_path.relative_to(directory)}': {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            print()

    return successful, skipped, errors


def main():
    parser = argparse.ArgumentParser(
        description='Batch convert TXT files to Markdown (.md) format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all .txt files in current directory
  python batch_convert_txttomd.py .

  # Convert all .txt files in a specific directory
  python batch_convert_txttomd.py /path/to/documents

  # Force overwrite existing .md files
  python batch_convert_txttomd.py . --force

  # Quiet mode (only show summary)
  python batch_convert_txttomd.py . --quiet

  # Disable smart formatting
  python batch_convert_txttomd.py . --no-smart-format
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to search for .txt files (default: current directory)'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Overwrite existing .md files'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - only show summary'
    )
    parser.add_argument(
        '--no-smart-format',
        action='store_true',
        help='Disable smart formatting (preserve text as-is)'
    )

    args = parser.parse_args()

    # Verify directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found")
        return 1

    # Convert to absolute path for cleaner output
    directory = Path(args.directory).resolve()

    print(f"Searching for .txt files in: {directory}")
    print()

    # Run batch conversion
    successful, skipped, errors = convert_batch(
        directory,
        force=args.force,
        verbose=not args.quiet,
        smart_format=not args.no_smart_format
    )

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully converted: {successful}")
    print(f"⏭  Skipped (already exists): {skipped}")
    print(f"❌ Errors: {errors}")
    print(f"📊 Total files processed: {successful + skipped + errors}")

    if skipped > 0 and not args.force:
        print("\nTip: Use --force to overwrite existing .md files")

    return 1 if errors > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
