#!/usr/bin/env python3
"""
RTF to Markdown converter:
- Uses macOS textutil to convert RTF to plain text
- Wraps entire content in ```bash code blocks for syntax highlighting
"""

import argparse
import os
import subprocess
import sys


def rtf_to_md(rtf_file, output_file=None, encoding='utf-8'):
    """
    Convert RTF file to Markdown (.md) format with bash code block wrapping.

    Args:
        rtf_file: Path to input RTF file
        output_file: Path to output MD file (optional, defaults to input name with .md)
        encoding: Output file encoding (default: utf-8)

    Returns:
        Path to created MD file
    """
    # Check if textutil is available (macOS only)
    try:
        subprocess.run(['which', 'textutil'], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: textutil not found. This script requires macOS textutil.", file=sys.stderr)
        return None

    # Convert RTF to plain text using textutil
    try:
        result = subprocess.run(
            ['textutil', '-convert', 'txt', '-stdout', rtf_file],
            capture_output=True,
            text=True,
            check=True
        )
        plain_text = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error converting RTF file: {e.stderr}", file=sys.stderr)
        return None

    # Wrap content in bash code block for syntax highlighting
    output_text = f"```bash\n{plain_text.rstrip()}\n```\n"

    # Save to file
    if output_file is None:
        # Replace .rtf extension with .md, or add .md if no extension
        base_name = rtf_file.rsplit('.', 1)[0] if '.' in rtf_file else rtf_file
        output_file = base_name + '.md'

    with open(output_file, 'w', encoding=encoding) as f:
        f.write(output_text)

    print(f"Successfully converted '{rtf_file}' to '{output_file}'")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Convert RTF file to Markdown (.md) format with bash code block'
    )
    parser.add_argument('input', help='Input RTF file path')
    parser.add_argument('-o', '--output', help='Output MD file path (default: input_name.md)')
    parser.add_argument('-e', '--encoding', default='utf-8', help='Output file encoding (default: utf-8)')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1

    try:
        result = rtf_to_md(args.input, args.output, args.encoding)
        if result is None:
            return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
