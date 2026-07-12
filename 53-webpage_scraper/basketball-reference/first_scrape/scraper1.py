import os
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

def extract_tables_from_url(url):
    """Extract all tables from the given URL"""
    try:
        print(f"Connecting to Chrome and navigating to {url}...")
        browser = connect_to_existing_chrome()
        
        if not browser:
            print("Failed to connect to Chrome.")
            return None
            
        # Navigate to the standings page
        browser.get(url)
        print(f"Loaded page: {browser.title}")
        
        # Wait for the page to fully load
        time.sleep(2)
        
        # Get the page HTML
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Process Eastern Conference table
        east_table = soup.find('table', {'id': 'confs_standings_E'})
        if east_table:
            print("Found Eastern Conference standings table")
            east_df = extract_table_data(east_table, "Eastern Conference")
        else:
            print("Eastern Conference table not found")
            east_df = None
            
        # Process Western Conference table
        west_table = soup.find('table', {'id': 'confs_standings_W'})
        if west_table:
            print("Found Western Conference standings table")
            west_df = extract_table_data(west_table, "Western Conference")
        else:
            print("Western Conference table not found")
            west_df = None
            
        # Process Expanded Standings table
        expanded_table = soup.find('table', {'id': 'expanded_standings'})
        if expanded_table:
            print("Found Expanded standings table")
            expanded_df = extract_expanded_table_data(expanded_table)
        else:
            print("Expanded standings table not found")
            expanded_df = None
            
        return {
            "eastern": east_df,
            "western": west_df,
            "expanded": expanded_df
        }
        
    except Exception as e:
        print(f"Error extracting tables: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'browser' in locals() and browser:
            browser.quit()

def extract_table_data(table, conference_name):
    """Extract data from conference standings table into a DataFrame"""
    rows = table.find_all('tr', class_='full_table')
    
    data = []
    for row in rows:
        team_cell = row.find('th', {'data-stat': 'team_name'})
        team_name = team_cell.find('a').text if team_cell and team_cell.find('a') else ""
        
        # Extract seed number from the span if available
        seed_span = team_cell.find('span', class_='seed')
        seed = re.search(r'\((\d+)', seed_span.text).group(1) if seed_span else ""
        
        wins = row.find('td', {'data-stat': 'wins'}).text if row.find('td', {'data-stat': 'wins'}) else ""
        losses = row.find('td', {'data-stat': 'losses'}).text if row.find('td', {'data-stat': 'losses'}) else ""
        win_loss_pct = row.find('td', {'data-stat': 'win_loss_pct'}).text if row.find('td', {'data-stat': 'win_loss_pct'}) else ""
        gb = row.find('td', {'data-stat': 'gb'}).text if row.find('td', {'data-stat': 'gb'}) else ""
        pts_per_game = row.find('td', {'data-stat': 'pts_per_g'}).text if row.find('td', {'data-stat': 'pts_per_g'}) else ""
        opp_pts_per_game = row.find('td', {'data-stat': 'opp_pts_per_g'}).text if row.find('td', {'data-stat': 'opp_pts_per_g'}) else ""
        srs = row.find('td', {'data-stat': 'srs'}).text if row.find('td', {'data-stat': 'srs'}) else ""
        
        data.append({
            'Conference': conference_name,
            'Team': team_name,
            'Seed': seed,
            'Wins': wins,
            'Losses': losses,
            'Win_Loss_Pct': win_loss_pct,
            'GB': gb,
            'Points_Per_Game': pts_per_game,
            'Opp_Points_Per_Game': opp_pts_per_game,
            'SRS': srs
        })
    
    return pd.DataFrame(data)

def extract_expanded_table_data(table):
    """Extract data from expanded standings table into a DataFrame"""
    rows = table.find_all('tr', {'data-row': re.compile(r'\d+')})
    
    # Get all column headers
    headers = []
    header_row = table.find('tr', class_=None)
    if header_row:
        for th in header_row.find_all('th'):
            # Get the data-stat attribute as the column name
            stat = th.get('data-stat', '')
            # Get the text as a more readable name
            text = th.get_text(strip=True)
            if stat and text:
                headers.append((stat, text))
    
    data = []
    for row in rows:
        row_data = {}
        
        # Get team name
        team_cell = row.find('td', {'data-stat': 'team_name'})
        if team_cell and team_cell.find('a'):
            row_data['Team'] = team_cell.find('a').text
        
        # Extract all columns
        for stat, header_text in headers:
            if stat == 'ranker':  # Skip the rank column
                continue
                
            if stat == 'team_name':
                continue  # Already handled above
                
            cell = row.find(['td', 'th'], {'data-stat': stat})
            if cell:
                row_data[header_text] = cell.text.strip()
            else:
                row_data[header_text] = ""
        
        data.append(row_data)
    
    return pd.DataFrame(data)

def save_dataframes_to_csv(dataframes, output_dir='data'):
    """Save the extracted DataFrames to CSV files"""
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    season = '2025'  # Default season, could be extracted from the page
    timestamp = time.strftime("%Y%m%d")
    
    # Save each table
    results = {}
    for table_name, df in dataframes.items():
        if df is not None:
            filename = f"{output_dir}/nba_{season}_{table_name}_standings_{timestamp}.csv"
            df.to_csv(filename, index=False)
            print(f"Saved {table_name} standings to {filename}")
            results[table_name] = filename
    
    return results

def scrape_standings(url="https://www.basketball-reference.com/leagues/NBA_2025_standings.html", output_dir="data"):
    """Main function to scrape NBA standings and save as CSV files"""
    print(f"Scraping NBA standings from {url}")
    tables = extract_tables_from_url(url)
    
    if tables:
        csv_files = save_dataframes_to_csv(tables, output_dir)
        print("\nScraping completed successfully!")
        for table_name, filepath in csv_files.items():
            print(f"- {table_name.capitalize()} standings saved to: {filepath}")
    else:
        print("Failed to extract tables.")

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("NBA STANDINGS SCRAPER")
    print("="*80)
    print("This script scrapes NBA standings from Basketball Reference and saves them as CSV files.")
    print("\nBefore using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS/Linux, run:")
    print("  google-chrome --remote-debugging-port=9222")
    print("\nOn Windows, run (adjust path as needed):")
    print("  \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    print("\nThen run this script to scrape the standings and save them as CSV files.")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Show instructions
    show_instructions()
    
    # Ask if user is ready
    proceed = input("Have you already started Chrome with debugging enabled? (y/n): ")
    if proceed.lower() != 'y':
        print("Please start Chrome with debugging enabled first.")
    else:
        # Default URL for NBA standings
        url = "https://www.basketball-reference.com/leagues/NBA_2025_standings.html"
        
        # Allow custom URL
        custom_url = input(f"Enter standings URL (or press Enter for default: {url}): ")
        if custom_url.strip():
            url = custom_url
            
        # Allow custom output directory
        output_dir = input("Enter output directory (or press Enter for default 'data'): ").strip()
        if not output_dir:
            output_dir = "data"
            
        # Run the scraper
        scrape_standings(url, output_dir)
