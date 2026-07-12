import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

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

def extract_four_factors(url):
    """Extract Four Factors data from a specific box score URL"""
    try:
        print(f"Connecting to Chrome and navigating to {url}...")
        browser = connect_to_existing_chrome()
        
        if not browser:
            print("Failed to connect to Chrome.")
            return None
            
        # Navigate to the box score page
        browser.get(url)
        print(f"Loaded page: {browser.title}")
        
        # Wait for the page to fully load
        time.sleep(2)
        
        # Get the page HTML
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Find the Four Factors table
        four_factors_table = soup.find('table', {'id': 'four_factors'})
        
        if not four_factors_table:
            print("Four Factors table not found")
            return None
            
        print("Found Four Factors table")
        
        # Extract basic game info
        scorebox = soup.find('div', {'class': 'scorebox'})
        teams = scorebox.find_all('div', {'itemprop': 'performer'})
        
        visitor_team = teams[0].find('a').text if len(teams) > 0 else "Visitor"
        home_team = teams[1].find('a').text if len(teams) > 1 else "Home"
        
        scores = scorebox.find_all('div', {'class': 'score'})
        visitor_score = scores[0].text if len(scores) > 0 else ""
        home_score = scores[1].text if len(scores) > 1 else ""
        
        # Get game date
        game_date = ""
        meta = scorebox.find('div', {'class': 'scorebox_meta'})
        if meta:
            date_div = meta.find_all('div')
            if date_div:
                game_date = date_div[0].text
        
        # Create game info dictionary
        game_info = {
            'Date': game_date,
            'Visitor_Team': visitor_team,
            'Home_Team': home_team, 
            'Visitor_Points': visitor_score,
            'Home_Points': home_score,
            'Box_Score_URL': url,
            'Overtime': '',
            'Attendance': '',
            'Arena': ''
        }
        
        # Get Four Factors data
        rows = four_factors_table.find('tbody').find_all('tr')
        
        four_factors_data = []
        
        # Process each row (away team and home team)
        for i, row in enumerate(rows):
            team_name = visitor_team if i == 0 else home_team
            is_home = False if i == 0 else True
            
            team_data = {
                'Game_Date': game_date,
                'Team': team_name,
                'Is_Home_Team': is_home,
                'Opponent': home_team if i == 0 else visitor_team,
                'Team_Score': visitor_score if i == 0 else home_score,
                'Opponent_Score': home_score if i == 0 else visitor_score,
                'Pace': get_cell_value(row, 'pace'),
                'eFG_PCT': get_cell_value(row, 'efg_pct'),
                'TOV_PCT': get_cell_value(row, 'tov_pct'),
                'ORB_PCT': get_cell_value(row, 'orb_pct'),
                'FT_Rate': get_cell_value(row, 'ft_rate'),
                'ORtg': get_cell_value(row, 'off_rtg')
            }
            
            four_factors_data.append(team_data)
        
        return pd.DataFrame(four_factors_data)
        
    except Exception as e:
        print(f"Error extracting Four Factors data: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'browser' in locals() and browser:
            browser.quit()

def get_cell_value(row, stat_name):
    """Helper function to extract cell value by stat name"""
    cell = row.find('td', {'data-stat': stat_name})
    return cell.text.strip() if cell else ""

def main():
    """Main function to scrape Four Factors from a specific box score"""
    print("\n" + "="*80)
    print("NBA FOUR FACTORS EXTRACTOR")
    print("="*80)
    print("This script extracts Four Factors data from a Basketball Reference box score.")
    print("\nBefore using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS/Linux, run:")
    print("  google-chrome --remote-debugging-port=9222")
    print("\nOn Windows, run (adjust path as needed):")
    print("  \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    print("="*80 + "\n")
    
    # Ask if user is ready
    proceed = input("Have you already started Chrome with debugging enabled? (y/n): ")
    if proceed.lower() != 'y':
        print("Please start Chrome with debugging enabled first.")
        return
    
    # Default URL
    default_url = "https://www.basketball-reference.com/boxscores/202503010CHO.html"
    
    # Allow custom URL
    custom_url = input(f"Enter box score URL (or press Enter for default: {default_url}): ")
    if not custom_url.strip():
        url = default_url
    else:
        url = custom_url
        
    # Allow custom output directory
    output_dir = input("Enter output directory (or press Enter for default 'data'): ").strip()
    if not output_dir:
        output_dir = "data"
    
    # Ensure the directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Scrape Four Factors data
    print(f"\nScraping Four Factors from {url}...")
    four_factors_data = extract_four_factors(url)
    
    if four_factors_data is not None and not four_factors_data.empty:
        # Generate filename
        game_parts = url.split('/')[-1].split('.')[0]  # e.g., 202503010CHO
        filename = f"{output_dir}/four_factors_{game_parts}.csv"
        
        # Save to CSV
        four_factors_data.to_csv(filename, index=False)
        print(f"\nScraping completed successfully!")
        print(f"- Four Factors data saved to: {filename}")
        
        # Display the data
        print("\nExtracted Four Factors Data:")
        print(four_factors_data)
    else:
        print("Failed to extract Four Factors data.")

if __name__ == "__main__":
    main()
