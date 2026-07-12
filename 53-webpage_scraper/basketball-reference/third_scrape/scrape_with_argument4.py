import os
import time
import pandas as pd
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def connect_to_existing_chrome():
    """Connect to an already running Chrome instance with remote debugging"""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")
        print("Make sure Chrome is running with --remote-debugging-port=9222")
        return None

def get_cell_value(row, stat_name):
    """Helper function to extract cell value by stat name"""
    cell = row.find('td', {'data-stat': stat_name})
    return cell.text.strip() if cell else ""

def extract_four_factors(browser, game_info):
    """Extract Four Factors data from a box score URL"""
    try:
        # Navigate to box score page
        box_score_url = game_info['Box_Score_URL']
        browser.get(box_score_url)
        print(f"Loading: {box_score_url}")
        time.sleep(2)  # Wait for page to load
        
        # Get the page HTML and parse it
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Find the Four Factors table
        four_factors_table = soup.find('table', {'id': 'four_factors'})
        
        if not four_factors_table:
            print("Four Factors table not found")
            return None
        
        print("Found Four Factors table")
        
        # Get rows from the table (should be 2 rows - away team and home team)
        rows = four_factors_table.find('tbody').find_all('tr')
        
        four_factors_data = []
        
        # First row is visitor team
        if len(rows) > 0:
            visitor_row = rows[0]
            visitor_data = {
                'Game_Date': game_info['Date'],
                'Team': game_info['Visitor_Team'],
                'Is_Home_Team': False,
                'Opponent': game_info['Home_Team'],
                'Team_Score': game_info['Visitor_Points'],
                'Opponent_Score': game_info['Home_Points'],
                'Pace': get_cell_value(visitor_row, 'pace'),
                'eFG_PCT': get_cell_value(visitor_row, 'efg_pct'),
                'TOV_PCT': get_cell_value(visitor_row, 'tov_pct'),
                'ORB_PCT': get_cell_value(visitor_row, 'orb_pct'),
                'FT_Rate': get_cell_value(visitor_row, 'ft_rate'),
                'ORtg': get_cell_value(visitor_row, 'off_rtg'),
                'Box_Score_URL': box_score_url
            }
            four_factors_data.append(visitor_data)
        
        # Second row is home team
        if len(rows) > 1:
            home_row = rows[1]
            home_data = {
                'Game_Date': game_info['Date'],
                'Team': game_info['Home_Team'],
                'Is_Home_Team': True,
                'Opponent': game_info['Visitor_Team'],
                'Team_Score': game_info['Home_Points'],
                'Opponent_Score': game_info['Visitor_Points'],
                'Pace': get_cell_value(home_row, 'pace'),
                'eFG_PCT': get_cell_value(home_row, 'efg_pct'),
                'TOV_PCT': get_cell_value(home_row, 'tov_pct'),
                'ORB_PCT': get_cell_value(home_row, 'orb_pct'),
                'FT_Rate': get_cell_value(home_row, 'ft_rate'),
                'ORtg': get_cell_value(home_row, 'off_rtg'),
                'Box_Score_URL': box_score_url
            }
            four_factors_data.append(home_data)
        
        return four_factors_data
        
    except Exception as e:
        print(f"Error extracting Four Factors data: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_schedule(schedule_path, output_dir='data', limit=None, start_date=None, end_date=None, force=False):
    """Process schedule and extract four factors data
    
    Args:
        schedule_path (str): Path to schedule CSV file
        output_dir (str): Output directory
        limit (int, optional): Limit number of games to scrape
        start_date (str, optional): Start date filter
        end_date (str, optional): End date filter
        force (bool): Force re-scrape even if files exist
    """
    # Create output directory and four factors subdirectory
    four_factors_dir = f"{output_dir}/four_factors"
    os.makedirs(four_factors_dir, exist_ok=True)
    
    # Load schedule data
    try:
        print(f"\nLoading schedule from {schedule_path}...")
        schedule_df = pd.read_csv(schedule_path)
        print(f"Loaded {len(schedule_df)} games from schedule")
    except Exception as e:
        print(f"Error loading schedule: {e}")
        return
    
    # Filter to games with box score URLs
    games_with_box_scores = schedule_df[schedule_df['Box_Score_URL'].str.strip() != '']
    total_original = len(games_with_box_scores)
    
    if total_original == 0:
        print("No games with box score URLs found in schedule")
        return
    
    # Apply date filters if specified
    if start_date or end_date:
        try:
            # Convert string dates to datetime for comparison
            schedule_df['Date_Obj'] = pd.to_datetime(schedule_df['Date'], format='%a, %b %d, %Y', errors='coerce')
            games_with_box_scores['Date_Obj'] = pd.to_datetime(games_with_box_scores['Date'], format='%a, %b %d, %Y', errors='coerce')
            
            if start_date:
                from_date_obj = pd.to_datetime(start_date)
                games_with_box_scores = games_with_box_scores[games_with_box_scores['Date_Obj'] >= from_date_obj]
            
            if end_date:
                to_date_obj = pd.to_datetime(end_date)
                games_with_box_scores = games_with_box_scores[games_with_box_scores['Date_Obj'] <= to_date_obj]
            
            print(f"Filtered from {total_original} to {len(games_with_box_scores)} games using date range")
        except Exception as e:
            print(f"Error applying date filters: {e}")
            print("Continuing with all games")
    
    # Apply limit if specified
    if limit and limit > 0:
        games_with_box_scores = games_with_box_scores.head(limit)
        print(f"Limited to {len(games_with_box_scores)} games")
    
    total_games = len(games_with_box_scores)
    print(f"Preparing to scrape {total_games} games")
    
    # Connect to Chrome
    browser = connect_to_existing_chrome()
    if not browser:
        print("Failed to connect to Chrome for box score scraping.")
        return
    
    # Initialize a list to collect all four factors data
    all_four_factors = []
    
    try:
        # Process each game
        for i, (_, game) in enumerate(games_with_box_scores.iterrows(), 1):
            # Skip games without box score URLs
            if not game['Box_Score_URL'] or str(game['Box_Score_URL']).strip() == '':
                print(f"Skipping game {i} - no box score URL")
                continue
            
            # Print progress
            visitor = game['Visitor_Team']
            home = game['Home_Team']
            date = game['Date']
            
            print(f"\nGame {i}/{total_games}: {visitor} @ {home} ({date})")
            
            # Generate a filename based on the game info
            visitor_abbr = ''.join([c for c in str(visitor) if c.isupper()]) if visitor else 'VIS'
            home_abbr = ''.join([c for c in str(home) if c.isupper()]) if home else 'HOME'
            
            # Extract date in a safe way
            if isinstance(date, str) and ',' in date:
                game_date = date.split(',')[1].strip().replace(' ', '_')
            else:
                game_date = 'unknown_date'
            
            filename = f"{four_factors_dir}/{game_date}_{visitor_abbr}_at_{home_abbr}_four_factors.csv"
            
            # Check if already scraped
            if os.path.exists(filename) and not force:
                print(f"Four factors data already exists at {filename}, skipping...")
                # Load and append to the combined dataset
                try:
                    existing_data = pd.read_csv(filename)
                    all_four_factors.append(existing_data)
                except Exception as e:
                    print(f"Error loading existing data: {e}, will re-scrape")
                    force = True
                
                if not force:
                    continue
            
            # Extract four factors data
            four_factors_data = extract_four_factors(browser, game)
            
            if four_factors_data:
                # Convert to DataFrame
                four_factors_df = pd.DataFrame(four_factors_data)
                
                # Save to individual CSV
                four_factors_df.to_csv(filename, index=False)
                print(f"Saved four factors data to {filename}")
                
                # Add to combined dataset
                all_four_factors.append(four_factors_df)
            else:
                print(f"Failed to extract four factors for {visitor_abbr} @ {home_abbr}")
            
            # Add a delay between requests
            time.sleep(1)
        
        # Save combined four factors data if we have any results
        if all_four_factors:
            combined_data = pd.concat(all_four_factors, ignore_index=True)
            combined_filename = f"{four_factors_dir}/all_four_factors.csv"
            combined_data.to_csv(combined_filename, index=False)
            print(f"\nSaved combined four factors data to {combined_filename}")
            
            # Create merged dataset with schedule info
            print("\nCreating comprehensive dataset with schedule and four factors data...")
            
            # Create game identifiers for matching
            schedule_df['game_id'] = (
                schedule_df['Date'].astype(str).str.replace(',', '').str.replace(' ', '_') + '_' + 
                schedule_df['Visitor_Team'].astype(str).str.replace(' ', '') + '_' + 
                schedule_df['Home_Team'].astype(str).str.replace(' ', '')
            )
            
            # For four factors: create game_id based on home/away status
            combined_data['game_date_formatted'] = combined_data['Game_Date'].astype(str).str.replace(',', '').str.replace(' ', '_')
            
            def create_game_id(row):
                if row['Is_Home_Team']:
                    # This team is home, opponent is visitor
                    return f"{row['game_date_formatted']}_{row['Opponent']}_{row['Team']}".replace(' ', '')
                else:
                    # This team is visitor, opponent is home
                    return f"{row['game_date_formatted']}_{row['Team']}_{row['Opponent']}".replace(' ', '')
            
            combined_data['game_id'] = combined_data.apply(create_game_id, axis=1)
            
            # Merge the datasets
            merged_df = pd.merge(
                schedule_df,
                combined_data,
                on='game_id',
                how='outer'
            )
            
            # Clean up columns for final dataset
            columns_to_keep = [
                # Game identification
                'Date', 'Time', 'Arena', 'Attendance', 'Game_Duration',
                
                # Teams and scores
                'Visitor_Team', 'Visitor_Points', 
                'Home_Team', 'Home_Points',
                'Overtime', 'Notes',
                
                # Team-specific data
                'Team', 'Opponent', 'Is_Home_Team',
                
                # Four factors data
                'Pace', 'eFG_PCT', 'TOV_PCT', 
                'ORB_PCT', 'FT_Rate', 'ORtg',
                
                # Link to source
                'Box_Score_URL'
            ]
            
            # Keep only columns that exist
            columns_to_keep = [col for col in columns_to_keep if col in merged_df.columns]
            
            # Add any remaining columns
            other_columns = [col for col in merged_df.columns 
                          if col not in columns_to_keep and col != 'game_id' 
                          and not col.endswith('_formatted')
                          and not col.endswith('_Obj')]
            columns_to_keep.extend(other_columns)
            
            # Reorder and select columns
            merged_df = merged_df[columns_to_keep]
            
            # Save comprehensive dataset
            merged_filename = f"{output_dir}/nba_comprehensive_data.csv"
            merged_df.to_csv(merged_filename, index=False)
            print(f"Saved comprehensive dataset to {merged_filename}")
            return merged_filename
        else:
            print("No four factors data was collected")
            return None
            
    except Exception as e:
        print(f"Error while scraping: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if browser:
            browser.quit()

def main():
    """Main function to parse arguments and process schedule"""
    # Create argument parser
    parser = argparse.ArgumentParser(description='Extract NBA Four Factors data using an existing schedule')
    
    # Add arguments
    parser.add_argument('schedule', help='Path to the schedule CSV file')
    parser.add_argument('-o', '--output', default='data', help='Output directory (default: data)')
    parser.add_argument('-l', '--limit', type=int, help='Limit number of games to scrape')
    parser.add_argument('-s', '--start-date', help='Start date filter (e.g. "Oct 22, 2024")')
    parser.add_argument('-e', '--end-date', help='End date filter (e.g. "Oct 31, 2024")')
    parser.add_argument('-f', '--force', action='store_true', help='Force re-scrape even if files exist')
    
    # Parse arguments
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("FOUR FACTORS SCRAPER USING EXISTING SCHEDULE")
    print("="*80)
    
    print("\nThis script extracts Four Factors data from box score URLs in an existing schedule.")
    print("\nBefore using this script, you need to start Chrome with remote debugging enabled.")
    print("\nOn Windows: \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    print("On macOS/Linux: google-chrome --remote-debugging-port=9222")
    print("="*80 + "\n")
    
    # Check if schedule file exists
    if not os.path.exists(args.schedule):
        print(f"Schedule file not found: {args.schedule}")
        return
    
    # Ask if Chrome is ready
    proceed = input("Have you already started Chrome with debugging enabled? (y/n): ")
    if proceed.lower() != 'y':
        print("Please start Chrome with debugging enabled first.")
        return
    
    # Process the schedule
    result = process_schedule(
        args.schedule,
        output_dir=args.output,
        limit=args.limit,
        start_date=args.start_date,
        end_date=args.end_date,
        force=args.force
    )
    
    if result:
        print("\nScraping completed successfully!")
    else:
        print("\nScraping completed with issues.")

if __name__ == "__main__":
    main()
