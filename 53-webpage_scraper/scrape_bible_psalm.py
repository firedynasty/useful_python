#!/usr/bin/env python3
"""
Scrape Psalms 1-150 from Bible Gateway (NLT)
Saves each psalm to ./bible/psalms/
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


def extract_bible_passage(html):
    """Extract Bible passage text from Bible Gateway HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # Bible Gateway uses .passage-text for the main passage content
    passage_selectors = [
        ".passage-text",
        ".passage-content",
        "#passage-container",
        ".result-text-style-normal"
    ]

    passage_content = None
    for selector in passage_selectors:
        passage_content = soup.select_one(selector)
        if passage_content:
            print(f"  Found content using selector: {selector}")
            break

    if not passage_content:
        print("  Warning: Could not find passage content")
        return None

    # Remove unwanted elements (but keep verse numbers)
    for element in passage_content.find_all(['script', 'style']):
        element.decompose()

    # Remove only footnote superscripts, NOT verse numbers
    for sup in passage_content.find_all('sup'):
        # Keep verse numbers (they have class 'versenum')
        if 'versenum' not in sup.get('class', []):
            sup.decompose()

    # Remove footnotes section
    for footnotes in passage_content.find_all(class_=['footnotes', 'crossrefs', 'passage-other-trans']):
        footnotes.decompose()

    # Remove crossreference links but keep verse numbers
    for crossref in passage_content.find_all(class_=['crossreference', 'crossref']):
        crossref.decompose()

    # Extract text with verse numbers
    lines = []

    # Get the chapter title if available
    chapter_title = soup.select_one('.dropdown-display-text')
    if chapter_title:
        lines.append(chapter_title.get_text(strip=True))
        lines.append("")

    # Process each verse
    for verse in passage_content.find_all(['p', 'div'], class_=lambda x: x and ('text' in str(x).lower() or 'verse' in str(x).lower())):
        verse_text = verse.get_text(separator=' ', strip=True)
        if verse_text:
            lines.append(verse_text)

    # If no verses found with specific classes, get all text
    if len(lines) <= 2:
        text = passage_content.get_text(separator='\n', strip=True)
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text

    return '\n\n'.join(lines)


def scrape_chapter(browser, chapter_num):
    """Scrape a single chapter from Bible Gateway"""
    url = f"https://www.biblegateway.com/passage/?search=psalm%20{chapter_num}&version=NLT"
    print(f"\nScraping Psalm {chapter_num}...")
    print(f"  URL: {url}")

    try:
        browser.get(url)

        # Wait for content to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".passage-text, .passage-content"))
        )
        time.sleep(1)  # Extra wait for full render

        html = browser.page_source
        passage_text = extract_bible_passage(html)

        if passage_text:
            print(f"  Extracted {len(passage_text)} characters")
            return passage_text
        else:
            print(f"  Failed to extract content")
            return None

    except Exception as e:
        print(f"  Error scraping chapter {chapter_num}: {e}")
        return None


def main():
    print("="*60)
    print("Bible Gateway Scraper - Psalms (NLT)")
    print("="*60)

    # Create output directory
    output_dir = "./bible/psalms"
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
        # Scrape all 150 psalms
        successful = 0
        failed = []

        for chapter in range(1, 151):  # 1 to 150
            content = scrape_chapter(browser, chapter)

            if content:
                # Save to file
                filename = f"psalm_{chapter:03d}.txt"
                filepath = os.path.join(output_dir, filename)

                # Add header
                full_content = f"Psalm {chapter} (NLT)\n"
                full_content += "="*40 + "\n\n"
                full_content += content

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(full_content)

                print(f"  Saved to: {filepath}")
                successful += 1
            else:
                failed.append(chapter)

            # Be polite to the server
            time.sleep(2)

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Successfully scraped: {successful}/150 psalms")
        if failed:
            print(f"Failed chapters: {failed}")
        print(f"Files saved to: {output_dir}/")

    finally:
        browser.quit()


if __name__ == "__main__":
    main()
