#!/usr/bin/env python3
"""
Create a chapter marker image to insert between Kindle screenshots.

Usage:
    python make_chapter_marker.py "Chapter Title" -o ./sports_injury/sports_injury15b.png

The marker image will be detected by extract_kindle_screenshots_txt.py
and used to split chapters.
"""

import argparse
from PIL import Image, ImageDraw, ImageFont


def create_marker(title: str, output_path: str):
    """Create a simple chapter marker image."""
    # Create white image
    width, height = 800, 200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw marker text
    marker_text = f"=== CHAPTER: {title} ==="

    # Try to use a readable font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), marker_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), marker_text, fill='black', font=font)

    # Save
    img.save(output_path)
    print(f"Created: {output_path}")
    print(f"Marker: {marker_text}")


def main():
    parser = argparse.ArgumentParser(
        description='Create chapter marker image'
    )
    parser.add_argument('title', help='Chapter title')
    parser.add_argument('-o', '--output', required=True,
                        help='Output image path (e.g., ./folder/img15b.png)')

    args = parser.parse_args()
    create_marker(args.title, args.output)


if __name__ == "__main__":
    main()
