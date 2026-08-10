"""
Extract a chapter from an EPUB and open it directly in pasteToOutline.html,
bypassing the paste step entirely.

Usage:
    python epub_to_outline.py brothers.epub 4
    python epub_to_outline.py brothers.epub 4 --mode theology
    python epub_to_outline.py brothers.epub --list
"""

import argparse
import sys
import tempfile
import webbrowser
from pathlib import Path

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup


OUTLINE_HTML = Path('/Users/stanleytan/Documents/technical/github/vercel_flashcards/pasteToOutline.html')


def get_chapters(book):
    chapters = []
    for idx, (item_id, _linear) in enumerate(book.spine, start=1):
        item = book.get_item_with_id(item_id)
        if item is not None and item.get_type() == ITEM_DOCUMENT:
            chapters.append((idx, item))
    return chapters


def extract_title(item):
    soup = BeautifulSoup(item.get_content(), "html.parser")
    for tag in ["h1", "h2", "h3", "h4"]:
        heading = soup.find(tag)
        if heading:
            text = heading.get_text(" ", strip=True)
            if text:
                return text
    title_tag = soup.find("title")
    if title_tag:
        text = title_tag.get_text(strip=True)
        if text:
            return text
    return "(no title)"


def html_to_text(html_bytes):
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n\n".join(lines)


def js_escape(text):
    """Escape text for safe embedding in a JS template literal."""
    return (text
        .replace('\\', '\\\\')
        .replace('`', '\\`')
        .replace('$', '\\$')
        .replace('\r', '')
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract an EPUB chapter and open it in the outline tool."
    )
    parser.add_argument("epub_path", help="Path to the .epub file")
    parser.add_argument("chapter_number", type=int, nargs="?",
                        help="Chapter number in spine order (1-based)")
    parser.add_argument("--list", action="store_true",
                        help="List all chapters instead of opening one")
    parser.add_argument("--mode", default="news",
                        choices=["theology", "general", "economy",
                                 "seeking-alpha", "reddit", "news"],
                        help="Outline mode (default: news)")
    args = parser.parse_args()

    if not OUTLINE_HTML.exists():
        print(f"Error: outline HTML not found at {OUTLINE_HTML}", file=sys.stderr)
        sys.exit(1)

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
    chapter_title = extract_title(match)

    # Inject a boot script at the end of the page's own <script> block.
    # By the time this runs, processInput and all event listeners are already set up
    # (both scripts are at the bottom of <body>, parsed synchronously).
    boot = f"""
<script>
(function () {{
  document.getElementById('paste-text').value = `{js_escape(text)}`;
  document.getElementById('title-in').value = `{js_escape(chapter_title)}`;
  document.getElementById('cleanup').checked = true;
  var radio = document.querySelector('input[name=mode][value="{args.mode}"]');
  if (radio) radio.checked = true;
  processInput();
  showTags = false;
  applyTags();
}})();
</script>
"""

    html_source = OUTLINE_HTML.read_text(encoding='utf-8')
    # Replace only the final </body> to avoid hitting the one inside
    # the btn-orig JS template literal string
    last_body = html_source.rfind('</body>')
    html_out = html_source[:last_body] + boot + '\n</body>' + html_source[last_body + len('</body>'):]

    tmp = tempfile.NamedTemporaryFile(
        mode='w', encoding='utf-8',
        suffix='.html', delete=False,
        prefix=f'epub_ch{args.chapter_number}_',
    )
    tmp.write(html_out)
    tmp.close()

    print(f"Opening chapter {args.chapter_number}: {chapter_title}")
    webbrowser.open(f'file://{tmp.name}')


if __name__ == "__main__":
    main()
