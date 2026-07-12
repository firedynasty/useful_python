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
        return None

def extract_business_insider_content(html):
    """Extract main content from Business Insider HTML with specific cleanup rules"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Business Insider specific content selectors (in order of preference)
    bi_content_selectors = [
        "section#post-body .post-body-content",
        "#post-body .post-body-content", 
        ".post-body-content.post-story-body-content",
        "section#post-body",
        "#post-body"
    ]
    
    main_content = None
    
    # Try Business Insider specific selectors first
    for selector in bi_content_selectors:
        content = soup.select_one(selector)
        if content and len(content.get_text(strip=True)) > 200:
            print(f"Found BI content using selector: {selector}")
            main_content = content
            break
    
    # If no specific BI content found, fall back to general selectors
    if not main_content:
        print("BI selectors failed, trying general article selectors...")
        general_selectors = [
            "article", 
            ".article-content", 
            ".article__body", 
            ".story-body",
            ".main-content"
        ]
        
        for selector in general_selectors:
            content = soup.select_one(selector)
            if content and len(content.get_text(strip=True)) > 200:
                print(f"Found content using general selector: {selector}")
                main_content = content
                break
    
    # Last resort: use body
    if not main_content:
        print("Using body as fallback")
        main_content = soup.body
    
    if main_content:
        # Business Insider specific cleanup
        cleanup_business_insider_elements(main_content)
        
        # General cleanup
        cleanup_general_elements(main_content)
    
    return main_content

def cleanup_business_insider_elements(content):
    """Remove Business Insider specific unwanted elements"""
    
    # BI-specific ad and tracking elements
    bi_unwanted_selectors = [
        # Ad containers
        '[data-bi-ad]',
        '.ad-wrapper',
        '.ad-callout-wrapper', 
        '.in-post-sticky',
        '.ntv-moap',
        '[id^="gpt-post-"]',
        '.masthead-ad',
        
        # Taboola recommendations
        '[id^="taboola-"]',
        '.vendor-taboola',
        '.taboola-feed',
        '[data-ntv-id]',
        
        # Social and sharing elements
        '.social-share',
        '.share-button',
        '.newsletter-signup',
        '.subscription-banner',
        
        # Navigation and structure
        'header.masthead',
        '.masthead',
        '.logo-link',
        '.grid-lines',
        
        # Tracking elements
        '[data-track-click]',
        '[data-track-module]',
        '[data-analytics-module]'
    ]
    
    print("Removing Business Insider specific elements...")
    removed_count = 0
    
    for selector in bi_unwanted_selectors:
        elements = content.select(selector)
        for element in elements:
            element.decompose()
            removed_count += 1
    
    # Remove elements by text content patterns
    text_patterns_to_remove = [
        r'Read the original article on Business Insider',
        r'Subscribe to Business Insider',
        r'Get the inside scoop on what traders are talking about',
        r'Sign up for notifications from Insider',
        r'More: Microsoft OpenAI',
        r'NOW WATCH:',
        r'Read next'
    ]
    
    # Find and remove elements containing these patterns
    for pattern in text_patterns_to_remove:
        for element in content.find_all(text=re.compile(pattern, re.IGNORECASE)):
            if element.parent:
                element.parent.decompose()
                removed_count += 1
    
    print(f"Removed {removed_count} BI-specific unwanted elements")

def cleanup_general_elements(content):
    """Remove general unwanted elements"""
    
    general_unwanted_elements = [
        'script', 'style', 'iframe', 'noscript', 'nav', 'footer',
        'aside', 'figure.advertisement', '.ad', '.advertisement',
        '.related-articles', '.recommended-articles'
    ]
    
    removed_count = 0
    for element_type in general_unwanted_elements:
        elements = content.find_all(element_type) if isinstance(element_type, str) and not element_type.startswith('.') else content.select(element_type)
        for element in elements:
            element.decompose()
            removed_count += 1
    
    print(f"Removed {removed_count} general unwanted elements")

def extract_business_insider_metadata(html):
    """Extract Business Insider specific metadata"""
    soup = BeautifulSoup(html, "html.parser")
    metadata = {}
    
    # Extract title
    title_elem = soup.select_one('h1.headline.heading-xl')
    if title_elem:
        metadata['title'] = title_elem.get_text().strip()
    else:
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
    
    # Extract author from meta tag
    author_meta = soup.find('meta', {'property': 'author'})
    if author_meta:
        metadata['author'] = author_meta.get('content', '')
    
    # Extract dates
    date_published = soup.find('meta', {'name': 'datePublished'})
    if date_published:
        metadata['published'] = date_published.get('content', '')
    
    date_modified = soup.find('meta', {'name': 'dateModified'})
    if date_modified:
        metadata['modified'] = date_modified.get('content', '')
    
    # Extract description
    desc_meta = soup.find('meta', {'name': 'description'})
    if desc_meta:
        metadata['description'] = desc_meta.get('content', '')
    
    # Check for exclusive badge
    exclusive_badge = soup.select_one('.post-overline-stamp.as-exclusive')
    if exclusive_badge:
        metadata['exclusive'] = True
    
    return metadata

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
        
        # Business Insider specific cleanup patterns
        bi_cleanup_patterns = [
            # Remove common BI footer text
            r'Read the original article on Business Insider.*?\n',
            r'Get the inside scoop on what traders are talking about.*?\n',
            r'Subscribe to Business Insider.*?\n',
            r'Sign up for notifications from Insider.*?\n',
            r'NOW WATCH:.*?\n',
            r'More:.*?\n',
            r'Read next.*?\n',
            # Remove advertisement markers
            r'\[Advertisement\].*?\n',
            r'\*\*Advertisement\*\*.*?\n',
        ]
        
        for pattern in bi_cleanup_patterns:
            plain_text = re.sub(pattern, '', plain_text, flags=re.IGNORECASE | re.DOTALL)
        
        # General cleanup
        plain_text = re.sub(r'\n\s*\n', '\n\n', plain_text)  # Remove multiple blank lines
        plain_text = re.sub(r'\*\*', '', plain_text)  # Remove bold markers
        plain_text = re.sub(r'__', '', plain_text)    # Remove alternate bold markers
        
        return plain_text
    except Exception as e:
        print(f"Error converting to plain text: {e}")
        return ""

def create_safe_filename(title, url):
    """Create a safe filename from the page title and URL"""
    if title:
        # Remove "- Business Insider" suffix if present
        title = re.sub(r'\s*-\s*Business Insider\s*$', '', title, flags=re.IGNORECASE)
        # Remove invalid characters and limit length
        safe_name = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        # Truncate if too long
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        
        if safe_name:
            return safe_name
    
    # If title doesn't work, use domain
    try:
        domain = re.search(r'https?://(?:www\.)?([^/]+)', url).group(1)
        domain = re.sub(r'[^\w\s-]', '', domain).strip().replace(' ', '_')
        return domain
    except:
        return f"business_insider_{int(time.time())}"

def grab_business_insider_content(template_text=None, copy_to_clipboard_flag=False):
    """
    Grab text content from Business Insider with specialized cleanup and save to file
    
    Args:
        template_text (str, optional): Custom template text to prepend to content
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
        
        print("Getting current page content...")
        current_url = browser.current_url
        
        # Verify it's a Business Insider URL
        if "businessinsider.com" not in current_url:
            print(f"Warning: This doesn't appear to be a Business Insider URL: {current_url}")
            print("This scraper is optimized for Business Insider articles.")
            proceed = input("Continue anyway? (y/n): ")
            if proceed.lower() != 'y':
                return False, None
        
        print(f"Current URL: {current_url}")
        
        # Get the page HTML
        html = browser.page_source
        
        # Extract Business Insider metadata
        metadata = extract_business_insider_metadata(html)
        print(f"Article title: {metadata.get('title', 'Unknown')}")
        print(f"Author: {metadata.get('author', 'Unknown')}")
        if metadata.get('exclusive'):
            print("📰 EXCLUSIVE article detected")
        
        # Process the content with BI-specific extraction
        main_content = extract_business_insider_content(html)
        if not main_content:
            print("Warning: Could not extract specific content, using full page.")
            main_content = html
        
        # Get plain text with BI-specific cleanup
        plain_text = html_to_plain_text(main_content)
        
        # Create enhanced metadata section
        meta_content = ""
        if metadata.get('title'):
            meta_content += f"Title: {metadata['title']}\n"
        meta_content += f"URL: {current_url}\n"
        if metadata.get('author'):
            meta_content += f"Author: {metadata['author']}\n"
        if metadata.get('published'):
            # Format the ISO date to be more readable
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(metadata['published'].replace('Z', '+00:00'))
                formatted_date = dt.strftime('%B %d, %Y at %I:%M %p UTC')
                meta_content += f"Published: {formatted_date}\n"
            except:
                meta_content += f"Published: {metadata['published']}\n"
        if metadata.get('exclusive'):
            meta_content += "Type: EXCLUSIVE\n"
        if metadata.get('description'):
            meta_content += f"Description: {metadata['description']}\n"
        
        meta_content += "\n" + "="*50 + "\n\n"
        
        # Use template
        default_template = "summarize this Business Insider article:\n\n"
        template = template_text if template_text is not None else default_template
        
        # Create full text
        full_text = template + meta_content + plain_text
        
        # Save to file
        output_dir = "./scraped_from_websites"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        
        # Create filename
        safe_filename = create_safe_filename(metadata.get('title'), current_url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"BI_{safe_filename}_{timestamp}.txt")
        
        # Write content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"\n✓ Business Insider content extracted and saved to: {filepath}")
        
        # Copy to clipboard if requested
        if copy_to_clipboard_flag:
            try:
                subprocess.run(['pbcopy'], input=full_text.encode(), check=True)
                print("✓ Content also copied to clipboard!")
            except Exception as e:
                print(f"Could not copy to clipboard: {e}")
        
        # Display preview
        print("\n" + "="*80)
        print("CONTENT PREVIEW:")
        print("="*80)
        preview_text = full_text[:500] + "..." if len(full_text) > 500 else full_text
        print(preview_text)
        print("="*80)
        
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
        s.connect(('127.0.0.1', 9222))
        s.close()
        return True
    except:
        s.close()
        return False

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("BUSINESS INSIDER SPECIALIZED SCRAPER")
    print("="*80)
    print("This scraper is optimized for Business Insider articles.")
    print("It automatically removes ads, navigation, related articles, and other clutter.")
    print("\nBefore using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS, run:")
    print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile")
    print("\nNavigate to a Business Insider article, then run this script.")
    
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
        print("Please start Chrome using the command shown above.")
        
        proceed = input("Try to continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting. Please restart Chrome with debugging enabled.")
            exit(1)
    
    # Custom template
    use_custom_template = input("\nUse custom template instead of default Business Insider template? (y/n): ")
    template_text = None
    if use_custom_template.lower() == 'y':
        template_text = input("Enter your template text: ")
    
    # Ask about clipboard
    copy_to_clipboard_flag = input("Also copy content to clipboard? (y/n): ").lower() == 'y'
    
    print("\nAttempting to connect to Chrome and extract Business Insider content...")
    
    # Extract content
    success, filepath = grab_business_insider_content(template_text, copy_to_clipboard_flag)
    
    if success:
        print("\n🎉 Operation completed successfully!")
        print(f"Business Insider content has been cleaned and saved to: {filepath}")
        if copy_to_clipboard_flag:
            print("Content is also available in your clipboard.")
        print("\nThe scraper removed:")
        print("  ✓ Advertisement containers and tracking elements")
        print("  ✓ Taboola recommendations and related articles")
        print("  ✓ Navigation menus and social sharing buttons")
        print("  ✓ Newsletter signups and subscription banners")
        print("  ✓ 'Read the original article' footers")
    else:
        print("\n❌ Failed to extract Business Insider content.")
        print("\nTroubleshooting suggestions:")
        print("1. Make sure you're on a Business Insider article page")
        print("2. Ensure Chrome is running with --remote-debugging-port=9222")
        print("3. Try refreshing the page and running the scraper again")
        print("4. Check if any Chrome extensions might be interfering")