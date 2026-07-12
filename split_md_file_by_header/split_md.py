#!/usr/bin/env python3
"""
Split a markdown file into separate .md files based on ## headings.

Usage:
    python split_md.py input.md [output_directory]
"""

import os
import re
import sys


def slugify(heading):
    """Convert a heading to a safe filename."""
    name = heading.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s_]+', '_', name)
    name = name.strip('_')
    return name or 'untitled'


def split_md(input_file, output_dir):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on lines starting with ## (but not ### or deeper)
    parts = re.split(r'(?m)^(?=## (?!#))', content)

    os.makedirs(output_dir, exist_ok=True)

    # Track filenames to avoid collisions
    used_names = {}
    written = 0

    for part in parts:
        part = part.strip()
        if not part:
            continue

        lines = part.split('\n', 1)
        first_line = lines[0].strip()

        if first_line.startswith('## '):
            heading = first_line.lstrip('#').strip()
            basename = slugify(heading)
        else:
            # Content before the first ## heading — skip or save as preamble
            basename = 'preamble'
            heading = None

        # Handle duplicate names
        if basename in used_names:
            used_names[basename] += 1
            basename = f"{basename}_{used_names[basename]}"
        else:
            used_names[basename] = 1

        filename = f"{basename}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(part + '\n')

        label = heading or '(preamble)'
        print(f"  {filename:40s} <- {label}")
        written += 1

    print(f"\n{written} file(s) written to {os.path.abspath(output_dir)}/")


def main():
    if len(sys.argv) < 2:
        print("Usage: python split_md.py <input.md> [output_directory]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'split_output'

    if not os.path.isfile(input_file):
        print(f"Error: '{input_file}' not found")
        sys.exit(1)

    print(f"Splitting: {input_file}")
    print(f"Output:    {output_dir}\n")
    split_md(input_file, output_dir)


if __name__ == "__main__":
    main()
