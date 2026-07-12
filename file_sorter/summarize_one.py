#!/usr/bin/env python3
"""
Summarize a single file using OpenAI API.

Usage:
    python summarize_one.py myfile.md
    python summarize_one.py myfile.pdf --chars 1000
"""

import argparse
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: pip install openai", file=sys.stderr)
    sys.exit(1)

from summarize_file import read_file_content


def main():
    parser = argparse.ArgumentParser(description='Summarize a single file')
    parser.add_argument('file', type=Path, help='File to summarize')
    parser.add_argument('--chars', type=int, default=500,
                        help='Characters to sample (default: 500)')
    parser.add_argument('--model', type=str, default='gpt-4o',
                        help='OpenAI model (default: gpt-4o)')

    args = parser.parse_args()

    if not args.file.exists():
        print(f"File not found: {args.file}")
        sys.exit(1)

    content = read_file_content(args.file, args.chars)

    client = OpenAI()
    resp = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": (
                "You analyze files and provide a concise summary. "
                "Return exactly this format:\n"
                "Keywords: keyword1, keyword2, keyword3\n"
                "Summary: 1-2 sentence explanation."
            )},
            {"role": "user", "content": (
                f"Filename: {args.file.name}\n\n"
                f"Content:\n{content}"
            )},
        ],
        temperature=0.2,
    )

    text = (resp.choices[0].message.content or "").strip()
    print(f"File: {args.file.name}")
    print(text)


if __name__ == "__main__":
    main()
