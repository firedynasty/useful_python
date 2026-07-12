#!/usr/bin/env python3
"""Convert scanned PDF pages to French/English flashcard text files using Claude Vision API."""

import argparse
import base64
import io
import os
import time

import anthropic
from pdf2image import convert_from_path

MODEL = "claude-sonnet-4-0"
DELAY_BETWEEN_CALLS = 1.0  # seconds

PROMPT = """Look at this textbook page. Extract all French vocabulary and phrases with their English translations.

Output ONLY flashcard pairs in this exact format — one French line, one English line, then a blank line between each pair:

bonjour
hello

merci
thank you

Rules:
- French on the first line, English on the second line
- One blank line between each pair
- No numbering, no extra text, no headers
- Include all vocabulary, phrases, and example sentences you can find on the page
- If a page has no French/English content (e.g. table of contents, blank page, copyright), output nothing"""


def page_to_base64_jpeg(page_image):
    buf = io.BytesIO()
    page_image.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def extract_flashcards(client, image_b64):
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
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )
    return message.content[0].text.strip()


def main():
    parser = argparse.ArgumentParser(description="Convert PDF pages to flashcard text files")
    parser.add_argument("-i", "--input", required=True, help="Path to PDF file")
    parser.add_argument("-o", "--output", required=True, help="Output directory for .txt files")
    parser.add_argument("--start", type=int, default=1, help="Start page (1-indexed, default: 1)")
    parser.add_argument("--end", type=int, default=None, help="End page (1-indexed, default: last page)")
    parser.add_argument("--dpi", type=int, default=200, help="DPI for page rendering (default: 200)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    client = anthropic.Anthropic()

    # Get total page count first (convert one page to check)
    print(f"Loading PDF: {args.input}")
    first_page = convert_from_path(args.input, dpi=args.dpi, first_page=1, last_page=1)
    # Get total pages by converting the info
    from pdf2image.pdf2image import pdfinfo_from_path
    info = pdfinfo_from_path(args.input)
    total_pages = info["Pages"]
    print(f"Total pages: {total_pages}")

    start = args.start
    end = args.end if args.end else total_pages
    end = min(end, total_pages)

    print(f"Processing pages {start}-{end}")

    for page_num in range(start, end + 1):
        out_file = os.path.join(args.output, f"page_{page_num:03d}.txt")

        if os.path.exists(out_file):
            print(f"  Page {page_num}/{end}: skipping (already exists)")
            continue

        print(f"  Page {page_num}/{end}: converting...", end=" ", flush=True)
        pages = convert_from_path(args.input, dpi=args.dpi, first_page=page_num, last_page=page_num)
        image_b64 = page_to_base64_jpeg(pages[0])

        print("sending to Claude...", end=" ", flush=True)
        try:
            flashcards = extract_flashcards(client, image_b64)
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        if flashcards:
            with open(out_file, "w") as f:
                f.write(flashcards + "\n")
            # Count pairs (separated by blank lines)
            pairs = len([s for s in flashcards.split("\n\n") if s.strip()])
            print(f"done ({pairs} cards)")
        else:
            # Write empty file so we skip on resume
            with open(out_file, "w") as f:
                pass
            print("done (no content)")

        time.sleep(DELAY_BETWEEN_CALLS)

    print("Complete!")


if __name__ == "__main__":
    main()
