"""
Book Context Scraper - Scrape all open Chrome tabs to build book context.

Workflow:
1. Start Chrome with remote debugging:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile

2. Open tabs with content about the book (reviews, summaries, articles, etc.)
   Also open the Book Notes Collector on CodePen to paste manual notes.

3. Run this script:
   python 06-book_context_scraper.py --title "The Best Place to Work"

   The script will:
   a) Scrape all open tabs
   b) Detect the CodePen Book Notes page and extract pasted notes
   c) (Optional) Use Claude API to clean/structure the content
   d) Compile into a single context file under 150k characters

Usage:
    python 06-book_context_scraper.py --title "Book Title"           # Scrape all open tabs
    python 06-book_context_scraper.py --suggest "Book Title Author"  # Print suggested search queries
    python 06-book_context_scraper.py --urls urls.txt                # Scrape URLs from a file
    python 06-book_context_scraper.py --char-limit 100000            # Set character limit (default: 150000)

Environment:
    export ANTHROPIC_API_KEY=sk-ant-...   # Optional: enables Claude to clean/structure scraped content
"""

import os
import sys
import time
import socket
import re
import argparse
from datetime import datetime
from urllib.parse import quote_plus, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


# ─── Configuration ───────────────────────────────────────────────────────────

DEFAULT_CHAR_LIMIT = 150000
OUTPUT_DIR = "./scraped_from_websites"



# ─── Chrome Connection ──────────────────────────────────────────────────────

def check_chrome_running():
    """Check if Chrome is running with remote debugging on port 9222."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', 9222))
        s.close()
        return True
    except Exception:
        s.close()
        return False


def connect_to_chrome():
    """Connect to an already running Chrome instance with remote debugging."""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        print("Setting up ChromeDriver...")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
        )
        print("Connected to Chrome.\n")
        return driver
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")
        print("\nStart Chrome with:")
        print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome "
              "--remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile")
        return None


# ─── Content Extraction (JS-based, runs in browser) ─────────────────────────

EXTRACT_JS = """
var t = (document.querySelector('h1') || {}).textContent || '';
t = t.trim();
var ps = document.querySelectorAll('article p, .article-body p, .article-content p, .post-content p, .entry-content p, .main-content p, .story-body p, p[data-type="paragraph"]');
if (!ps.length) {
    // Fallback: grab all body paragraphs
    ps = document.querySelectorAll('body p');
}
var o = '';
ps.forEach(function(p) {
    var x = (p.textContent || '').trim();
    if (x && x.length > 20) o += x + '\\n\\n';
});
return {title: t, text: o.trim()};
"""


def extract_page_text(browser):
    """Extract article text by running JS directly in the browser (bookmarklet approach)."""
    try:
        result = browser.execute_script(EXTRACT_JS)
        return result.get('title', ''), result.get('text', '')
    except Exception as e:
        print(f"  JS extraction error: {e}")
        return '', ''


# ─── Book Notes Page Detection ──────────────────────────────────────────────

def is_book_notes_page(url, html):
    """Check if the page is our book_notes.html collector (local or CodePen)."""
    if 'cdpn.io' in url or 'codepen.io' in url:
        return 'book-notes-content' in html
    return 'id="book-notes-content"' in html


def extract_book_notes(html):
    """Extract all appended notes from the book_notes.html page."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id='book-notes-content')
    if not container:
        return []

    notes = []
    for card in container.find_all('div', class_='note-card'):
        source_el = card.find(class_='note-source')
        body_el = card.find(class_='note-body')
        if body_el:
            source = source_el.get_text(strip=True) if source_el else "Manual Note"
            text = body_el.get_text(strip=True)
            if text:
                notes.append({
                    'title': f"Manual: {source}",
                    'url': 'book_notes.html (local)',
                    'text': text,
                    'char_count': len(text),
                })
    return notes


# ─── Scraping ────────────────────────────────────────────────────────────────

def scrape_url(browser, url, index, total):
    """Navigate to a URL, scrape it, and return structured content."""
    try:
        browser.get(url)
        time.sleep(2)

        title = browser.title or "Untitled"
        print(f"  [{index}/{total}] {title[:60]}")
        print(f"           {url[:80]}")

        js_title, text = extract_page_text(browser)
        if js_title:
            title = js_title

        if len(text) < 100:
            print(f"           Skipping: too little content ({len(text)} chars).")
            return None

        print(f"           OK: {len(text):,} characters")

        return {
            'title': title,
            'url': url,
            'text': text,
            'char_count': len(text),
        }

    except Exception as e:
        print(f"  [{index}/{total}] Error: {e}")
        return None


def scrape_tab_content(browser, tab_handle, index, total):
    """Scrape content from an already-open tab using JS extraction."""
    try:
        browser.switch_to.window(tab_handle)
        time.sleep(1)

        url = browser.current_url
        title = browser.title or "Untitled"

        print(f"  [{index}/{total}] {title[:60]}")
        print(f"           {url[:80]}")

        js_title, text = extract_page_text(browser)
        if js_title:
            title = js_title

        if len(text) < 100:
            print(f"           Skipping: too little content ({len(text)} chars).")
            return None

        print(f"           OK: {len(text):,} characters")

        return {
            'title': title,
            'url': url,
            'text': text,
            'char_count': len(text),
        }

    except Exception as e:
        print(f"  [{index}/{total}] Error: {e}")
        return None


# ─── Claude API Integration ─────────────────────────────────────────────────

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
    Use Claude to clean and structure scraped content into useful book context.

    Args:
        client: Anthropic client
        raw_text: The raw scraped text from one source
        book_title: The book title for context
        char_budget: Target character count for the output

    Returns:
        Cleaned and structured text
    """
    prompt = f"""You are extracting useful book context from a scraped web page about the book "{book_title}".

Your task:
1. Extract ONLY information relevant to the book: summaries, key ideas, chapter content, reviews, author insights, research findings, actionable takeaways
2. Remove: navigation text, ads, cookie notices, unrelated content, repetitive boilerplate, purchase links
3. Keep the content factual and information-dense
4. Preserve specific examples, statistics, and quotes from the book
5. Target approximately {char_budget:,} characters

Raw scraped content:
{raw_text[:20000]}

Return ONLY the cleaned, relevant content. No preamble or explanation."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"  Claude API error: {e}")
        return raw_text  # Fall back to raw text


# ─── Context Compilation ────────────────────────────────────────────────────

def compile_context(results, book_title, char_limit, claude_client=None):
    """
    Compile scraped results into a single context document.
    Optionally uses Claude to clean each source.
    """
    if not results:
        print("No content was scraped.")
        return ""

    # Build header
    header = f"# Book Context: {book_title}\n"
    header += f"# Sources: {len(results)} web pages\n"
    header += f"# Compiled: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    # Table of contents
    toc = "## Sources\n"
    for i, r in enumerate(results, 1):
        toc += f"{i}. {r['title'][:80]}\n"
    toc += "\n"

    overhead = len(header) + len(toc) + (len(results) * 150)
    available_chars = char_limit - overhead

    total_chars = sum(r['char_count'] for r in results)

    sections = []

    for i, r in enumerate(results, 1):
        # Proportional allocation
        if total_chars > available_chars:
            allocation = int((r['char_count'] / total_chars) * available_chars)
            allocation = max(allocation, 500)
        else:
            allocation = r['char_count']

        text = r['text']

        # Use Claude to clean if available
        if claude_client:
            print(f"  Cleaning source {i}/{len(results)} with Claude...")
            text = clean_with_claude(claude_client, text, book_title, allocation)
        else:
            # Manual truncation
            text = text[:allocation]
            if len(r['text']) > allocation:
                last_period = text.rfind('. ')
                if last_period > allocation * 0.7:
                    text = text[:last_period + 1]
                text += "\n\n[... truncated ...]"

        source_header = f"\n{'='*80}\n"
        source_header += f"## Source {i}: {r['title']}\n"
        source_header += f"URL: {r['url']}\n"
        source_header += f"{'='*80}\n\n"

        sections.append(source_header + text)

    document = header + toc + "\n".join(sections)

    # Final safety trim
    if len(document) > char_limit:
        document = document[:char_limit]
        document = document[:document.rfind('\n')]
        document += "\n\n[Truncated to character limit]"

    return document


# ─── Search Suggestions ─────────────────────────────────────────────────────

def print_search_suggestions(book_query):
    """Print suggested Google search queries for finding book context."""
    queries = [
        f'{book_query} book summary',
        f'{book_query} book review',
        f'{book_query} key takeaways',
        f'{book_query} chapter summary',
        f'{book_query} author interview',
        f'{book_query} main ideas concepts',
        f'{book_query} book notes',
        f'{book_query} goodreads',
    ]

    print("\n" + "="*80)
    print(f"SUGGESTED SEARCHES for: {book_query}")
    print("="*80)
    print("\nOpen these search pages in Chrome, then run the scraper:\n")

    for i, q in enumerate(queries, 1):
        url = f"https://www.google.com/search?q={quote_plus(q)}"
        print(f"  {i}. {q}")
        print(f"     {url}\n")

    print("The script will automatically extract links from your Google search tabs")
    print("and scrape each result page.\n")
    print("Run:  python 06-book_context_scraper.py --title \"Your Book Title\"")
    print("="*80)


# ─── Main ────────────────────────────────────────────────────────────────────

def create_safe_filename(title):
    """Create a filesystem-safe filename from a title."""
    safe = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    return safe[:50] if len(safe) > 50 else safe


def main():
    parser = argparse.ArgumentParser(
        description="Scrape all open Chrome tabs to build book context (under 150k chars)."
    )
    parser.add_argument('--title', type=str, default=None,
                        help='Book title (used for output filename)')
    parser.add_argument('--char-limit', type=int, default=DEFAULT_CHAR_LIMIT,
                        help=f'Max character count (default: {DEFAULT_CHAR_LIMIT:,})')
    parser.add_argument('--urls', type=str, default=None,
                        help='Path to a text file with URLs to scrape (one per line)')
    parser.add_argument('--suggest', type=str, default=None,
                        help='Print suggested search queries (no scraping)')
    parser.add_argument('--no-clipboard', action='store_true',
                        help='Skip copying to clipboard')

    args = parser.parse_args()

    # Mode: Just print search suggestions
    if args.suggest:
        print_search_suggestions(args.suggest)
        return

    # Check Anthropic API key (required)
    claude_client = get_anthropic_client()
    print("Claude API: ready\n")

    # Check Chrome
    if not check_chrome_running():
        print("Chrome is not running with remote debugging.")
        print("\nStart Chrome with:")
        print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome "
              "--remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile")
        proceed = input("\nTry to continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            return

    browser = connect_to_chrome()
    if not browser:
        return

    try:
        results = []

        if args.urls:
            # Mode: Scrape from URL file
            if not os.path.exists(args.urls):
                print(f"File not found: {args.urls}")
                return
            with open(args.urls, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"Loaded {len(urls)} URL(s) from {args.urls}.\n")
            for i, url in enumerate(urls, 1):
                result = scrape_url(browser, url, i, len(urls))
                if result:
                    results.append(result)

        else:
            # Default: Scrape all open tabs (detects CodePen book notes automatically)
            tabs = browser.window_handles
            print(f"Scraping {len(tabs)} open tab(s)...\n")
            for i, handle in enumerate(tabs, 1):
                browser.switch_to.window(handle)
                time.sleep(0.5)
                try:
                    browser.execute_script("if(document.activeElement) document.activeElement.blur();")
                except Exception:
                    pass
                url = browser.current_url
                html = browser.page_source
                if is_book_notes_page(url, html):
                    notes = extract_book_notes(html)
                    if notes:
                        print(f"  [{i}/{len(tabs)}] Book Notes page: {len(notes)} note(s)")
                        results.extend(notes)
                    else:
                        print(f"  [{i}/{len(tabs)}] Book Notes page: empty")
                    continue
                result = scrape_tab_content(browser, handle, i, len(tabs))
                if result:
                    results.append(result)

        if not results:
            print("\nNo content was scraped.")
            return

        # Summary
        total_raw = sum(r['char_count'] for r in results)
        print(f"\n{'─'*60}")
        print(f"Scraped {len(results)} source(s), {total_raw:,} raw characters total.")
        print(f"Character limit: {args.char_limit:,}")

        print(f"Claude API: will clean/structure content")
        print(f"{'─'*60}\n")

        # Get book title
        book_title = args.title
        if not book_title:
            book_title = input("Enter book title (for output filename): ").strip()
            if not book_title:
                book_title = "book_context"

        # Compile
        print("Compiling context document...")
        document = compile_context(results, book_title, args.char_limit, claude_client)

        if not document:
            return

        # Save
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        safe_name = create_safe_filename(book_title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(OUTPUT_DIR, f"book_context_{safe_name}_{timestamp}.txt")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(document)

        print(f"\nSaved to: {filepath}")
        print(f"Final size: {len(document):,} characters")
        print(f"Sources included: {len(results)}")

        # Copy to clipboard
        if not args.no_clipboard:
            try:
                import subprocess
                subprocess.run(['pbcopy'], input=document.encode(), check=True)
                print("Copied to clipboard.")
            except Exception:
                print("Could not copy to clipboard.")

    finally:
        browser.quit()


if __name__ == "__main__":
    main()
