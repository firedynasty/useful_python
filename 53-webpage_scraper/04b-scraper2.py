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

def grab_active_window_to_clipboard():
    """
    Grab text content from the currently open Chrome tab and copy to clipboard
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
        
        # Add summary request and page metadata at the top
        meta_content = f"summarize this scraped data from a website page\n\nURL: {current_url}\n"
        try:
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
        
        meta_content += "\n" + "="*50 + "\n\n"
        
        # Get plain text and add metadata
        plain_text = html_to_plain_text(main_content)
        full_text = meta_content + plain_text
        
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
