"""
Table Scraper - Scrape HTML tables from web pages using Chrome remote debugging.

Workflow:
1. Start Chrome with remote debugging:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile

2. Open the page with the table you want to scrape.

3. Run this script:
   python 07-table_scraper.py                          # Scrape table from active Chrome tab
   python 07-table_scraper.py --file input.html         # Parse table from local HTML file
   python 07-table_scraper.py --table-index 1           # Select specific table (0-based, default: 0)
   python 07-table_scraper.py --output my_data.csv      # Custom output filename

Usage:
    python 07-table_scraper.py                    # Scrape from active Chrome tab
    python 07-table_scraper.py --file page.html   # Parse from local HTML file
"""

import os
import sys
import csv
import re
import socket
import argparse
from datetime import datetime

from bs4 import BeautifulSoup


# ─── Configuration ───────────────────────────────────────────────────────────

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
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager

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


# ─── Table Extraction ──────────────────────────────────────────────────────

def clean_text(text):
    """Clean extracted text: normalize whitespace, strip extra spaces."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_tables(html, table_index=None):
    """
    Extract tables from HTML and return as list of dicts.

    Args:
        html: Raw HTML string
        table_index: Which table to extract (0-based). None extracts all.

    Returns:
        List of tables, where each table is a list of row dicts.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find all tables (including tbody-only if no <table> wrapper)
    tables = soup.find_all('table')
    if not tables:
        # Try finding standalone tbody elements
        tbodies = soup.find_all('tbody')
        if tbodies:
            tables = tbodies

    if not tables:
        print("No tables found in the HTML.")
        return []

    print(f"Found {len(tables)} table(s) in the page.")

    if table_index is not None:
        if table_index >= len(tables):
            print(f"Table index {table_index} out of range (0-{len(tables)-1}).")
            return []
        tables = [tables[table_index]]
        print(f"Extracting table at index {table_index}.")

    all_tables = []

    for t_idx, table in enumerate(tables):
        rows_data = []

        # Get headers from <thead> or first <tr> with <th>
        headers = []
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [clean_text(th.get_text()) for th in header_row.find_all(['th', 'td'])]

        # If no thead, check first row for <th> elements
        if not headers:
            first_row = table.find('tr')
            if first_row:
                ths = first_row.find_all('th')
                if ths:
                    headers = [clean_text(th.get_text()) for th in ths]

        # Get body rows
        tbody = table.find('tbody') or table
        rows = tbody.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            # Skip if this is a header row we already processed
            if all(c.name == 'th' for c in cells) and headers:
                continue

            row_data = {}
            for i, cell in enumerate(cells):
                # Get column name from class or header
                col_name = None
                cell_classes = cell.get('class', [])
                for cls in cell_classes:
                    if cls.startswith('column-'):
                        col_name = cls
                        break

                if not col_name and i < len(headers):
                    col_name = headers[i]
                if not col_name:
                    col_name = f"column_{i+1}"

                # Extract text content
                text = clean_text(cell.get_text())

                # Also extract links if present
                links = []
                for a in cell.find_all('a'):
                    href = a.get('href', '')
                    link_text = clean_text(a.get_text())
                    if href and not href.startswith('#'):
                        links.append(href)

                row_data[col_name] = text
                if links:
                    row_data[f"{col_name}_links"] = ' | '.join(links)

            if row_data:
                rows_data.append(row_data)

        if rows_data:
            print(f"  Table {t_idx}: {len(rows_data)} rows, {len(rows_data[0])} columns")
            all_tables.append(rows_data)

    return all_tables


def save_to_csv(table_data, filepath):
    """Save table data (list of dicts) to CSV."""
    if not table_data:
        return

    # Collect all column names preserving order
    columns = []
    for row in table_data:
        for key in row:
            if key not in columns:
                columns.append(key)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(table_data)

    print(f"Saved {len(table_data)} rows to: {filepath}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scrape HTML tables from web pages or local files."
    )
    parser.add_argument('--file', type=str, default=None,
                        help='Path to local HTML file to parse')
    parser.add_argument('--table-index', type=int, default=0,
                        help='Which table to extract (0-based index, default: 0)')
    parser.add_argument('--all-tables', action='store_true',
                        help='Extract all tables from the page')
    parser.add_argument('--output', type=str, default=None,
                        help='Output CSV filename')

    args = parser.parse_args()

    html = None

    if args.file:
        # Parse from local file
        if not os.path.exists(args.file):
            print(f"File not found: {args.file}")
            return
        with open(args.file, 'r', encoding='utf-8') as f:
            html = f.read()
        print(f"Loaded HTML from: {args.file}")
    else:
        # Scrape from active Chrome tab
        if not check_chrome_running():
            print("Chrome is not running with remote debugging.")
            print("\nStart Chrome with:")
            print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome "
                  "--remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile")
            return

        browser = connect_to_chrome()
        if not browser:
            return

        try:
            url = browser.current_url
            title = browser.title or "Untitled"
            print(f"Page: {title}")
            print(f"URL:  {url}\n")
            html = browser.page_source
        finally:
            pass  # Don't quit - leave Chrome open

    if not html:
        print("No HTML content to parse.")
        return

    # Extract tables
    table_index = None if args.all_tables else args.table_index
    tables = extract_tables(html, table_index=table_index)

    if not tables:
        print("No table data extracted.")
        return

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, table_data in enumerate(tables):
        if args.output:
            if len(tables) > 1:
                base, ext = os.path.splitext(args.output)
                filepath = os.path.join(OUTPUT_DIR, f"{base}_table{i}{ext}")
            else:
                filepath = os.path.join(OUTPUT_DIR, args.output)
        else:
            suffix = f"_table{i}" if len(tables) > 1 else ""
            filepath = os.path.join(OUTPUT_DIR, f"table_scrape{suffix}_{timestamp}.csv")

        save_to_csv(table_data, filepath)

    print(f"\nDone. Extracted {sum(len(t) for t in tables)} total rows from {len(tables)} table(s).")


if __name__ == "__main__":
    main()
