"""
Saved Text Scraper - Build book context from locally saved text files.

Files can be anything you've copied and saved — website content (reviews, summaries,
Reddit threads, Goodreads listings) OR actual book content (chapters, passages, notes).
Claude will handle each appropriately.

Workflow:
1. Copy/paste content into plain text files using Sublime Text (or any editor)
   - From websites: reviews, summaries, Reddit discussions, etc.
   - From the book itself: chapter excerpts, key passages, your own notes
2. Save them all into one folder (e.g. ./loveBook)
3. Run this script:
   python 08-scrape_saved_text_from_websites.py --folder ./loveBook --title "Deeper Dating"

   The script will:
   a) Read all text files in the folder
   b) Use Claude API to clean/structure each file's content
   c) Compile into a single context file under 150k characters

Usage:
    python 08-scrape_saved_text_from_websites.py --folder ./loveBook --title "Book Title"
    python 08-scrape_saved_text_from_websites.py --folder ./loveBook --title "Book Title" --char-limit 100000
    python 08-scrape_saved_text_from_websites.py --folder ./loveBook --title "Book Title" --no-clipboard

Environment:
    export ANTHROPIC_API_KEY=sk-ant-...   # Required: enables Claude to clean/structure content
"""

import os
import sys
import re
import argparse
from datetime import datetime


DEFAULT_CHAR_LIMIT = 150000
OUTPUT_DIR = "./scraped_from_websites"


# ─── File Loading ────────────────────────────────────────────────────────────

def load_files_from_folder(folder_path):
    """Read all files in folder and return list of result dicts."""
    if not os.path.isdir(folder_path):
        print(f"Error: folder not found: {folder_path}")
        sys.exit(1)

    results = []
    entries = sorted(os.listdir(folder_path))

    print(f"Loading files from: {folder_path}\n")

    for filename in entries:
        filepath = os.path.join(folder_path, filename)
        if not os.path.isfile(filepath):
            continue

        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"  Skipping {filename}: {e}")
            continue

        if len(text) < 50:
            print(f"  Skipping {filename}: too short ({len(text)} chars)")
            continue

        print(f"  {filename} — {len(text):,} chars")
        results.append({
            'title': filename,
            'url': filepath,
            'text': text,
            'char_count': len(text),
        })

    return results


# ─── Claude API Integration ──────────────────────────────────────────────────

def get_anthropic_client():
    """Get Anthropic client. Requires ANTHROPIC_API_KEY to be set."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set.")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY=sk-ant-your-key-here")
        sys.exit(1)

    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        print("Error: anthropic package not installed.")
        print("\nInstall it with:")
        print("  pip install anthropic")
        sys.exit(1)


def clean_with_claude(client, raw_text, book_title, char_budget):
    """
    Use Claude to clean and structure content into useful book context.

    Args:
        client: Anthropic client
        raw_text: Raw text copied from a website
        book_title: The book title for context
        char_budget: Target character count for the output

    Returns:
        Cleaned and structured text
    """
    prompt = f"""You are building a rich context document for the book "{book_title}" from text that was copied and saved to a file. The text may be from a website (review, summary, Reddit thread, Goodreads page, etc.) OR it may be actual content from the book itself (chapter excerpts, passages, notes).

Your task:
1. First determine what kind of content this is:
   - Website content: clean out navigation, ads, cookie banners, UI chrome, purchase links, unrelated boilerplate
   - Book content (chapters/passages): preserve it faithfully — do not summarize or cut substance, just clean up any formatting artifacts from copy/paste
2. Keep everything relevant to understanding the book: key ideas, chapter content, summaries, reviews, author insights, research findings, specific examples, statistics, quotes, and actionable takeaways
3. Preserve the original voice and structure where it adds value
4. Target approximately {char_budget:,} characters

Raw copied text:
{raw_text[:20000]}

Return ONLY the cleaned content. No preamble or explanation."""

    try:
        import anthropic
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"  Claude API error: {e}")
        return raw_text


# ─── Context Compilation ─────────────────────────────────────────────────────

def compile_context(results, book_title, char_limit, claude_client=None):
    """Compile file results into a single context document."""
    if not results:
        print("No content to compile.")
        return ""

    header = f"# Book Context: {book_title}\n"
    header += f"# Sources: {len(results)} file(s)\n"
    header += f"# Compiled: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    toc = "## Sources\n"
    for i, r in enumerate(results, 1):
        toc += f"{i}. {r['title']}\n"
    toc += "\n"

    overhead = len(header) + len(toc) + (len(results) * 150)
    available_chars = char_limit - overhead
    total_chars = sum(r['char_count'] for r in results)

    sections = []

    for i, r in enumerate(results, 1):
        if total_chars > available_chars:
            allocation = int((r['char_count'] / total_chars) * available_chars)
            allocation = max(allocation, 500)
        else:
            allocation = r['char_count']

        text = r['text']

        if claude_client:
            print(f"  Cleaning {r['title']} with Claude ({i}/{len(results)})...")
            text = clean_with_claude(claude_client, text, book_title, allocation)
        else:
            text = text[:allocation]
            if len(r['text']) > allocation:
                last_period = text.rfind('. ')
                if last_period > allocation * 0.7:
                    text = text[:last_period + 1]
                text += "\n\n[... truncated ...]"

        source_header = f"\n{'='*80}\n"
        source_header += f"## Source {i}: {r['title']}\n"
        source_header += f"File: {r['url']}\n"
        source_header += f"{'='*80}\n\n"

        sections.append(source_header + text)

    document = header + toc + "\n".join(sections)

    if len(document) > char_limit:
        document = document[:char_limit]
        document = document[:document.rfind('\n')]
        document += "\n\n[Truncated to character limit]"

    return document


# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_safe_filename(title):
    safe = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    return safe[:50] if len(safe) > 50 else safe


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build book context from locally saved text files."
    )
    parser.add_argument('--folder', type=str, required=True,
                        help='Folder containing saved text files (e.g. ./loveBook)')
    parser.add_argument('--title', type=str, default=None,
                        help='Book title (used for output filename and Claude prompts)')
    parser.add_argument('--char-limit', type=int, default=DEFAULT_CHAR_LIMIT,
                        help=f'Max character count (default: {DEFAULT_CHAR_LIMIT:,})')
    parser.add_argument('--no-claude', action='store_true',
                        help='Skip Claude cleaning, just compile raw text')
    parser.add_argument('--no-clipboard', action='store_true',
                        help='Skip copying to clipboard')

    args = parser.parse_args()

    claude_client = None
    if not args.no_claude:
        claude_client = get_anthropic_client()
        print("Claude API: ready\n")

    results = load_files_from_folder(args.folder)

    if not results:
        print("\nNo files found.")
        return

    total_raw = sum(r['char_count'] for r in results)
    print(f"\n{'─'*60}")
    print(f"Loaded {len(results)} file(s), {total_raw:,} raw characters total.")
    print(f"Character limit: {args.char_limit:,}")
    print(f"{'─'*60}\n")

    book_title = args.title
    if not book_title:
        book_title = input("Enter book title: ").strip()
        if not book_title:
            book_title = "book_context"

    print("Compiling context document...")
    document = compile_context(results, book_title, args.char_limit, claude_client)

    if not document:
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_name = create_safe_filename(book_title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"book_context_{safe_name}_{timestamp}.txt")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(document)

    print(f"\nSaved to: {filepath}")
    print(f"Final size: {len(document):,} characters")
    print(f"Sources included: {len(results)}")

    if not args.no_clipboard:
        try:
            import subprocess
            subprocess.run(['pbcopy'], input=document.encode(), check=True)
            print("Copied to clipboard.")
        except Exception:
            print("Could not copy to clipboard.")


if __name__ == "__main__":
    main()
