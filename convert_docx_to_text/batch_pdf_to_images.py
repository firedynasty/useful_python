#!/usr/bin/env python3
"""
Batch convert all PDF files in a directory to images.
Splits each page into top and bottom halves.
Creates folders named after each PDF file containing the images.

STANDALONE VERSION - Embeds pdf_to_images functionality
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


# ============================================================================
# PDF to Images Conversion Functions (embedded)
# ============================================================================

def check_imagemagick():
    """Check if ImageMagick is installed."""
    try:
        result = subprocess.run(
            ['convert', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_pdf_page_count(pdf_file):
    """Get the number of pages in a PDF file using pdfinfo."""
    try:
        result = subprocess.run(
            ['pdfinfo', pdf_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Pages:'):
                    return int(line.split(':')[1].strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass

    return None


def pdf_to_images(pdf_file, output_dir=None, density=300, quality=100, verbose=True):
    """
    Convert PDF file to images, splitting each page into top and bottom halves.

    Args:
        pdf_file: Path to input PDF file
        output_dir: Output directory (defaults to PDF name without extension)
        density: DPI for conversion (default: 300)
        quality: JPEG quality 1-100 (default: 100)
        verbose: Print detailed progress

    Returns:
        Tuple of (success: bool, image_count: int, output_path: str)
    """
    pdf_path = Path(pdf_file)

    # Determine output directory with sequential numbering if exists
    if output_dir is None:
        base_dir = pdf_path.stem  # PDF name without extension
    else:
        base_dir = str(output_dir)

    output_dir = base_dir
    counter = 1

    # Find next available folder name
    while Path(output_dir).exists():
        output_dir = f"{base_dir}_{counter}"
        counter += 1

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Converting '{pdf_file}' to images in '{output_path}/'")
        print(f"Settings: density={density} dpi, quality={quality}")

    # Get page count if possible
    page_count = get_pdf_page_count(pdf_file)
    if page_count and verbose:
        print(f"PDF has {page_count} page(s)")

    # Create temporary file path for full page images
    temp_page = output_path / "temp_page.jpg"

    # Try to determine page count by attempting conversion
    if page_count is None:
        page_count = 0
        while True:
            result = subprocess.run(
                [
                    'convert',
                    '-density', str(density),
                    f'{pdf_file}[{page_count}]',
                    '-quality', str(quality),
                    str(temp_page)
                ],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                break
            page_count += 1
            if temp_page.exists():
                temp_page.unlink()

    if verbose:
        print(f"Processing {page_count} page(s)...")

    # Process each page
    success_count = 0
    for page_num in range(page_count):
        if verbose:
            print(f"  Page {page_num + 1}/{page_count}...", end=' ')

        # Convert page to temporary full image
        result = subprocess.run(
            [
                'convert',
                '-density', str(density),
                f'{pdf_file}[{page_num}]',
                '-quality', str(quality),
                str(temp_page)
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            if verbose:
                print(f"❌ Error converting")
            continue

        # Get image dimensions
        result = subprocess.run(
            ['identify', '-format', '%w %h', str(temp_page)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            if verbose:
                print(f"❌ Error getting dimensions")
            if temp_page.exists():
                temp_page.unlink()
            continue

        try:
            width, height = map(int, result.stdout.strip().split())
            half_height = height // 2
        except ValueError:
            if verbose:
                print(f"❌ Error parsing dimensions")
            if temp_page.exists():
                temp_page.unlink()
            continue

        # Crop top half (a)
        a_file = output_path / f"page{page_num}_a.jpg"
        result = subprocess.run(
            [
                'convert',
                str(temp_page),
                '-crop', f'{width}x{half_height}+0+0',
                '+repage',
                str(a_file)
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            if verbose:
                print(f"❌ Error cropping top half")
            if temp_page.exists():
                temp_page.unlink()
            continue

        # Crop bottom half (b)
        b_file = output_path / f"page{page_num}_b.jpg"
        result = subprocess.run(
            [
                'convert',
                str(temp_page),
                '-crop', f'{width}x{half_height}+0+{half_height}',
                '+repage',
                str(b_file)
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            if verbose:
                print(f"❌ Error cropping bottom half")
            if temp_page.exists():
                temp_page.unlink()
            continue

        # Clean up temp file
        if temp_page.exists():
            temp_page.unlink()

        if verbose:
            print(f"✅")
        success_count += 1

    total_images = success_count * 2
    if verbose:
        print(f"Created {total_images} images")

    return success_count > 0, total_images, str(output_path)


# ============================================================================
# Batch Conversion Functions
# ============================================================================

def find_pdf_files(directory):
    """
    Find all .pdf files in directory and subdirectories.

    Args:
        directory: Root directory to search

    Returns:
        List of Path objects for .pdf files
    """
    pdf_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                # Skip hidden files
                if file.startswith('.'):
                    continue
                pdf_files.append(Path(root) / file)

    return sorted(pdf_files)


def convert_batch(directory, density=300, quality=100, force=False, verbose=True):
    """
    Convert all PDF files in directory to images.

    Args:
        directory: Directory to search for .pdf files
        density: DPI for conversion (default: 300)
        quality: JPEG quality 1-100 (default: 100)
        force: Overwrite existing image folders
        verbose: Print detailed progress

    Returns:
        Tuple of (successful_count, skipped_count, error_count)
    """
    # Check ImageMagick first
    if not check_imagemagick():
        print("Error: ImageMagick is not installed or not in PATH")
        print("Install with: brew install imagemagick (macOS)")
        print("           or: sudo apt-get install imagemagick (Ubuntu)")
        return 0, 0, 0

    # Find all PDF files
    pdf_files = find_pdf_files(directory)

    if not pdf_files:
        print(f"No .pdf files found in '{directory}'")
        return 0, 0, 0

    print(f"Found {len(pdf_files)} PDF file(s)")
    print("-" * 60)

    successful = 0
    skipped = 0
    errors = 0

    for pdf_path in pdf_files:
        try:
            if verbose:
                print(f"🔄 Converting: {pdf_path.relative_to(directory)}")

            # Determine base output directory (same location as PDF, named after PDF)
            base_output_dir = pdf_path.parent / pdf_path.stem

            success, image_count, output = pdf_to_images(
                str(pdf_path),
                str(base_output_dir),  # Pass base directory, function will add sequential numbering
                density,
                quality,
                verbose=verbose
            )

            if success:
                successful += 1
                if verbose:
                    print(f"✅ Created: {output_dir.relative_to(directory)}/ ({image_count} images)")
                    print()
            else:
                errors += 1
                print(f"❌ Failed to convert '{pdf_path.relative_to(directory)}'")
                print()

        except Exception as e:
            errors += 1
            print(f"❌ Error converting '{pdf_path.relative_to(directory)}': {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            print()

    return successful, skipped, errors


def main():
    parser = argparse.ArgumentParser(
        description='Batch convert PDF files to images (split into top/bottom halves)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all .pdf files in current directory
  python batch_pdf_to_images.py .

  # Convert all .pdf files in a specific directory
  python batch_pdf_to_images.py /path/to/documents

  # Force overwrite existing image folders
  python batch_pdf_to_images.py . --force

  # Use higher DPI for better quality
  python batch_pdf_to_images.py . --density 600

  # Quiet mode (only show summary)
  python batch_pdf_to_images.py . --quiet
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to search for .pdf files (default: current directory)'
    )
    parser.add_argument(
        '-d', '--density',
        type=int,
        default=300,
        help='DPI for conversion (default: 300)'
    )
    parser.add_argument(
        '-q', '--quality',
        type=int,
        default=100,
        help='JPEG quality 1-100 (default: 100)'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Overwrite existing image folders'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Quiet mode - only show summary'
    )

    args = parser.parse_args()

    # Verify directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found")
        return 1

    # Validate quality
    if not 1 <= args.quality <= 100:
        print(f"Error: Quality must be between 1 and 100")
        return 1

    # Convert to absolute path for cleaner output
    directory = Path(args.directory).resolve()

    print(f"Searching for .pdf files in: {directory}")
    print()

    # Run batch conversion
    successful, skipped, errors = convert_batch(
        directory,
        density=args.density,
        quality=args.quality,
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
        print("\nTip: Use --force to overwrite existing image folders")

    return 1 if errors > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
