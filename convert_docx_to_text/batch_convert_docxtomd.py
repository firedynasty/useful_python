#!/usr/bin/env python3
"""
Batch convert all DOCX files in a directory to Markdown format.
Converts files in-place (creates .md files alongside .docx files).

Uses Pandoc for full-fidelity conversion (preserves hyperlinks, tables, etc.)

Requirements:
    - Pandoc must be installed: brew install pandoc (macOS)
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================================
# DOCX to Markdown Conversion using Pandoc
# ============================================================================

def check_pandoc():
    """Check if Pandoc is installed and available."""
    if shutil.which('pandoc') is None:
        print("Error: Pandoc not found.")
        print("Please install Pandoc:")
        print("  macOS:   brew install pandoc")
        print("  Ubuntu:  sudo apt install pandoc")
        print("  Windows: choco install pandoc")
        return False
    return True


def docx_to_md(docx_file, output_file=None):
    """
    Convert DOCX file to Markdown (.md) format using Pandoc.

    Args:
        docx_file: Path to input DOCX file
        output_file: Path to output MD file (optional, defaults to input name with .md)

    Returns:
        Path to created MD file
    """
    if output_file is None:
        output_file = str(docx_file).rsplit('.', 1)[0] + '.md'

    # Run Pandoc conversion
    result = subprocess.run(
        ['pandoc', str(docx_file), '-o', str(output_file), '--wrap=none'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Pandoc error: {result.stderr}")

    return output_file


# ============================================================================
# Batch Conversion Functions
# ============================================================================

def find_docx_files(directory, skip_temp=True):
    """
    Find all .docx files in directory and subdirectories.

    Args:
        directory: Root directory to search
        skip_temp: Skip temporary Word files (starting with ~$)

    Returns:
        List of Path objects for .docx files
    """
    docx_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.docx'):
                # Skip temporary Word files
                if skip_temp and file.startswith('~$'):
                    continue
                docx_files.append(Path(root) / file)

    return sorted(docx_files)


def convert_batch(directory, force=False, verbose=True):
    """
    Convert all DOCX files in directory to Markdown.

    Args:
        directory: Directory to search for .docx files
        force: Overwrite existing .md files
        verbose: Print detailed progress

    Returns:
        Tuple of (successful_count, skipped_count, error_count)
    """
    # Find all DOCX files
    docx_files = find_docx_files(directory)

    if not docx_files:
        print(f"No .docx files found in '{directory}'")
        return 0, 0, 0

    print(f"Found {len(docx_files)} .docx file(s)")
    print("-" * 60)

    successful = 0
    skipped = 0
    errors = 0

    for docx_path in docx_files:
        # Determine output path (same location, .md extension)
        md_path = docx_path.with_suffix('.md')

        # Check if MD file already exists
        if md_path.exists() and not force:
            if verbose:
                print(f"⏭  Skipping (MD exists): {docx_path.relative_to(directory)}")
            skipped += 1
            continue

        try:
            if verbose:
                print(f"🔄 Converting: {docx_path.relative_to(directory)}")

            docx_to_md(str(docx_path), str(md_path))
            successful += 1

            if verbose:
                print(f"✅ Created: {md_path.relative_to(directory)}")
                print()

        except Exception as e:
            errors += 1
            print(f"❌ Error converting '{docx_path.relative_to(directory)}': {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            print()

    return successful, skipped, errors


def main():
    parser = argparse.ArgumentParser(
        description='Batch convert DOCX files to Markdown (.md) format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all .docx files in current directory
  python batch_convert_docx.py .

  # Convert all .docx files in a specific directory
  python batch_convert_docx.py /path/to/googledrive

  # Force overwrite existing .md files
  python batch_convert_docx.py . --force

  # Quiet mode (only show summary)
  python batch_convert_docx.py . --quiet
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to search for .docx files (default: current directory)'
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

    args = parser.parse_args()

    # Check if Pandoc is installed
    if not check_pandoc():
        return 1

    # Verify directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found")
        return 1

    # Convert to absolute path for cleaner output
    directory = Path(args.directory).resolve()

    print(f"Searching for .docx files in: {directory}")
    print()

    # Run batch conversion
    successful, skipped, errors = convert_batch(
        directory,
        force=args.force,
        verbose=not args.quiet
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
