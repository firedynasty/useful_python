#!/usr/bin/env python3
"""
Scrape Romans Bible study from studyandobey.com
Saves combined content to ./romans_study/
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


# Remaining Romans study URLs (resume from failed)
URLS = [
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans6-1-14/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans6-15-23/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans7-1-12/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans7-13-25/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans8-1-17/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans8-18-39/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans9-1-13/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans10/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans11/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans12/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans13/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans14-13-15-6/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans15/",
    "https://studyandobey.com/inductive-bible-study/romans-studies/romans16/",
]


def connect_to_existing_chrome():
    """Connect to an already running Chrome instance with remote debugging"""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        print("Connecting to Chrome on port 9222...")
        # Try without webdriver_manager first (uses system chromedriver)
        try:
            driver = webdriver.Chrome(options=options)
        except Exception:
            # Fallback to webdriver_manager
            print("Trying with ChromeDriverManager...")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        print("Successfully connected to Chrome!")
        return driver
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")
        print("\nMake sure Chrome is running with:")
        print('  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222')
        return None


def url_to_header(url):
    """
    Convert URL to readable header.
    E.g., '.../romans1-1-17/' -> 'Romans 1:1-17'
         '.../romans10/' -> 'Romans 10'
         '.../romans14-13-15-6/' -> 'Romans 14:13-15:6'
    """
    # Extract the last part of the URL (the passage identifier)
    slug = url.rstrip('/').split('/')[-1]

    # Handle "romans14-13-15-6" format (cross-chapter reference)
    cross_chapter = re.match(r'romans(\d+)-(\d+)-(\d+)-(\d+)', slug)
    if cross_chapter:
        ch1, v1, ch2, v2 = cross_chapter.groups()
        return f"Romans {ch1}:{v1}-{ch2}:{v2}"

    # Handle "romans1-1-17" format (chapter:verse-verse)
    verse_range = re.match(r'romans(\d+)-(\d+)-(\d+)', slug)
    if verse_range:
        ch, v1, v2 = verse_range.groups()
        return f"Romans {ch}:{v1}-{v2}"

    # Handle "romans10" format (whole chapter)
    chapter_only = re.match(r'romans(\d+)$', slug)
    if chapter_only:
        return f"Romans {chapter_only.group(1)}"

    # Fallback
    return f"Romans {slug.replace('romans', '')}"


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

        # Wait for content to load (longer timeout)
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article, .entry-content, .post-content, main"))
        )
        time.sleep(4)  # Extra wait for full render

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
    print("StudyAndObey Scraper - Romans Bible Study")
    print("="*60)

    # Create output directory
    output_dir = "./romans_study"
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
            time.sleep(3)

        # Append to combined file
        combined_path = os.path.join(output_dir, "romans_combined.txt")
        with open(combined_path, 'a', encoding='utf-8') as f:
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
