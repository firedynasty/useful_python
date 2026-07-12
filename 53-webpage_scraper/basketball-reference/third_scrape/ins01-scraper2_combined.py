#!/usr/bin/env python3

import os
import time
import socket
import pandas as pd
import argparse
import sys
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

def extract_schedule_data(url):
    """Extract NBA schedule data from the given URL"""
    try:
        print(f"Connecting to Chrome and navigating to {url}...")
        browser = connect_to_existing_chrome()
        
        if not browser:
            print("Failed to connect to Chrome.")
            return None
            
        # Navigate to the schedule page
        browser.get(url)
        print(f"Loaded page: {browser.title}")
        
        # Wait for the page to fully load
        time.sleep(2)
        
        # Get the page HTML
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Find the schedule table
        schedule_table = soup.find('table', {'id': 'schedule'})
        
        if not schedule_table:
            print("Schedule table not found")
            return None
            
        print("Found schedule table")
        games_data = extract_games_data(schedule_table)
        
        return games_data
        
    except Exception as e:
        print(f"Error extracting schedule: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'browser' in locals() and browser:
            browser.quit()

def extract_games_data(table):
    """Extract data from schedule table into a DataFrame"""
    # Find all game rows (skip header rows)
    rows = table.find_all('tr', {'data-row': True})
    
    data = []
    for row in rows:
        # Extract date
        date_cell = row.find('th', {'data-stat': 'date_game'})
        date = date_cell.find('a').text if date_cell and date_cell.find('a') else ""
        
        # Extract game time
        time_cell = row.find('td', {'data-stat': 'game_start_time'})
        game_time = time_cell.text if time_cell else ""
        
        # Extract visitor team
        visitor_cell = row.find('td', {'data-stat': 'visitor_team_name'})
        visitor_team = visitor_cell.find('a').text if visitor_cell and visitor_cell.find('a') else ""
        
        # Extract visitor points
        visitor_pts_cell = row.find('td', {'data-stat': 'visitor_pts'})
        visitor_pts = visitor_pts_cell.text if visitor_pts_cell else ""
        
        # Extract home team
        home_cell = row.find('td', {'data-stat': 'home_team_name'})
        home_team = home_cell.find('a').text if home_cell and home_cell.find('a') else ""
        
        # Extract home points
        home_pts_cell = row.find('td', {'data-stat': 'home_pts'})
        home_pts = home_pts_cell.text if home_pts_cell else ""
        
        # Extract box score link
        box_score_cell = row.find('td', {'data-stat': 'box_score_text'})
        box_score_link = box_score_cell.find('a')['href'] if box_score_cell and box_score_cell.find('a') else ""
        
        # Extract overtime info
        overtime_cell = row.find('td', {'data-stat': 'overtimes'})
        overtime = overtime_cell.text if overtime_cell else ""
        
        # Extract attendance
        attendance_cell = row.find('td', {'data-stat': 'attendance'})
        attendance = attendance_cell.text if attendance_cell else ""
        
        # Extract game duration
        duration_cell = row.find('td', {'data-stat': 'game_duration'})
        duration = duration_cell.text if duration_cell else ""
        
        # Extract arena
        arena_cell = row.find('td', {'data-stat': 'arena_name'})
        arena = arena_cell.text if arena_cell else ""
        
        # Extract notes/remarks
        notes_cell = row.find('td', {'data-stat': 'game_remarks'})
        notes = notes_cell.text if notes_cell else ""
        
        # Get the full box score URL
        box_score_url = ""
        if box_score_link:
            box_score_url = f"https://www.basketball-reference.com{box_score_link}"
        
        data.append({
            'Date': date,
            'Time': game_time,
            'Visitor_Team': visitor_team,
            'Visitor_Points': visitor_pts,
            'Home_Team': home_team,
            'Home_Points': home_pts,
            'Box_Score_URL': box_score_url,
            'Overtime': overtime,
            'Attendance': attendance,
            'Game_Duration': duration,
            'Arena': arena,
            'Notes': notes
        })
    
    return pd.DataFrame(data)

def save_dataframe_to_csv(df, output_dir='data', clean_output=True):
    """Save the extracted DataFrame to CSV file with optional cleaning"""
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/nba_2025_schedule_{timestamp}.csv"
    
    if clean_output:
        # Clean the DataFrame by removing rows with empty Box_Score_URL
        initial_rows = len(df)
        
        # Count empty Box_Score_URL values
        empty_count = df['Box_Score_URL'].isna().sum()
        empty_string_count = (df['Box_Score_URL'] == '').sum()
        total_empty = empty_count + empty_string_count
        
        # Drop rows with empty Box_Score_URL (both NaN and empty strings)
        df = df.dropna(subset=['Box_Score_URL'])
        df = df[df['Box_Score_URL'] != '']
        
        # Print summary
        final_rows = len(df)
        print(f"Rows with empty Box_Score_URL: {total_empty}")
        print(f"Final number of rows after dropping empty values: {final_rows}")
        print(f"Removed {initial_rows - final_rows} rows in total")
    
    # Save the DataFrame
    df.to_csv(filename, index=False)
    print(f"Saved schedule data to {filename}")
    
    return filename

def scrape_box_scores(schedule_df, output_dir='data'):
    """Scrape individual box scores for each game in the schedule"""
    if schedule_df is None or schedule_df.empty:
        print("No schedule data to scrape box scores")
        return
    
    # Create subdirectory for box scores
    box_scores_dir = f"{output_dir}/box_scores"
    os.makedirs(box_scores_dir, exist_ok=True)
    
    # Count games with available box scores
    games_with_box_scores = schedule_df[schedule_df['Box_Score_URL'].str.strip() != '']
    total_games = len(games_with_box_scores)
    
    print(f"\nFound {total_games} games with box score links")
    
    # Ask user if they want to scrape all box scores
    all_games = input(f"Do you want to scrape all {total_games} box scores? (y/n, default=n): ")
    
    if all_games.lower() != 'y':
        # Ask for specific date range
        from_date = input("Enter start date (e.g. Oct 22, 2024) or leave empty for all: ")
        to_date = input("Enter end date (e.g. Oct 31, 2024) or leave empty for all: ")
        
        if from_date and to_date:
            # Filter by date range if provided
            # Convert string dates to datetime for comparison
            schedule_df['Date_Obj'] = pd.to_datetime(schedule_df['Date'], format='%a, %b %d, %Y')
            from_date_obj = pd.to_datetime(from_date)
            to_date_obj = pd.to_datetime(to_date)
            
            games_with_box_scores = games_with_box_scores[
                (games_with_box_scores['Date_Obj'] >= from_date_obj) & 
                (games_with_box_scores['Date_Obj'] <= to_date_obj)
            ]
            
            total_games = len(games_with_box_scores)
            print(f"Filtered to {total_games} games between {from_date} and {to_date}")
    
    # Connect to Chrome using the improved method
    browser = connect_to_existing_chrome()
    if not browser:
        print("Failed to connect to Chrome for box score scraping.")
        return
    
    try:
        # Process each game
        for i, (_, game) in enumerate(games_with_box_scores.iterrows(), 1):
            box_score_url = game['Box_Score_URL']
            if not box_score_url:
                continue
                
            print(f"\nScraping box score {i}/{total_games}: {game['Visitor_Team']} @ {game['Home_Team']} ({game['Date']})")
            
            # Generate a filename based on the game info
            game_date = game['Date'].split(',')[1].strip().replace(' ', '_')
            visitor_abbr = ''.join([c for c in game['Visitor_Team'] if c.isupper()])
            home_abbr = ''.join([c for c in game['Home_Team'] if c.isupper()])
            filename = f"{box_scores_dir}/{game_date}_{visitor_abbr}_at_{home_abbr}.csv"
            
            # Check if already scraped
            if os.path.exists(filename):
                print(f"Box score already exists at {filename}, skipping...")
                continue
            
            # Navigate to box score page
            browser.get(box_score_url)
            print(f"Loading: {box_score_url}")
            time.sleep(2)  # Wait for page to load
            
            # Extract box score data
            box_score_data = extract_box_score(browser.page_source, game)
            
            if box_score_data is not None:
                # Save to CSV
                box_score_data.to_csv(filename, index=False)
                print(f"Saved box score to {filename}")
            else:
                print(f"Failed to extract box score for {visitor_abbr} @ {home_abbr}")
                
            # Add a small delay between requests to avoid rate limiting
            time.sleep(1)
            
    except Exception as e:
        print(f"Error while scraping box scores: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            browser.quit()

def extract_box_score(html, game_info):
    """Extract box score data from the box score page HTML"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Create a dictionary to store all box score data
    box_score_data = {
        'Game_Date': game_info['Date'],
        'Visitor_Team': game_info['Visitor_Team'],
        'Home_Team': game_info['Home_Team'],
        'Visitor_Points': game_info['Visitor_Points'],
        'Home_Points': game_info['Home_Points'],
        'Overtime': game_info['Overtime'],
        'Attendance': game_info['Attendance'],
        'Arena': game_info['Arena']
    }
    
    # Find basic game info table
    game_info_div = soup.find('div', {'class': 'scorebox'})
    if game_info_div:
        # Additional game metadata could be extracted here
        pass
    
    # Extract team stats tables
    visitor_stats = extract_team_stats(soup, is_visitor=True)
    home_stats = extract_team_stats(soup, is_visitor=False)
    
    # Extract line scores (quarter by quarter)
    line_score = extract_line_score(soup)
    
    # Combine all data into a single DataFrame
    all_data = []
    
    # Add team stats if available
    if visitor_stats is not None:
        for _, player in visitor_stats.iterrows():
            row = box_score_data.copy()
            row.update({
                'Team': game_info['Visitor_Team'],
                'Is_Home_Team': False,
                'Player': player.get('Player', ''),
                'MP': player.get('MP', ''),
                'FG': player.get('FG', ''),
                'FGA': player.get('FGA', ''),
                'FG_PCT': player.get('FG%', ''),
                'TP': player.get('3P', ''),
                'TPA': player.get('3PA', ''),
                'TP_PCT': player.get('3P%', ''),
                'FT': player.get('FT', ''),
                'FTA': player.get('FTA', ''),
                'FT_PCT': player.get('FT%', ''),
                'ORB': player.get('ORB', ''),
                'DRB': player.get('DRB', ''),
                'TRB': player.get('TRB', ''),
                'AST': player.get('AST', ''),
                'STL': player.get('STL', ''),
                'BLK': player.get('BLK', ''),
                'TOV': player.get('TOV', ''),
                'PF': player.get('PF', ''),
                'PTS': player.get('PTS', ''),
                'PLUS_MINUS': player.get('+/-', '')
            })
            all_data.append(row)
    
    if home_stats is not None:
        for _, player in home_stats.iterrows():
            row = box_score_data.copy()
            row.update({
                'Team': game_info['Home_Team'],
                'Is_Home_Team': True,
                'Player': player.get('Player', ''),
                'MP': player.get('MP', ''),
                'FG': player.get('FG', ''),
                'FGA': player.get('FGA', ''),
                'FG_PCT': player.get('FG%', ''),
                'TP': player.get('3P', ''),
                'TPA': player.get('3PA', ''),
                'TP_PCT': player.get('3P%', ''),
                'FT': player.get('FT', ''),
                'FTA': player.get('FTA', ''),
                'FT_PCT': player.get('FT%', ''),
                'ORB': player.get('ORB', ''),
                'DRB': player.get('DRB', ''),
                'TRB': player.get('TRB', ''),
                'AST': player.get('AST', ''),
                'STL': player.get('STL', ''),
                'BLK': player.get('BLK', ''),
                'TOV': player.get('TOV', ''),
                'PF': player.get('PF', ''),
                'PTS': player.get('PTS', ''),
                'PLUS_MINUS': player.get('+/-', '')
            })
            all_data.append(row)
    
    # Add line score if available
    if line_score is not None:
        # Could add line score data to the result here
        pass
    
    # Convert to DataFrame
    if all_data:
        return pd.DataFrame(all_data)
    else:
        return None

def extract_team_stats(soup, is_visitor=True):
    """Extract player statistics for a team from the box score page"""
    # Find the appropriate stats table
    # The first table is for the visitor team, the second is for the home team
    index = 0 if is_visitor else 1
    
    # Find all box score tables
    box_tables = soup.find_all('table', {'class': 'sortable stats_table'})
    
    if not box_tables or len(box_tables) <= index:
        return None
    
    # Get the right box score table
    table = box_tables[index]
    
    # Get column headers
    headers = []
    header_row = table.find('thead').find('tr')
    for th in header_row.find_all('th'):
        # Get header text or stat abbreviation
        header = th.get_text(strip=True)
        if not header and 'data-stat' in th.attrs:
            header = th['data-stat']
        headers.append(header)
    
    # Process player data rows
    rows = []
    for tr in table.find('tbody').find_all('tr'):
        # Skip header rows and separators
        if 'class' in tr.attrs and ('thead' in tr['class'] or 'divider' in tr['class']):
            continue
            
        # Extract player data
        player_data = {}
        for i, td in enumerate(tr.find_all(['th', 'td'])):
            if i < len(headers):
                # For player names which are typically in th elements
                if td.name == 'th' and td.find('a'):
                    player_data[headers[i]] = td.find('a').get_text(strip=True)
                else:
                    player_data[headers[i]] = td.get_text(strip=True)
                    
        if player_data:
            rows.append(player_data)
    
    return pd.DataFrame(rows)

def extract_line_score(soup):
    """Extract quarter-by-quarter scores from the box score page"""
    # Find the line score table
    line_score_table = soup.find('table', {'class': 'nav_table stats_table'})
    
    if not line_score_table:
        return None
    
    # Get column headers
    headers = []
    header_row = line_score_table.find('thead').find_all('tr')[-1]  # Get the last header row
    for th in header_row.find_all('th'):
        header = th.get_text(strip=True)
        if header:
            headers.append(header)
    
    # Process team scores by quarter
    rows = []
    for tr in line_score_table.find('tbody').find_all('tr'):
        team_data = {}
        team_name = ""
        
        for i, td in enumerate(tr.find_all(['th', 'td'])):
            if i == 0 and td.find('a'):
                team_name = td.find('a').get_text(strip=True)
                team_data['Team'] = team_name
            elif i < len(headers):
                team_data[headers[i]] = td.get_text(strip=True)
                
        if team_data:
            rows.append(team_data)
    
    return pd.DataFrame(rows)

def show_instructions():
    """Show instructions for starting Chrome with remote debugging"""
    print("\n" + "="*80)
    print("NBA SCHEDULE AND BOX SCORE SCRAPER")
    print("="*80)
    print("This script scrapes NBA schedule and box scores from Basketball Reference.")
    print("\nBefore using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn macOS/Linux, run:")
    print("  google-chrome --remote-debugging-port=9222")
    print("\nOn Windows, run (adjust path as needed):")
    print("  \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    
    # Check if Chrome is already running with debugging
    if check_chrome_running():
        print("\n✓ DETECTED: Chrome appears to be running with remote debugging enabled.")
    else:
        print("\n✗ WARNING: Could not detect Chrome running with remote debugging.")
        print("  Please make sure to start Chrome with the --remote-debugging-port=9222 flag.")
    
    print("="*80 + "\n")

def clean_existing_file(input_file):
    """
    Load an existing NBA schedule CSV, drop rows with empty Box_Score_URL, and save the result.
    
    Args:
        input_file (str): Path to the input CSV file
    """
    try:
        # Generate output filename by adding "_1" before the extension
        file_name, file_ext = os.path.splitext(input_file)
        output_file = f"{file_name}_1{file_ext}"
        
        # Load the CSV file
        print(f"Loading NBA schedule from {input_file}...")
        df = pd.read_csv(input_file)
        
        # Print initial information
        initial_rows = len(df)
        print(f"Initial number of rows: {initial_rows}")
        
        # Check if Box_Score_URL column exists
        if 'Box_Score_URL' not in df.columns:
            print(f"Error: 'Box_Score_URL' column not found in the CSV file.")
            print(f"Available columns: {', '.join(df.columns)}")
            sys.exit(1)
        
        # Count empty Box_Score_URL values
        empty_count = df['Box_Score_URL'].isna().sum()
        empty_string_count = (df['Box_Score_URL'] == '').sum()
        total_empty = empty_count + empty_string_count
        
        # Drop rows with empty Box_Score_URL (both NaN and empty strings)
        df = df.dropna(subset=['Box_Score_URL'])
        df = df[df['Box_Score_URL'] != '']
        
        # Print summary
        final_rows = len(df)
        print(f"Rows with empty Box_Score_URL: {total_empty}")
        print(f"Final number of rows after dropping empty values: {final_rows}")
        print(f"Removed {initial_rows - final_rows} rows in total")
        
        # Save to output file
        df.to_csv(output_file, index=False)
        print(f"Cleaned data saved to {output_file}")
            
        return df
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    """Main function to scrape NBA schedule and box scores or clean existing file"""
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='NBA Schedule Scraper and Cleaner')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--scrape', action='store_true', help='Scrape new NBA schedule data')
    group.add_argument('--clean', metavar='INPUT_FILE', help='Clean an existing schedule CSV file')
    
    parser.add_argument('--output-dir', default='data', help='Output directory for saved files')
    
    args = parser.parse_args()
    
    if args.scrape:
        # Show instructions
        show_instructions()
        
        if not check_chrome_running():
            proceed = input("Chrome debugging does not appear to be running. Try to continue anyway? (y/n): ")
            if proceed.lower() != 'y':
                print("Please start Chrome with --remote-debugging-port=9222 and try again.")
                return
        
        # Default URL for NBA schedule
        default_url = "https://www.basketball-reference.com/leagues/NBA_2025_games.html"
        
        # Allow custom URL
        custom_url = input(f"Enter schedule URL (or press Enter for default: {default_url}): ")
        if not custom_url.strip():
            url = default_url
        else:
            url = custom_url
            
        # Scrape schedule data
        print(f"\nScraping NBA schedule from {url}...")
        schedule_data = extract_schedule_data(url)
        
        if schedule_data is not None and not schedule_data.empty:
            # Save schedule data (with cleaning)
            csv_file = save_dataframe_to_csv(schedule_data, args.output_dir, clean_output=True)
            print(f"\nScraping completed successfully!")
            print(f"- Schedule saved to: {csv_file}")
            
            # Ask if user wants to scrape box scores
            scrape_scores = input("\nDo you want to scrape individual box scores? (y/n): ")
            if scrape_scores.lower() == 'y':
                scrape_box_scores(schedule_data, args.output_dir)
        else:
            print("Failed to extract schedule data.")
    
    elif args.clean:
        # Clean existing file
        clean_existing_file(args.clean)

if __name__ == "__main__":
    main()