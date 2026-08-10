"""
Extract a chapter from an EPUB3 file and copy its text to the clipboard.

Install dependencies first:
    pip install ebooklib beautifulsoup4 pyperclip

Usage:
    python epub_chapter_extractor.py mybook.epub 3
    python epub_chapter_extractor.py mybook.epub 3 --list   # just list chapters, don't copy
"""

import argparse
import sys

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup


def get_chapters(book):
    """
    Return the document items in spine order (i.e. reading order).
    Each entry is (index, item) where item.get_name() gives the filename
    and item.get_content() gives the raw XHTML bytes.
    """
    chapters = []
    for idx, (item_id, _linear) in enumerate(book.spine, start=1):
        item = book.get_item_with_id(item_id)
        if item is not None and item.get_type() == ITEM_DOCUMENT:
            chapters.append((idx, item))
    return chapters


def extract_title(item):
    """Extract a human-readable title from an XHTML spine item."""
    soup = BeautifulSoup(item.get_content(), "html.parser")
    # Try headings in priority order
    for tag in ["h1", "h2", "h3", "h4"]:
        heading = soup.find(tag)
        if heading:
            text = heading.get_text(" ", strip=True)
            if text:
                return text
    # Fall back to <title> element
    title_tag = soup.find("title")
    if title_tag:
        text = title_tag.get_text(strip=True)
        if text:
            return text
    return "(no title)"


def html_to_text(html_bytes):
    soup = BeautifulSoup(html_bytes, "html.parser")
    # Strip script/style, keep paragraph breaks readable
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract a chapter from an EPUB3 file.")
    parser.add_argument("epub_path", help="Path to the .epub file")
    parser.add_argument("chapter_number", type=int, nargs="?",
                         help="Chapter number in spine order (1-based)")
    parser.add_argument("--list", action="store_true",
                         help="List all chapters/spine items instead of extracting one")
    parser.add_argument("--no-clipboard", action="store_true",
                         help="Print to stdout instead of copying to clipboard")
    args = parser.parse_args()

    book = epub.read_epub(args.epub_path)
    chapters = get_chapters(book)

    if args.list or args.chapter_number is None:
        print(f"{len(chapters)} chapters found:\n")
        for idx, item in chapters:
            title = extract_title(item)
            print(f"  {idx:>3}. {title}")
        return

    match = next((item for idx, item in chapters if idx == args.chapter_number), None)
    if match is None:
        print(f"Chapter {args.chapter_number} not found. Use --list to see available chapters.",
              file=sys.stderr)
        sys.exit(1)

    text = html_to_text(match.get_content())

    if args.no_clipboard:
        print(text)
    else:
        try:
            import pyperclip
            pyperclip.copy(text)
            print(f"Copied chapter {args.chapter_number} ({match.get_name()}) "
                  f"to clipboard ({len(text)} characters).")
        except ImportError:
            print("pyperclip not installed — printing instead:\n")
            print(text)


if __name__ == "__main__":
    main()
