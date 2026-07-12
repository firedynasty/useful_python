#!/usr/bin/env python3
"""
PDF to Images converter that splits each page into top and bottom halves.
Uses ImageMagick to convert PDF pages and split them horizontally.

Each page is converted to two images:
- page0_a.jpg (top half), page0_b.jpg (bottom half)
- page1_a.jpg (top half), page1_b.jpg (bottom half)
- etc.

Images are saved in a folder named after the PDF file.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


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

    # Fallback: try to convert and count
    return None


def pdf_to_images(pdf_file, output_dir=None, density=300, quality=100):
    """
    Convert PDF file to images, splitting each page into top and bottom halves.

    Args:
        pdf_file: Path to input PDF file
        output_dir: Output directory (defaults to PDF name without extension)
        density: DPI for conversion (default: 300)
        quality: JPEG quality 1-100 (default: 100)

    Returns:
        Path to output directory
    """
    pdf_path = Path(pdf_file)

    # Check if ImageMagick is installed
    if not check_imagemagick():
        print("Error: ImageMagick is not installed or not in PATH")
        print("Install with: brew install imagemagick (macOS)")
        print("           or: sudo apt-get install imagemagick (Ubuntu)")
        return None

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

    print(f"Converting '{pdf_file}' to images in '{output_path}/'")
    print(f"Settings: density={density} dpi, quality={quality}")
    print()

    # Get page count if possible
    page_count = get_pdf_page_count(pdf_file)
    if page_count:
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

    print(f"Processing {page_count} page(s)...")
    print()

    # Process each page
    for page_num in range(page_count):
        print(f"Processing page {page_num + 1}/{page_count}...", end=' ')

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
            print(f"\n❌ Error converting page {page_num}: {result.stderr}")
            continue

        # Get image dimensions
        result = subprocess.run(
            ['identify', '-format', '%w %h', str(temp_page)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"\n❌ Error getting dimensions for page {page_num}")
            if temp_page.exists():
                temp_page.unlink()
            continue

        try:
            width, height = map(int, result.stdout.strip().split())
            half_height = height // 2
        except ValueError:
            print(f"\n❌ Error parsing dimensions for page {page_num}")
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
            print(f"\n❌ Error cropping top half of page {page_num}")
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
            print(f"\n❌ Error cropping bottom half of page {page_num}")
            if temp_page.exists():
                temp_page.unlink()
            continue

        # Clean up temp file
        if temp_page.exists():
            temp_page.unlink()

        print(f"✅ Created {a_file.name} and {b_file.name}")

    print()
    print(f"✅ Successfully converted PDF to {page_count * 2} images in '{output_path}/'")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF to images, splitting each page into top and bottom halves'
    )
    parser.add_argument('input', help='Input PDF file path')
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: PDF filename without extension)'
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

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1

    # Check if it's a PDF
    if not args.input.lower().endswith('.pdf'):
        print(f"Error: Input file must be a PDF (.pdf)")
        return 1

    # Validate quality
    if not 1 <= args.quality <= 100:
        print(f"Error: Quality must be between 1 and 100")
        return 1

    try:
        result = pdf_to_images(
            args.input,
            args.output,
            args.density,
            args.quality
        )
        if result is None:
            return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
