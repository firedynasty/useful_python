# This new code is an expanded version of the previous script that adds multi-tab functionality. While both scripts extract content from Chrome browser tabs, this enhanced version provides significantly more options and capabilities.
# Key Differences

# Multi-Tab Support: Unlike the previous script that could only extract content from the active tab, this version can:

# Process only the active tab
# Process specific tabs by their index
# Process all open tabs at once


# New Functions:

# process_tab_content(): Processes a specific tab's content (replacing grab_active_window_to_clipboard())
# grab_all_tabs_content(): Main function to extract content from multiple tabs
# save_contents_to_files(): Saves extracted content to text files
# copy_to_clipboard(): Dedicated function for clipboard operations
# main(): Interactive CLI interface with multiple options


# Output Options:

# Save extracted content to individual text files
# Copy content to clipboard
# Or do both simultaneously


# User Interface:

# Interactive command-line menu
# Allows selection of which tabs to process
# Offers choice of output methods
# Option to use custom template text



# Workflow of the New Script

# User starts Chrome with remote debugging enabled
# User runs the script, which presents an interactive menu
# User selects which tabs to process:

# Active tab only
# Specific tabs by number
# All open tabs


# User chooses the output method:

# Save to text files
# Copy to clipboard
# Both


# User can optionally specify a custom template
# The script processes the selected tabs and handles the output according to user choices

# In Summary
# The previous script was focused on extracting content from the active Chrome tab and copying it to the clipboard. This new version is a significant upgrade that provides batch processing capabilities and more output options while maintaining the same core content extraction functionality.
# This makes it much more useful for research, data collection, and analysis tasks where you might have multiple tabs open with relevant content. For example, a user could open several news articles, research papers, or documentation pages and extract all their contents at once for further processing.


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

def process_tab_content(browser, tab_handle, template_text=None):
    """
    Process the content of a specific Chrome tab
    
    Args:
        browser: Selenium webdriver instance
        tab_handle: Handle of the specific tab to process
        template_text: Optional template to use
        
    Returns:
        tuple: (tab_title, processed_content)
    """
    # Switch to the specified tab
    browser.switch_to.window(tab_handle)
    
    current_url = browser.current_url
    tab_title = browser.title
    print(f"Processing tab: {tab_title}")
    print(f"URL: {current_url}")
    
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
    
    return tab_title, full_text

def grab_all_tabs_content(template_text=None, tab_indices=None, active_tab_only=False):
    """
    Grab text content from multiple Chrome tabs
    
    Args:
        template_text (str, optional): Custom template text to prepend to content.
        tab_indices (list, optional): List of specific tab indices to grab (0-based)
        active_tab_only (bool): If True, only grab from the active tab
    
    Returns:
        dict: Dictionary with tab titles as keys and their content as values
    """
    try:
        print("Connecting to existing Chrome instance...")
        browser = connect_to_existing_chrome()
        
        if not browser:
            print("Failed to connect to Chrome. Make sure it's running with remote debugging enabled.")
            return {}
        
        # Get all window handles (tabs)
        all_handles = browser.window_handles
        
        # Determine which tabs to process
        if active_tab_only:
            # Get the current active tab's handle
            current_handle = browser.current_window_handle
            handles_to_process = [current_handle]
            print(f"Processing active tab only (1 of {len(all_handles)} tabs)")
        elif tab_indices is not None:
            # Process only the specified tab indices
            handles_to_process = [all_handles[i] for i in tab_indices if 0 <= i < len(all_handles)]
            print(f"Processing {len(handles_to_process)} specific tabs out of {len(all_handles)}")
        else:
            # Process all tabs
            handles_to_process = all_handles
            print(f"Processing all {len(handles_to_process)} tabs")
        
        # Dictionary to store contents of each tab
        tab_contents = {}
        
        # Process each tab
        for i, handle in enumerate(handles_to_process):
            print(f"\nProcessing tab {i+1} of {len(handles_to_process)}")
            tab_title, content = process_tab_content(browser, handle, template_text)
            tab_contents[tab_title] = content
        
        return tab_contents
        
    except Exception as e:
        print(f"Error grabbing content: {e}")
        import traceback
        traceback.print_exc()
        return {}
    finally:
        if 'browser' in locals() and browser:
            browser.quit()

def save_contents_to_files(tab_contents, output_dir="tab_contents"):
    """Save tab contents to individual text files"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for tab_title, content in tab_contents.items():
        # Create a safe filename from the tab title
        safe_filename = re.sub(r'[^\w\s-]', '', tab_title).strip().replace(' ', '_')
        if not safe_filename:
            safe_filename = f"tab_{hash(tab_title) % 10000}"
            
        filepath = os.path.join(output_dir, f"{safe_filename}.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved content to: {filepath}")

def copy_to_clipboard(text):
    """Copy text to clipboard"""
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("INSTRUCTIONS:")
    print("Before using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS, run:")
    print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print("\nNavigate to the page you want to grab, then run this script.")
    print("="*80 + "\n")

def main():
    # Show instructions
    show_instructions()
    
    # Ask if user is ready
    proceed = input("Have you already started Chrome with debugging enabled? (y/n): ")
    if proceed.lower() != 'y':
        print("Please start Chrome with debugging enabled first.")
        return
    
    # Options for which tabs to grab
    print("\nChoose an option:")
    print("1. Grab active tab only")
    print("2. Grab specific tabs (by number)")
    print("3. Grab all open tabs")
    
    choice = input("Enter your choice (1-3): ")
    
    active_tab_only = False
    tab_indices = None
    
    if choice == '1':
        active_tab_only = True
    elif choice == '2':
        indices_input = input("Enter tab numbers separated by commas (starting from 1): ")
        try:
            # Convert from 1-based to 0-based indices
            tab_indices = [int(idx.strip()) - 1 for idx in indices_input.split(',')]
        except ValueError:
            print("Invalid input. Using all tabs.")
            tab_indices = None
    
    # What to do with the results
    print("\nWhat would you like to do with the results?")
    print("1. Save to individual text files")
    print("2. Copy active tab to clipboard")
    print("3. Both save files and copy active tab")
    
    output_choice = input("Enter your choice (1-3): ")
    
    # Custom template
    use_custom_template = input("\nUse custom template instead of default? (y/n): ")
    template_text = None
    if use_custom_template.lower() == 'y':
        template_text = input("Enter your template text: ")
    
    # Grab the content
    tab_contents = grab_all_tabs_content(
        template_text=template_text,
        tab_indices=tab_indices,
        active_tab_only=active_tab_only
    )
    
    if not tab_contents:
        print("No content was grabbed.")
        return
    
    # Handle the output based on user choice
    if output_choice in ('1', '3'):
        save_contents_to_files(tab_contents)
    
    if output_choice in ('2', '3') and active_tab_only:
        # There should be only one entry in the dictionary
        content = list(tab_contents.values())[0]
        if copy_to_clipboard(content):
            print("\n✓ Active tab content copied to clipboard!")
    
    print("\nOperation completed successfully!")

if __name__ == "__main__":
    main()
