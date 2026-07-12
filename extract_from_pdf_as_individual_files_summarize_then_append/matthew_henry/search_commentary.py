#!/usr/bin/env python3
"""
Matthew Henry Commentary Search Tool
Searches through all HTM files for keywords and displays results with context.
"""

import os
import re
import argparse
from html.parser import HTMLParser
from pathlib import Path

# Book codes mapping (MHC file prefix -> book name)
BOOKS = {
    '00': 'Preface',
    # Old Testament
    '01': 'Genesis', '02': 'Exodus', '03': 'Leviticus', '04': 'Numbers', '05': 'Deuteronomy',
    '06': 'Joshua', '07': 'Judges', '08': 'Ruth', '09': '1 Samuel', '10': '2 Samuel',
    '11': '1 Kings', '12': '2 Kings', '13': '1 Chronicles', '14': '2 Chronicles',
    '15': 'Ezra', '16': 'Nehemiah', '17': 'Esther', '18': 'Job', '19': 'Psalms',
    '20': 'Proverbs', '21': 'Ecclesiastes', '22': 'Song of Solomon', '23': 'Isaiah',
    '24': 'Jeremiah', '25': 'Lamentations', '26': 'Ezekiel', '27': 'Daniel',
    '28': 'Hosea', '29': 'Joel', '30': 'Amos', '31': 'Obadiah', '32': 'Jonah',
    '33': 'Micah', '34': 'Nahum', '35': 'Habakkuk', '36': 'Zephaniah', '37': 'Haggai',
    '38': 'Zechariah', '39': 'Malachi',
    # New Testament
    '40': 'Matthew', '41': 'Mark', '42': 'Luke', '43': 'John', '44': 'Acts',
    '45': 'Romans', '46': '1 Corinthians', '47': '2 Corinthians', '48': 'Galatians',
    '49': 'Ephesians', '50': 'Philippians', '51': 'Colossians', '52': '1 Thessalonians',
    '53': '2 Thessalonians', '54': '1 Timothy', '55': '2 Timothy', '56': 'Titus',
    '57': 'Philemon', '58': 'Hebrews', '59': 'James', '60': '1 Peter', '61': '2 Peter',
    '62': '1 John', '63': '2 John', '64': '3 John', '65': 'Jude', '66': 'Revelation',
}

# Reverse lookup: book name -> code
BOOK_CODES = {v.lower(): k for k, v in BOOKS.items()}
# Add common abbreviations
BOOK_CODES.update({
    'gen': '01', 'ex': '02', 'exod': '02', 'lev': '03', 'num': '04', 'deut': '05',
    'josh': '06', 'judg': '07', '1sam': '09', '2sam': '10', '1ki': '11', '2ki': '12',
    '1chr': '13', '2chr': '14', 'neh': '16', 'est': '17', 'ps': '19', 'psalm': '19',
    'prov': '20', 'eccl': '21', 'song': '22', 'isa': '23', 'jer': '24', 'lam': '25',
    'ezek': '26', 'dan': '27', 'hos': '28', 'ob': '31', 'mic': '33', 'nah': '34',
    'hab': '35', 'zeph': '36', 'hag': '37', 'zech': '38', 'mal': '39',
    'matt': '40', 'mt': '40', 'mk': '41', 'lk': '42', 'jn': '43', 'rom': '45',
    '1cor': '46', '2cor': '47', 'gal': '48', 'eph': '49', 'phil': '50', 'col': '51',
    '1thess': '52', '2thess': '53', '1tim': '54', '2tim': '55', 'tit': '56',
    'phm': '57', 'heb': '58', 'jas': '59', '1pet': '60', '2pet': '61',
    '1jn': '62', '2jn': '63', '3jn': '64', 'rev': '66',
})


def list_books():
    """Print available books."""
    print("\nAvailable books:")
    print("-" * 40)
    print("Old Testament:")
    for code in range(1, 40):
        c = f'{code:02d}'
        if c in BOOKS:
            print(f"  {c}: {BOOKS[c]}")
    print("\nNew Testament:")
    for code in range(40, 67):
        c = f'{code:02d}'
        if c in BOOKS:
            print(f"  {c}: {BOOKS[c]}")


def get_book_code(book_name):
    """Get the book code from a book name or abbreviation."""
    book_lower = book_name.lower().strip()
    # Direct code match (e.g., "01", "40")
    if book_lower in BOOKS:
        return book_lower
    # Name or abbreviation match
    if book_lower in BOOK_CODES:
        return BOOK_CODES[book_lower]
    # Partial match
    for name, code in BOOK_CODES.items():
        if name.startswith(book_lower) or book_lower in name:
            return code
    return None


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML content."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts)


def strip_html(html_content):
    """Remove HTML tags and return plain text."""
    parser = HTMLTextExtractor()
    try:
        parser.feed(html_content)
        return parser.get_text()
    except:
        # Fallback: simple regex-based stripping
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        return text


def get_title_from_html(html_content):
    """Extract the title from HTML content."""
    match = re.search(r'<TITLE[^>]*>(.*?)</TITLE>', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Unknown"


def highlight_match(text, keyword, case_insensitive=True):
    """Highlight the keyword in the text with ANSI colors."""
    flags = re.IGNORECASE if case_insensitive else 0
    pattern = re.compile(f'({re.escape(keyword)})', flags)
    return pattern.sub(r'\033[1;33m\1\033[0m', text)


def get_context(text, keyword, context_chars=150, case_insensitive=True):
    """Get text surrounding each match of the keyword."""
    flags = re.IGNORECASE if case_insensitive else 0
    pattern = re.compile(re.escape(keyword), flags)

    contexts = []
    for match in pattern.finditer(text):
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)

        # Adjust to word boundaries
        if start > 0:
            space_pos = text.rfind(' ', start - 20, start)
            if space_pos != -1:
                start = space_pos + 1

        if end < len(text):
            space_pos = text.find(' ', end, end + 20)
            if space_pos != -1:
                end = space_pos

        context = text[start:end].strip()
        # Clean up whitespace
        context = re.sub(r'\s+', ' ', context)

        prefix = '...' if start > 0 else ''
        suffix = '...' if end < len(text) else ''

        contexts.append(f"{prefix}{context}{suffix}")

    return contexts


def search_files(directory, keyword, case_insensitive=True, context_chars=150, max_results=None, book_code=None):
    """Search through all HTM files in the directory."""
    results = []

    if book_code:
        # Filter to specific book
        htm_files = sorted(Path(directory).glob(f'MHC{book_code}*.HTM'))
    else:
        htm_files = sorted(Path(directory).glob('MHC*.HTM'))

    flags = re.IGNORECASE if case_insensitive else 0
    pattern = re.compile(re.escape(keyword), flags)

    for filepath in htm_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            title = get_title_from_html(html_content)
            text = strip_html(html_content)

            matches = pattern.findall(text)
            if matches:
                contexts = get_context(text, keyword, context_chars, case_insensitive)
                results.append({
                    'file': filepath.name,
                    'title': title,
                    'count': len(matches),
                    'contexts': contexts
                })

                if max_results and len(results) >= max_results:
                    break

        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Search Matthew Henry Commentary for keywords',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python search_commentary.py grace
  python search_commentary.py "eternal life" -c 200
  python search_commentary.py faith --case-sensitive
  python search_commentary.py redemption -n 10
  python search_commentary.py "Holy Spirit" --no-context
  python search_commentary.py grace -b romans
  python search_commentary.py faith -b john
  python search_commentary.py --list-books
        '''
    )
    parser.add_argument('keyword', nargs='?', help='Keyword or phrase to search for')
    parser.add_argument('-b', '--book', default=None,
                        help='Filter by book (e.g., "genesis", "gen", "romans", "rom", "01", "45")')
    parser.add_argument('--list-books', action='store_true',
                        help='List all available books and their codes')
    parser.add_argument('-d', '--directory', default='.',
                        help='Directory containing HTM files (default: current directory)')
    parser.add_argument('-c', '--context', type=int, default=150,
                        help='Number of characters of context around matches (default: 150)')
    parser.add_argument('-n', '--max-results', type=int, default=None,
                        help='Maximum number of files to show results from')
    parser.add_argument('--case-sensitive', action='store_true',
                        help='Make search case-sensitive (default: case-insensitive)')
    parser.add_argument('--no-context', action='store_true',
                        help='Only show file names and match counts, no context')
    parser.add_argument('--max-contexts', type=int, default=3,
                        help='Maximum number of context snippets per file (default: 3)')

    args = parser.parse_args()

    # Handle --list-books
    if args.list_books:
        list_books()
        return

    # Require keyword if not listing books
    if not args.keyword:
        parser.error("keyword is required (or use --list-books)")

    # Handle book filter
    book_code = None
    book_name = None
    if args.book:
        book_code = get_book_code(args.book)
        if not book_code:
            print(f"Error: Unknown book '{args.book}'")
            print("Use --list-books to see available books")
            return
        book_name = BOOKS.get(book_code, args.book)

    case_insensitive = not args.case_sensitive

    print(f"\nSearching for: \"{args.keyword}\"")
    if book_name:
        print(f"Book: {book_name}")
    print(f"Case {'in' if case_insensitive else ''}sensitive search")
    print("-" * 60)

    results = search_files(
        args.directory,
        args.keyword,
        case_insensitive=case_insensitive,
        context_chars=args.context,
        max_results=args.max_results,
        book_code=book_code
    )

    if not results:
        print(f"\nNo matches found for \"{args.keyword}\"")
        return

    total_matches = sum(r['count'] for r in results)
    print(f"\nFound {total_matches} matches in {len(results)} files\n")

    for result in results:
        # Clean up the title for display
        title = result['title'].replace("Matthew Henry's Complete Commentary on the Whole Bible ", "")
        print(f"\033[1;36m{result['file']}\033[0m - {title}")
        print(f"  Matches: {result['count']}")

        if not args.no_context:
            contexts = result['contexts'][:args.max_contexts]
            for i, ctx in enumerate(contexts, 1):
                highlighted = highlight_match(ctx, args.keyword, case_insensitive)
                print(f"  [{i}] {highlighted}")

            if len(result['contexts']) > args.max_contexts:
                print(f"  ... and {len(result['contexts']) - args.max_contexts} more matches")

        print()


if __name__ == '__main__':
    main()
