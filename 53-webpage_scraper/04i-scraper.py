import os
import time
import subprocess
import re
import platform
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import html2text

def connect_to_existing_chrome():
    """Connect to an already running Chrome instance with remote debugging"""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        # For Chrome version 115 and newer, we need to explicitly use the Selenium Manager
        # This ensures we get the correct ChromeDriver version
        print("Setting up ChromeDriver using webdriver-manager...")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        print("Successfully connected to Chrome!")
        return driver
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure Chrome is running with --remote-debugging-port=9222")
        print("2. Ensure the Chrome instance is accessible at 127.0.0.1:9222")
        print("3. Try closing and restarting Chrome with the debugging flag")
        print("4. If using a non-standard Chrome installation, specify its path to ChromeDriverManager")
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

def create_safe_filename(title, url):
    """Create a safe filename from the page title and URL"""
    # First try to use the title
    if title:
        # Remove invalid characters and limit length
        safe_name = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        # Truncate if too long
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        
        if safe_name:
            return safe_name
    
    # If title doesn't work, use the domain from the URL
    try:
        domain = re.search(r'https?://(?:www\.)?([^/]+)', url).group(1)
        domain = re.sub(r'[^\w\s-]', '', domain).strip().replace(' ', '_')
        return domain
    except:
        # Last resort: timestamp
        return f"scraped_content_{int(time.time())}"

def display_file_content(filepath):
    """Display the content of the saved file"""
    try:
        print("\n" + "="*80)
        print(f"CONTENT OF SAVED FILE: {os.path.basename(filepath)}")
        print("="*80)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        
        print("="*80)
        print(f"END OF FILE: {os.path.basename(filepath)}")
        print("="*80)
        
    except Exception as e:
        print(f"Error reading file content: {e}")

def copy_to_clipboard(content):
    """Copy content to clipboard (macOS)"""
    try:
        subprocess.run(['pbcopy'], input=content.encode(), check=True)
        print("✓ Content also copied to clipboard!")
        return True
    except Exception as e:
        print(f"Could not copy to clipboard: {e}")
        return False

def grab_active_window_to_file(template_text=None, copy_to_clipboard_flag=False):
    """
    Grab text content from the currently open Chrome tab and save to a file
    
    Args:
        template_text (str, optional): Custom template text to prepend to content.
                                      If None, default templates will be used based on content type.
        copy_to_clipboard_flag (bool): Whether to also copy content to clipboard
    
    Returns:
        tuple: (success, filepath) where success is a boolean and filepath is the path to the saved file
    """
    try:
        print("Connecting to existing Chrome instance...")
        browser = connect_to_existing_chrome()
        
        if not browser:
            print("Failed to connect to Chrome. Make sure it's running with remote debugging enabled.")
            return False, None
        
        # Get all tabs and switch to tab 1 (first tab)
        all_tabs = browser.window_handles
        print(f"Found {len(all_tabs)} tabs")
        
        if len(all_tabs) >= 1:
            print("Switching to tab 1 (first tab)...")
            browser.switch_to.window(all_tabs[0])  # Index 0 = first tab
        else:
            print("No tabs found!")
            return False, None
        
        print("Getting content from tab 1...")
        current_url = browser.current_url
        tab_title = browser.title
        print(f"Current URL: {current_url}")
        print(f"Title: {tab_title}")
        
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
                meta_content += f"Title: {tab_title}\n"
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
        
        # Save to file in the specified directory
        output_dir = "./scraped_from_websites"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        
        # Create a safe filename from the title
        safe_filename = create_safe_filename(tab_title, current_url)
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"{safe_filename}_{timestamp}.txt")
        
        # Write the content to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"\n✓ Content extracted and saved to: {filepath}")
        
        # Copy to clipboard if requested
        if copy_to_clipboard_flag:
            copy_to_clipboard(full_text)
        
        # Display the file content
        display_file_content(filepath)
        
        return True, filepath
        
    except Exception as e:
        print(f"Error grabbing content: {e}")
        import traceback
        traceback.print_exc()
        return False, None
    finally:
        if 'browser' in locals() and browser:
            browser.quit()

def check_chrome_running():
    """Check if Chrome is running with remote debugging enabled"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Try to connect to the debug port
        s.connect(('127.0.0.1', 9222))
        s.close()
        return True
    except:
        s.close()
        return False

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("INSTRUCTIONS:")
    print("Before using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS, run:")
    print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile")
    print("\nNavigate to the page you want to grab, then run this script.")
    
    # Check if Chrome is already running with debugging
    if check_chrome_running():
        print("\n✓ DETECTED: Chrome appears to be running with remote debugging enabled.")
    else:
        print("\n✗ WARNING: Could not detect Chrome running with remote debugging.")
        print("  Please make sure to start Chrome with the --remote-debugging-port=9222 flag.")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    # Show instructions
    show_instructions()
    
    if not check_chrome_running():
        print("Chrome does not appear to be running with the debug port open.")
        print("Please start Chrome using the command:")
        print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile")
        
        proceed = input("Try to continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting. Please restart Chrome with debugging enabled.")
            exit(1)
    
    # Custom template
    use_custom_template = input("\nUse custom template instead of default? (y/n): ")
    template_text = None
    if use_custom_template.lower() == 'y':
        template_text = input("Enter your template text: ")
    
    # Ask about clipboard
    copy_to_clipboard_flag = input("Also copy content to clipboard? (y/n): ").lower() == 'y'
    
    print("\nAttempting to connect to Chrome and extract content...")
    # Try to grab the content
    success, filepath = grab_active_window_to_file(template_text, copy_to_clipboard_flag)
    
    if success:
        print("\nOperation completed successfully!")
        print(f"The content has been saved to: {filepath}")
        if copy_to_clipboard_flag:
            print("Content is also available in your clipboard.")
    else:
        print("\nFailed to save content.")
        print("\nTroubleshooting suggestions:")
        print("1. Make sure Chrome is running with --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile")
        print("2. Try closing all Chrome windows and starting fresh")
        print("3. Check if any Chrome extensions might be interfering")
        print("4. If using Python version control (conda/venv), ensure all dependencies are installed in your active environment")
