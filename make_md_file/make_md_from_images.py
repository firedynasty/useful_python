#!/usr/bin/env python3
"""
Create a .md file with relative image paths from selected image files.

Usage:
    python3 make_md_from_images.py image1.png image2.jpg ...

The .md file is created in the same directory as the first image.
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: make_md_from_images.py <image1> <image2> ...")
        sys.exit(1)

    files = sys.argv[1:]
    output_dir = os.path.dirname(os.path.abspath(files[0]))
    md_path = os.path.join(output_dir, "images.md")

    lines = []
    for filepath in files:
        filename = os.path.basename(filepath)
        name_no_ext = os.path.splitext(filename)[0]
        lines.append(f"![{name_no_ext}]({filename})\n")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Created {md_path} with {len(files)} image(s)")


if __name__ == "__main__":
    main()
