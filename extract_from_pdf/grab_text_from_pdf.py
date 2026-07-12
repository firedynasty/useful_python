#!/usr/bin/env python3
"""Extract text from a PDF page using Claude Vision and copy to clipboard."""

import argparse
import base64
import io
import subprocess

import anthropic
from pdf2image import convert_from_path

MODEL = "claude-sonnet-4-0"


def main():
    parser = argparse.ArgumentParser(description="Grab text from a PDF page to clipboard")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("-p", "--page", type=int, required=True, help="Page number (1-indexed)")
    parser.add_argument("--dpi", type=int, default=200, help="DPI for rendering (default: 200)")
    args = parser.parse_args()

    pages = convert_from_path(args.pdf, dpi=args.dpi, first_page=args.page, last_page=args.page)

    buf = io.BytesIO()
    pages[0].save(buf, format="JPEG", quality=85)
    image_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": "Extract all text from this page exactly as it appears. Preserve the layout and formatting as much as possible. Output only the extracted text, nothing else."},
                ],
            }
        ],
    )

    text = message.content[0].text.strip()
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
    print(f"Page {args.page} copied to clipboard ({len(text)} chars)")


if __name__ == "__main__":
    main()
