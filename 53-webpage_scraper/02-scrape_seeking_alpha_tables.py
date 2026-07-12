import os
import time
import subprocess
import re
import csv
import socket
import pandas as pd
import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def check_chrome_running():
    """Check if Chrome is running with remote debugging enabled"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Try to connect to the debug port
        s.connect(('127.0.0.1', 9222))
        s.close()
        return True
    except:
        s.close()
        return False

def connect_to_existing_chrome():
    """Connect to an already running Chrome instance with remote debugging"""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    # Check if Chrome is running with remote debugging port
    if not check_chrome_running():
        print("\n✗ ERROR: Could not detect Chrome running with remote debugging.")
        print("  Please make sure to start Chrome with the --remote-debugging-port=9222 flag.")
        print("\nOn macOS, run:")
        print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        print("\nOn Windows, run:")
        print("  \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
        print("\nOn Linux, run:")
        print("  google-chrome --remote-debugging-port=9222")
        return None
    
    try:
        # Use webdriver-manager to handle ChromeDriver versioning automatically
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

def extract_financial_table(html):
    """Extract financial table data from HTML using BeautifulSoup"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Look for the financial table - adjust these selectors as needed based on the site structure
    table = soup.find('table', {'data-test-id': 'table'})
    
    if not table:
        print("Could not find financial table")
        return None
    
    # Extract headers
    headers = []
    header_row = table.find('thead').find('tr')
    
    # Extract the row label header (typically empty or contains "Metrics")
    first_header = header_row.find('th', {'data-test-id': 'date-header'})
    headers.append(first_header.get_text(strip=True) if first_header else "Metrics")
    
    # Extract period headers
    for header in header_row.find_all('th')[1:]:  # Skip the first header which is typically empty
        header_text = header.get_text(strip=True)
        if not header_text and header.find('div', {'class': 'u0E03'}):
            header_text = header.find('div', {'class': 'u0E03'}).get_text(strip=True)
        headers.append(header_text)
    
    # Extract rows
    rows = []
    for row in table.find('tbody').find_all('tr'):
        row_data = []
        
        # Get the row label
        label = row.find('th').get_text(strip=True)
        row_data.append(label)
        
        # Get the values
        for cell in row.find_all('td'):
            # Extract the value, removing any non-numeric characters except for decimal points and minus signs
            value = cell.get_text(strip=True)
            # If there's a mini chart, skip it or handle specially
            if cell.find('span', {'data-test-id': 'mini-chart-placeholder'}):
                # Skip the chart data or handle it specially
                pass
            row_data.append(value)
        
        rows.append(row_data)
    
    # Create a DataFrame
    df = pd.DataFrame(rows, columns=headers)
    
    return df

def save_to_csv(df, output_file='financial_table.csv'):
    """Save DataFrame to CSV file"""
    if df is not None:
        df.to_csv(output_file, index=False)
        print(f"Successfully saved data to {output_file}")
        return True
    return False

def extract_table_to_csv(output_file='financial_table.csv'):
    """Extract financial table from the current page and save to CSV"""
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
        
        # Extract the financial table
        df = extract_financial_table(html)
        
        if df is not None:
            # Generate filename if not provided
            if output_file == 'financial_table.csv':
                # Extract symbol from URL if possible
                symbol_match = re.search(r'/symbol/([^/]+)', current_url)
                if symbol_match:
                    symbol = symbol_match.group(1)
                    # Determine the table type
                    if 'income-statement' in current_url:
                        table_type = 'income_statement'
                    elif 'balance-sheet' in current_url:
                        table_type = 'balance_sheet'
                    elif 'cash-flow' in current_url:
                        table_type = 'cash_flow'
                    else:
                        table_type = 'financials'
                    
                    output_file = f"{symbol}_{table_type}.csv"
            
            # Save to CSV
            return save_to_csv(df, output_file)
        else:
            print("Failed to extract financial table.")
            return False
            
    except Exception as e:
        print(f"Error extracting table: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'browser' in locals() and browser:
            pass  # Don't quit the browser since it was started externally

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("SEEKING ALPHA FINANCIAL TABLE SCRAPER")
    print("="*80)
    print("\nThis script extracts financial tables from Seeking Alpha using Chrome with remote debugging.")
    print("\nBefore using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS, run:")
    print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print("\nOn Windows, run:")
    print("  \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    print("\nOn Linux, run:")
    print("  google-chrome --remote-debugging-port=9222")
    print("\nThen navigate to the financial table page you want to extract")
    print("(e.g., income statement, balance sheet, cash flow)")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Show instructions
    show_instructions()
    
    # Check if Chrome is already running with remote debugging
    if check_chrome_running():
        print("✓ Detected Chrome running with remote debugging enabled!")
    else:
        print("✗ Chrome with remote debugging not detected.")
        print("  Please start Chrome with --remote-debugging-port=9222")
        
        # Ask if user wants to start Chrome automatically
        start_chrome = input("\nWould you like to start Chrome with remote debugging now? (y/n): ")
        if start_chrome.lower() == 'y':
            try:
                if platform.system() == 'Darwin':  # macOS
                    print("\nStarting Chrome with remote debugging on macOS...")
                    subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
                                     '--remote-debugging-port=9222'])
                elif platform.system() == 'Windows':
                    print("\nStarting Chrome with remote debugging on Windows...")
                    subprocess.Popen(['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', 
                                     '--remote-debugging-port=9222'])
                else:  # Linux
                    print("\nStarting Chrome with remote debugging on Linux...")
                    subprocess.Popen(['google-chrome', '--remote-debugging-port=9222'])
                
                print("Chrome has been started. Please navigate to the financial table page.")
                time.sleep(3)  # Give Chrome time to start
            except Exception as e:
                print(f"Error starting Chrome: {e}")
                print("Please start Chrome manually with the remote debugging flag.")
        else:
            print("\nPlease start Chrome with remote debugging and try again.")
            exit()
    
    # Wait for user to navigate to the correct page
    proceed = input("\nHave you navigated to the financial table page? (y/n): ")
    if proceed.lower() != 'y':
        print("Please navigate to the financial table page and run this script again.")
        exit()
    
    # Ask for output filename or use default
    output_file = input("Enter output filename (or press Enter to auto-generate): ").strip()
    if not output_file:
        output_file = 'financial_table.csv'
    
    # Try to extract the table
    success = extract_table_to_csv(output_file)
    
    if success:
        # Re-determine the actual filename that was used
        if output_file == 'financial_table.csv':
            # If auto-generated, we need to figure out what name was actually used
            browser = connect_to_existing_chrome()
            if browser:
                current_url = browser.current_url
                symbol_match = re.search(r'/symbol/([^/]+)', current_url)
                if symbol_match:
                    symbol = symbol_match.group(1)
                    if 'income-statement' in current_url:
                        table_type = 'income_statement'
                    elif 'balance-sheet' in current_url:
                        table_type = 'balance_sheet'
                    elif 'cash-flow' in current_url:
                        table_type = 'cash_flow'
                    else:
                        table_type = 'financials'
                    
                    # This is the actual filename that was generated
                    final_filename = f"{symbol}_{table_type}.csv"
                    print("\n✓ Operation completed successfully!")
                    print(f"  The financial table has been saved to {final_filename}")
                else:
                    print("\n✓ Operation completed successfully!")
                    print(f"  The financial table has been saved to {output_file}")
            else:
                print("\n✓ Operation completed successfully!")
                print(f"  The financial table has been saved to {output_file}")
        else:
            print("\n✓ Operation completed successfully!")
            print(f"  The financial table has been saved to {output_file}")
    else:
        print("\n✗ Failed to extract table.")
        print("  Check the error messages above for troubleshooting.")