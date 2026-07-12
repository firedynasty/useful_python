import os
import time
import re
import pyperclip  # For clipboard operations
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import html2text
import json

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

def extract_twitter_content(browser, url):
    """Extract tweet and comments from a Twitter/X page"""
    print(f"Extracting content from: {url}")
    
    try:
        # Wait for the tweet content to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        )
        
        # First, get the main tweet
        main_tweet = None
        try:
            articles = browser.find_elements(By.CSS_SELECTOR, "article")
            if articles:
                main_tweet = articles[0]
        except Exception as e:
            print(f"Error finding main tweet: {e}")
        
        tweet_data = []
        
        # Extract the main tweet content
        if main_tweet:
            tweet_text_elem = main_tweet.find_elements(By.CSS_SELECTOR, "[data-testid='tweetText']")
            tweet_text = tweet_text_elem[0].text if tweet_text_elem else "No tweet text found"
            
            author_elem = main_tweet.find_elements(By.CSS_SELECTOR, "[data-testid='User-Name']")
            author = author_elem[0].text if author_elem else "Unknown author"
            
            time_elem = main_tweet.find_elements(By.TAG_NAME, "time")
            timestamp = time_elem[0].get_attribute("datetime") if time_elem else "Unknown time"
            
            tweet_data.append({
                "type": "main_tweet",
                "author": author,
                "text": tweet_text,
                "timestamp": timestamp
            })
        
        # Scroll down to load more replies
        print("Loading comments...")
        for _ in range(5):  # Scroll a few times to load more comments
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
        
        # Now extract all comments/replies
        comment_articles = browser.find_elements(By.CSS_SELECTOR, "article")
        
        # Skip the first one (main tweet) if it exists
        comment_articles = comment_articles[1:] if main_tweet else comment_articles
        
        for idx, article in enumerate(comment_articles):
            try:
                # Extract comment text
                comment_text_elem = article.find_elements(By.CSS_SELECTOR, "[data-testid='tweetText']")
                comment_text = comment_text_elem[0].text if comment_text_elem else "No comment text found"
                
                # Extract commenter info
                author_elem = article.find_elements(By.CSS_SELECTOR, "[data-testid='User-Name']")
                author = author_elem[0].text if author_elem else "Unknown commenter"
                
                # Extract timestamp if available
                time_elem = article.find_elements(By.TAG_NAME, "time")
                timestamp = time_elem[0].get_attribute("datetime") if time_elem else "Unknown time"
                
                tweet_data.append({
                    "type": "comment",
                    "author": author,
                    "text": comment_text,
                    "timestamp": timestamp
                })
            except Exception as e:
                print(f"Error processing comment {idx}: {e}")
        
        print(f"Found {len(tweet_data)-1} comments")
        return tweet_data
    
    except Exception as e:
        print(f"Error extracting Twitter content: {e}")
        import traceback
        traceback.print_exc()
        return []

def format_tweet_data(tweet_data):
    """Format the tweet data into a readable text format"""
    if not tweet_data:
        return "No tweet data found"
    
    formatted_text = ""
    
    # Add the main tweet first
    main_tweets = [t for t in tweet_data if t["type"] == "main_tweet"]
    if main_tweets:
        main_tweet = main_tweets[0]
        formatted_text += f"MAIN TWEET:\n"
        formatted_text += f"Author: {main_tweet['author']}\n"
        formatted_text += f"Time: {main_tweet['timestamp']}\n"
        formatted_text += f"Content: {main_tweet['text']}\n\n"
    
    # Add all comments
    comments = [t for t in tweet_data if t["type"] == "comment"]
    if comments:
        formatted_text += f"COMMENTS ({len(comments)}):\n"
        for idx, comment in enumerate(comments, 1):
            formatted_text += f"------- Comment #{idx} -------\n"
            formatted_text += f"Author: {comment['author']}\n"
            formatted_text += f"Time: {comment['timestamp']}\n"
            formatted_text += f"Content: {comment['text']}\n\n"
    else:
        formatted_text += "No comments found.\n"
    
    return formatted_text

def grab_twitter_comments():
    """Grab comments from the currently open Twitter/X tab and copy to clipboard"""
    try:
        print("Connecting to existing Chrome instance...")
        browser = connect_to_existing_chrome()
        
        if not browser:
            print("Failed to connect to Chrome. Make sure it's running with remote debugging enabled.")
            return False
        
        print("Getting current page content...")
        current_url = browser.current_url
        print(f"Current URL: {current_url}")
        
        # Check if we're on Twitter/X
        if not ("twitter.com" in current_url or "x.com" in current_url):
            print("The current page is not Twitter/X. Please navigate to a Twitter/X page.")
            return False
            
        # Extract tweet and comments
        tweet_data = extract_twitter_content(browser, current_url)
        
        if not tweet_data:
            print("Failed to extract any content from this Twitter/X page.")
            return False
        
        # Format the data for clipboard
        formatted_text = format_tweet_data(tweet_data)
        
        # Copy to clipboard
        pyperclip.copy(formatted_text)
        
        # Also save to file
        filename = f"twitter_scrape_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted_text)
        
        print(f"\n✓ Content extracted and copied to clipboard!")
        print(f"✓ Content also saved to {filename}")
        
        # Save raw data as JSON for further processing if needed
        json_filename = f"twitter_scrape_{int(time.time())}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(tweet_data, f, indent=2)
        
        print(f"✓ Raw data saved to {json_filename}")
        return True
        
    except Exception as e:
        print(f"Error grabbing Twitter content: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'browser' in locals() and browser:
            browser.quit()

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("TWITTER/X SCRAPER INSTRUCTIONS:")
    print("Before using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS, run:")
    print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print("\nOn Windows, run:")
    print("  \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    print("\nOn Linux, run:")
    print("  google-chrome --remote-debugging-port=9222")
    print("\nThen navigate to the Twitter/X tweet you want to scrape comments from.")
    print("Make sure you've scrolled down to load the comments you want to capture.")
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
        success = grab_twitter_comments()
        
        if success:
            print("\nOperation completed successfully!")
            print("The content has been copied to your clipboard.")
        else:
            print("\nFailed to grab Twitter content.")
