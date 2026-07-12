#!/usr/bin/env python3
"""
Scrape 2 Corinthians Bible study from studyandobey.com
Saves combined content to ./2corinthians_study/
"""

import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


# All 2 Corinthians study URLs
URLS = [
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-1-1-11/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-1-12-24/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-2-1-11/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-2-12-17/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-3-1-6/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-3-7-18/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-4/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-4-7-12/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-4-13-18/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-5-1-10/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-5-11-15/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-5-16-21/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-6-1-10/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-6-11-18/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-7-1-5/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-7-6-16/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-8-1-7/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2corinthians-8-8-15/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-8-16-24/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-9-1-7/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-9-8-15/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-10-1-6/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-10-7-18/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2corinthians-11-1-15/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-11-16-33/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-12-1-10/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2-corinthians-12-11-21/",
    "https://studyandobey.com/inductive-bible-study/2-corinthians/2_corinthians_13/",
]


def connect_to_existing_chrome():
    """Connect to an already running Chrome instance with remote debugging"""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        print("Setting up ChromeDriver...")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        print("Successfully connected to Chrome!")
        return driver
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")
        print("\nMake sure Chrome is running with --remote-debugging-port=9222")
        return None


def url_to_header(url):
    """
    Convert URL to readable header.
    E.g., '.../2-corinthians-1-1-11/' -> '2 Corinthians 1:1-11'
    """
    # Extract the last part of the URL (the passage identifier)
    slug = url.rstrip('/').split('/')[-1]

    # Handle various formats: 2-corinthians-1-1-11, 2corinthians-8-8-15, 2_corinthians_13
    # Normalize to common format
    slug = slug.replace('_', '-').replace('2corinthians', '2-corinthians')

    # Remove '2-corinthians-' prefix
    passage = slug.replace('2-corinthians-', '')

    # Parse the passage reference
    parts = passage.split('-')

    if len(parts) == 1:
        # Just chapter: "13" -> "2 Corinthians 13"
        return f"2 Corinthians {parts[0]}"
    elif len(parts) == 2:
        # Chapter and single verse or range start: "4-7" could be ch4 v7 or ambiguous
        # Based on the URLs, this seems to be chapter-verse_start
        return f"2 Corinthians {parts[0]}:{parts[1]}"
    elif len(parts) == 3:
        # Chapter-verse_start-verse_end: "1-1-11" -> "1:1-11"
        return f"2 Corinthians {parts[0]}:{parts[1]}-{parts[2]}"
    else:
        # Fallback
        return f"2 Corinthians {passage}"


def extract_study_content(html):
    """Extract Bible study content from studyandobey.com HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # Try various content selectors for studyandobey.com
    content_selectors = [
        "article.post",
        ".entry-content",
        ".post-content",
        "article",
        ".content",
        "main"
    ]

    content_element = None
    for selector in content_selectors:
        content_element = soup.select_one(selector)
        if content_element:
            print(f"  Found content using selector: {selector}")
            break

    if not content_element:
        print("  Warning: Could not find content element")
        return None

    # Remove unwanted elements
    for element in content_element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()

    # Remove share buttons, subscribe forms, etc.
    for unwanted in content_element.find_all(class_=lambda x: x and any(
        term in str(x).lower() for term in ['share', 'social', 'subscribe', 'newsletter', 'sidebar', 'widget', 'comment', 'related']
    )):
        unwanted.decompose()

    # Remove navigation links
    for nav in content_element.find_all(['nav', 'ul'], class_=lambda x: x and 'nav' in str(x).lower()):
        nav.decompose()

    # Extract text content
    text = content_element.get_text(separator='\n', strip=True)

    # Clean up the text
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove multiple blank lines
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

    # Remove common navigation/UI text
    patterns_to_remove = [
        r'Share this:.*?(?=\n|$)',
        r'Like this:.*?(?=\n|$)',
        r'Loading\.\.\.',
        r'Subscribe.*?(?=\n|$)',
        r'Click to share.*?(?=\n|$)',
        r'Previous Post.*?(?=\n|$)',
        r'Next Post.*?(?=\n|$)',
        r'Leave a Reply.*',
        r'Comment \*.*',
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    return text.strip()


def scrape_url(browser, url):
    """Scrape a single study page"""
    header = url_to_header(url)
    print(f"\nScraping: {header}")
    print(f"  URL: {url}")

    try:
        browser.get(url)

        # Wait for content to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article, .entry-content, .post-content, main"))
        )
        time.sleep(2)  # Extra wait for full render

        html = browser.page_source
        content = extract_study_content(html)

        if content:
            print(f"  Extracted {len(content)} characters")
            return header, content
        else:
            print(f"  Failed to extract content")
            return header, None

    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return header, None


def main():
    print("="*60)
    print("StudyAndObey Scraper - 2 Corinthians Bible Study")
    print("="*60)

    # Create output directory
    output_dir = "./2corinthians_study"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Connect to Chrome
    browser = connect_to_existing_chrome()
    if not browser:
        print("\nFailed to connect to Chrome.")
        print("Start Chrome with: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        return

    try:
        # Scrape all URLs
        successful = 0
        failed = []
        all_content = []

        for i, url in enumerate(URLS, 1):
            header, content = scrape_url(browser, url)

            if content:
                all_content.append((header, content))
                successful += 1
            else:
                failed.append(url)

            # Be polite to the server
            time.sleep(2)

        # Save combined file
        combined_path = os.path.join(output_dir, "2corinthians_combined.txt")
        with open(combined_path, 'w', encoding='utf-8') as f:
            for header, content in all_content:
                f.write(f"## {header}\n")
                f.write("-" * 40 + "\n\n")
                f.write(content)
                f.write("\n\n" + "=" * 60 + "\n\n")

        print(f"\nSaved combined file to: {combined_path}")

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Successfully scraped: {successful}/{len(URLS)} pages")
        if failed:
            print(f"Failed URLs:")
            for url in failed:
                print(f"  - {url}")
        print(f"Combined output: {combined_path}")

        # File size
        file_size = os.path.getsize(combined_path)
        print(f"Output file size: {file_size/1024:.1f} KB")

    finally:
        browser.quit()


if __name__ == "__main__":
    main()
