# This code is a Python script that extracts content from web pages open in Google Chrome and formats it for easy analysis. It's designed to help users grab article text without the clutter of ads, navigation menus, and other unnecessary elements. Here's a breakdown of what it does:

# ## Main Functionality

# The script connects to an already running Chrome browser, extracts the main content from the current web page, converts it to plain text, and copies it to the clipboard with some formatting. It's particularly useful for quickly preparing web content for summarization by AI tools.

# ## Key Components

# 1. **Chrome Connection**:
#    - Connects to an existing Chrome instance through remote debugging (port 9222)
#    - Requires Chrome to be started with a special flag (`--remote-debugging-port=9222`)

# 2. **Content Extraction**:
#    - Uses BeautifulSoup to parse the HTML and extract the main content
#    - Has a list of common selectors for article content (like `.article-content`, `#article-body`, etc.)
#    - Falls back to the entire body if it can't find specific content areas

# 3. **Text Processing**:
#    - Converts HTML to plain text using the html2text library
#    - Cleans up the text by removing extra line breaks and Markdown formatting
#    - Creates a formatted output with metadata like URL and title

# 4. **Special Handling**:
#    - Has specific logic for a Bible app running on localhost:3000, extracting just chapter content
#    - For other websites, it attempts to add metadata including publication date

# 5. **Clipboard Integration**:
#    - Uses pyperclip to copy the processed content to the clipboard
#    - Adds a template text (by default "summarize this from:") before the content

# ## Workflow

# 1. The user launches Chrome with remote debugging enabled
# 2. They navigate to the web page they want to extract content from
# 3. The user runs this script, which:
#    - Connects to Chrome
#    - Extracts the main content
#    - Processes it into clean text
#    - Copies it to the clipboard with a template
# 4. The user can then paste this content into another application (likely an AI tool)

# ## Notable Features

# - Tries multiple CSS selectors to find the main content
# - Removes scripts, styles, iframes, and other non-content elements
# - Special handling for a Bible application
# - Attempts to extract publication dates from various common formats
# - Provides clear instructions for starting Chrome with debugging enabled
# - Handles errors gracefully with helpful messages

# This script would be particularly useful for researchers, writers, or anyone who needs to quickly extract and analyze content from web pages without the distraction of ads and other irrelevant elements.


import os
import time
import subprocess
import re
import platform
import pyperclip  # For clipboard operations
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import html2text

def connect_to_existing_chrome():
    """Connect to an already running Chrome instance with remote debugging"""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        # Try to use the existing driver if available
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")
        print("Make sure Chrome is running with --remote-debugging-port=9222")
        return None

def extract_main_content(html, content_selectors=None):
    """Extract the main content from HTML using BeautifulSoup"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Default selectors for common article content areas
    if content_selectors is None:
        content_selectors = [
            "article", 
            ".article-content", 
            ".article__body", 
            ".story-body",
            ".main-content",
            "#article-body",
            ".post-content",
            ".entry-content",
            ".content-article",
            ".wsj-snippet-body",
            ".article-wrap",
            ".wsj-article-body"
        ]
    
    # Try each selector
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content and len(main_content.get_text(strip=True)) > 200:
            print(f"Found content using selector: {selector}")
            break
    else:
        # Fallback to the whole body
        print("Using body as fallback")
        main_content = soup.body
    
    # Remove unwanted elements
    if main_content:
        for element in main_content.find_all(['script', 'style', 'iframe', 'noscript']):
            element.decompose()
    
    return main_content

def html_to_plain_text(html_content):
    """Convert HTML to plain text optimized for AI analysis"""
    try:
        # Convert HTML to plain text
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.body_width = 0  # Don't wrap text at a specific width
        converter.ignore_images = True
        converter.ignore_tables = False
        converter.single_line_break = True  # Better paragraph handling
        converter.unicode_snob = True  # Use Unicode, not ASCII
        plain_text = converter.handle(str(html_content))
        
        # Additional cleanup for AI processing
        # Remove multiple blank lines
        plain_text = re.sub(r'\n\s*\n', '\n\n', plain_text)
        
        # Remove most Markdown formatting artifacts that aren't useful for AI
        plain_text = re.sub(r'\*\*', '', plain_text)  # Remove bold markers
        plain_text = re.sub(r'__', '', plain_text)    # Remove alternate bold markers
        
        return plain_text
    except Exception as e:
        print(f"Error converting to plain text: {e}")
        return ""

def grab_active_window_to_clipboard(template_text=None):
    """
    Grab text content from the currently open Chrome tab and copy to clipboard
    
    Args:
        template_text (str, optional): Custom template text to prepend to content.
                                      If None, default templates will be used based on content type.
    """
    try:
        print("Connecting to existing Chrome instance...")
        browser = connect_to_existing_chrome()
        
        if not browser:
            print("Failed to connect to Chrome. Make sure it's running with remote debugging enabled.")
            return False
        
        print("Getting current page content...")
        current_url = browser.current_url
        print(f"Current URL: {current_url}")
        
        # Get the page HTML
        html = browser.page_source
        
        # Process the content
        main_content = extract_main_content(html)
        if not main_content:
            print("Warning: Could not extract specific content, using full page.")
            main_content = html
        
        # Get plain text
        plain_text = html_to_plain_text(main_content)
        
        # Default template to use for all websites
        default_template = "summarize this from:\n\n"
        template = template_text if template_text is not None else default_template
        
        # Skip the metadata and separator line
        # Check if we're scraping the biblical content site
        if "localhost:3000" in current_url:
            # We're on the Bible app - extract only the specific chapter content
            # Look for the actual chapter content (skipping the book list and navigation)
            # This pattern will match any Bible book (Genesis, Exodus, Psalms, etc.)
            chapter_content_match = re.search(r'(## [A-Za-z ]+ \d+\n)([\s\S]*?)(?:< Previous Chapter|## Ask about Scripture)', plain_text)
            if chapter_content_match:
                # Keep the title and extract only the verses content
                chapter_title = chapter_content_match.group(1)
                verses_content = chapter_content_match.group(2).strip()
                plain_text = chapter_title + verses_content
                print(f"Extracted content with title: {chapter_title.strip()}")
            else:
                # Fallback to find any chapter heading
                fallback_match = re.search(r'(## [A-Za-z ]+ \d+\n)([\s\S]*)', plain_text)
                if fallback_match:
                    chapter_title = fallback_match.group(1)
                    verses_content = fallback_match.group(2).strip()
                    plain_text = chapter_title + verses_content
                    print(f"Used fallback extraction with title: {chapter_title.strip()}")
            
            # Use the already defined template
            full_text = template + plain_text
        else:
            # For other websites, add metadata after the template
            meta_content = ""
            try:
                meta_content += f"URL: {current_url}\n"
                meta_content += f"Title: {browser.title}\n"
            except:
                pass
            
            try:
                # Look for publication date
                date_selectors = [
                    'time', 
                    '.date', 
                    '.published', 
                    '.pub-date', 
                    'meta[property="article:published_time"]',
                    '.timestamp',
                    '.article-timestamp',
                    '.byline-timestamp'
                ]
                
                for selector in date_selectors:
                    date_elem = BeautifulSoup(html, "html.parser").select_one(selector)
                    if date_elem:
                        if date_elem.name == 'meta':
                            date_text = date_elem.get('content', '')
                        else:
                            date_text = date_elem.get_text().strip()
                        
                        if date_text:
                            meta_content += f"Published: {date_text}\n"
                            break
            except:
                pass
            
            if meta_content:
                meta_content += "\n"
                
            # Add the metadata after the template and before the content
            full_text = template + meta_content + plain_text
        
        # Copy to clipboard
        pyperclip.copy(full_text)
        
        print("\n✓ Content extracted and copied to clipboard!")
        return True
        
    except Exception as e:
        print(f"Error grabbing content: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'browser' in locals() and browser:
            browser.quit()

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("INSTRUCTIONS:")
    print("Before using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS, run:")
    print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print("\nNavigate to the page you want to grab, then run this script.")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Show instructions
    show_instructions()
    
    # Ask if user is ready
    proceed = input("Have you already started Chrome with debugging enabled? (y/n): ")
    if proceed.lower() != 'y':
        print("Please start Chrome with debugging enabled first.")
    else:
        # Try to grab the content
        success = grab_active_window_to_clipboard()
        
        if success:
            print("\nOperation completed successfully!")
            print("The content has been copied to your clipboard.")
        else:
            print("\nFailed to grab content.")
