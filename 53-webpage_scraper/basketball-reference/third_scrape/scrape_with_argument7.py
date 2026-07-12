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

def extract_four_factors(browser, game_info, retry_count=0):
    """
    Extract Four Factors data from a box score URL
    
    Args:
        browser: Selenium WebDriver instance
        game_info: Dictionary with game information
        retry_count: Number of retries already attempted
        
    Returns:
        List of dictionaries with four factors data, or None if extraction failed
    """
    max_retries = 3
    
    try:
        # Navigate to box score page
        box_score_url = game_info['Box_Score_URL']
        browser.get(box_score_url)
        print(f"Loading: {box_score_url}" + (" (Retry #" + str(retry_count) + ")" if retry_count > 0 else ""))
        
        # Wait for page to load - increase wait time for retries
        wait_time = 2 + (retry_count * 1)  # Add 1 second for each retry
        time.sleep(wait_time)
        
        # Get the page HTML and parse it
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Convert date to ISO format (YYYY-MM-DD)
        game_date_str = game_info['Date']  # e.g. "Sat, Mar 1, 2025"
        try:
            # Convert to datetime object
            game_date_obj = pd.to_datetime(game_date_str, format='%a, %b %d, %Y')
            # Format as YYYY-MM-DD
            formatted_date = game_date_obj.strftime('%Y-%m-%d')
        except:
            formatted_date = game_date_str  # Keep original if conversion fails
        
        # Find the Four Factors table
        four_factors_table = soup.find('table', {'id': 'four_factors'})
        
        if not four_factors_table:
            print("Four Factors table not found")
            
            # If we haven't reached max retries, suggest a retry
            if retry_count < max_retries:
                print(f"Retry attempt {retry_count+1}/{max_retries} failed.")
                return None
            else:
                print(f"Maximum retries ({max_retries}) reached. Unable to extract data.")
                return None
        
        print("Found Four Factors table")
        
        # Get rows from the table (should be 2 rows - away team and home team)
        rows = four_factors_table.find('tbody').find_all('tr')
        
        if len(rows) < 2:
            print(f"Expected 2 rows in Four Factors table, but found {len(rows)}")
            return None
        
        four_factors_data = []
        
        # First row is visitor team
        visitor_row = rows[0]
        home_row = rows[1]
        
        # Get scores as integers for comparison
        visitor_points = int(game_info['Visitor_Points'])
        home_points = int(game_info['Home_Points'])
        
        visitor_data = {
            'Game_Date': game_info['Date'],
            'Game_Date_ISO': formatted_date,
            'Team': game_info['Visitor_Team'],
            'Is_Home_Team': False,
            'Opponent': game_info['Home_Team'],
            'Team_Score': visitor_points,
            'Opponent_Score': home_points,
            'Pace': get_cell_value(visitor_row, 'pace'),
            'eFG_PCT': get_cell_value(visitor_row, 'efg_pct'),
            'TOV_PCT': get_cell_value(visitor_row, 'tov_pct'),
            'ORB_PCT': get_cell_value(visitor_row, 'orb_pct'),
            'FT_Rate': get_cell_value(visitor_row, 'ft_rate'),
            'ORtg': get_cell_value(visitor_row, 'off_rtg'),
            'Won': 1 if visitor_points > home_points else 0,
            'Home_Won': 0,  # Visitor is away team
            'Opponent_eFG_PCT': get_cell_value(home_row, 'efg_pct'),
            'Opponent_TOV_PCT': get_cell_value(home_row, 'tov_pct'),
            'Opponent_ORB_PCT': get_cell_value(home_row, 'orb_pct'),
            'Opponent_FT_Rate': get_cell_value(home_row, 'ft_rate'),
            'Opponent_ORtg': get_cell_value(home_row, 'off_rtg'),
            'Box_Score_URL': box_score_url
        }
        four_factors_data.append(visitor_data)
        
        # Second row is home team
        home_data = {
            'Game_Date': game_info['Date'],
            'Game_Date_ISO': formatted_date,
            'Team': game_info['Home_Team'],
            'Is_Home_Team': True,
            'Opponent': game_info['Visitor_Team'],
            'Team_Score': home_points,
            'Opponent_Score': visitor_points,
            'Pace': get_cell_value(home_row, 'pace'),
            'eFG_PCT': get_cell_value(home_row, 'efg_pct'),
            'TOV_PCT': get_cell_value(home_row, 'tov_pct'),
            'ORB_PCT': get_cell_value(home_row, 'orb_pct'),
            'FT_Rate': get_cell_value(home_row, 'ft_rate'),
            'ORtg': get_cell_value(home_row, 'off_rtg'),
            'Won': 1 if home_points > visitor_points else 0,
            'Home_Won': 1,  # Home is home team
            'Opponent_eFG_PCT': get_cell_value(visitor_row, 'efg_pct'),
            'Opponent_TOV_PCT': get_cell_value(visitor_row, 'tov_pct'),
            'Opponent_ORB_PCT': get_cell_value(visitor_row, 'orb_pct'),
            'Opponent_FT_Rate': get_cell_value(visitor_row, 'ft_rate'),
            'Opponent_ORtg': get_cell_value(visitor_row, 'off_rtg'),
            'Box_Score_URL': box_score_url
        }
        four_factors_data.append(home_data)
        
        return four_factors_data
        
    except Exception as e:
        print(f"Error extracting Four Factors data: {e}")
        import traceback
        traceback.print_exc()
        
        # If we haven't reached max retries, allow retry
        if retry_count < max_retries:
            print(f"Retry attempt {retry_count+1}/{max_retries} failed due to error.")
            return None
        else:
            print(f"Maximum retries ({max_retries}) reached. Unable to extract data.")
            return None
#
# here output_dir is defined as data

def process_schedule(schedule_path, output_dir='data', limit=None, start_date=None, end_date=None, force=False, interactive=True):
    """Process schedule and extract four factors data
    
    Args:
        schedule_path (str): Path to schedule CSV file
        output_dir (str): Output directory
        limit (int, optional): Limit number of games to scrape
        start_date (str, optional): Start date filter
        end_date (str, optional): End date filter
        force (bool): Force re-scrape even if files exist
        interactive (bool): Prompt for confirmation after each game
    """
    # Create output directory and four factors subdirectory
    # def process_schedule(schedule_path, output_dir='data', limit=None, start_date=None, end_date=None, force=False, interactive=True):
    # data is defined in this function so it will save it in there. 

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
        # Convert to list for easier manipulation
        games_list = games_with_box_scores.to_dict('records')
        i = 0  # Game index
        
        # Process each game
        while i < len(games_list):
            game = games_list[i]
            
            # Skip games without box score URLs
            if not game['Box_Score_URL'] or str(game['Box_Score_URL']).strip() == '':
                print(f"Skipping game {i+1} - no box score URL")
                i += 1
                continue
            
            # Print progress
            visitor = game['Visitor_Team']
            home = game['Home_Team']
            date = game['Date']
            
            print(f"\nGame {i+1}/{total_games}: {visitor} @ {home} ({date})")
            
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
                    if interactive:
                        continue_scraping = input("Continue to next game? (y/n): ")
                        if continue_scraping.lower() != 'y':
                            print("Stopping scraping as requested.")
                            break
                    i += 1  # Move to next game
                    continue
            
            # Extract four factors data
            retry_count = 0
            four_factors_data = None
            
            # Keep trying until we succeed or hit retry limit
            while four_factors_data is None:
                four_factors_data = extract_four_factors(browser, game, retry_count)
                
                if four_factors_data is None:
                    if interactive:
                        retry_option = input("Failed to extract data. Retry this game? (y/n): ")
                        if retry_option.lower() == 'y':
                            retry_count += 1
                            print(f"Retrying game {i+1}...")
                            continue
                        else:
                            print(f"Skipping game {i+1} as requested.")
                            break
                    else:
                        # In non-interactive mode, retry automatically up to 3 times
                        if retry_count < 3:
                            retry_count += 1
                            print(f"Automatically retrying ({retry_count}/3)...")
                            time.sleep(2)  # Wait before retry
                            continue
                        else:
                            print(f"Maximum auto-retries reached. Skipping game {i+1}.")
                            break
            
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
            
            # Ask to continue if in interactive mode
            if interactive:
                continue_scraping = input("Continue to next game? (y/n): ")
                if continue_scraping.lower() != 'y':
                    print("Stopping scraping as requested.")
                    break
            else:
                # Add a delay between requests if not interactive
                time.sleep(1)
                
            # Move to next game
            i += 1
        
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
                'Date', 'Game_Date_ISO', 'Time', 'Arena', 'Attendance', 'Game_Duration',
                
                # Teams and scores
                'Visitor_Team', 'Visitor_Points', 
                'Home_Team', 'Home_Points',
                'Overtime', 'Notes',
                
                # Team-specific data
                'Team', 'Opponent', 'Is_Home_Team', 'Won', 'Home_Won',
                
                # Four factors data
                'Pace', 'eFG_PCT', 'TOV_PCT', 
                'ORB_PCT', 'FT_Rate', 'ORtg',
                
                # Opponent stats
                'Opponent_eFG_PCT', 'Opponent_TOV_PCT',
                'Opponent_ORB_PCT', 'Opponent_FT_Rate', 'Opponent_ORtg',
                
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
            
            # Now create a one-row-per-game version for reporting
            print("\nCreating one-row-per-game dataset for reporting...")
            create_reporting_dataset(combined_data, schedule_df, output_dir)
            
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

def create_reporting_dataset(four_factors_df, schedule_df, output_dir):
    """
    Create a one-row-per-game dataset for reporting purposes.
    
    Args:
        four_factors_df (DataFrame): The combined four factors data
        schedule_df (DataFrame): The schedule data
        output_dir (str): Output directory
    """
    # Transform data to have one row per game
    # First, separate home and visitor data
    home_teams = four_factors_df[four_factors_df['Is_Home_Team'] == True].copy()
    away_teams = four_factors_df[four_factors_df['Is_Home_Team'] == False].copy()
    
    # Rename columns to distinguish home and away stats
    home_teams = home_teams.rename(columns={
        'Team': 'Home_Team_Name',
        'Opponent': 'Away_Team_Name',
        'Team_Score': 'Home_Score',
        'Opponent_Score': 'Away_Score',
        'Pace': 'Game_Pace',  # Same for both teams
        'eFG_PCT': 'Home_eFG_PCT',
        'TOV_PCT': 'Home_TOV_PCT',
        'ORB_PCT': 'Home_ORB_PCT',
        'FT_Rate': 'Home_FT_Rate',
        'ORtg': 'Home_ORtg',
        'Won': 'Home_Team_Won',
        'Opponent_eFG_PCT': 'Home_Opp_eFG_PCT',
        'Opponent_TOV_PCT': 'Home_Opp_TOV_PCT',
        'Opponent_ORB_PCT': 'Home_Opp_ORB_PCT',
        'Opponent_FT_Rate': 'Home_Opp_FT_Rate',
        'Opponent_ORtg': 'Home_Opp_ORtg',
        'Game_Date_ISO': 'Game_Date_ISO'
    })
    
    away_teams = away_teams.rename(columns={
        'Team': 'Away_Team_Name',
        'Opponent': 'Home_Team_Name',
        'Team_Score': 'Away_Score',
        'Opponent_Score': 'Home_Score',
        'Pace': 'Game_Pace',  # Same for both teams
        'eFG_PCT': 'Away_eFG_PCT',
        'TOV_PCT': 'Away_TOV_PCT',
        'ORB_PCT': 'Away_ORB_PCT',
        'FT_Rate': 'Away_FT_Rate',
        'ORtg': 'Away_ORtg',
        'Won': 'Away_Team_Won',
        'Opponent_eFG_PCT': 'Away_Opp_eFG_PCT',
        'Opponent_TOV_PCT': 'Away_Opp_TOV_PCT',
        'Opponent_ORB_PCT': 'Away_Opp_ORB_PCT',
        'Opponent_FT_Rate': 'Away_Opp_FT_Rate',
        'Opponent_ORtg': 'Away_Opp_ORtg',
        'Game_Date_ISO': 'Game_Date_ISO'
    })
    
    # Create a game ID for joining the datasets
    home_teams['game_id'] = home_teams['Box_Score_URL'].str.split('/').str[-1].str.split('.').str[0]
    away_teams['game_id'] = away_teams['Box_Score_URL'].str.split('/').str[-1].str.split('.').str[0]
    
    # Select only necessary columns from both dataframes
    home_cols = ['game_id', 'Game_Date', 'Game_Date_ISO', 'Box_Score_URL', 
                 'Home_Team_Name', 'Home_Score', 'Home_Team_Won',
                 'Game_Pace', 'Home_eFG_PCT', 'Home_TOV_PCT', 'Home_ORB_PCT', 
                 'Home_FT_Rate', 'Home_ORtg', 'Home_Opp_eFG_PCT', 
                 'Home_Opp_TOV_PCT', 'Home_Opp_ORB_PCT', 'Home_Opp_FT_Rate', 
                 'Home_Opp_ORtg']
    
    away_cols = ['game_id', 'Away_Team_Name', 'Away_Score', 'Away_Team_Won',
                 'Away_eFG_PCT', 'Away_TOV_PCT', 'Away_ORB_PCT', 
                 'Away_FT_Rate', 'Away_ORtg', 'Away_Opp_eFG_PCT', 
                 'Away_Opp_TOV_PCT', 'Away_Opp_ORB_PCT', 'Away_Opp_FT_Rate', 
                 'Away_Opp_ORtg']
    
    # Keep only columns that exist
    home_cols = [col for col in home_cols if col in home_teams.columns]
    away_cols = [col for col in away_cols if col in away_teams.columns]
    
    home_data = home_teams[home_cols]
    away_data = away_teams[away_cols]
    
    # Merge home and away data on game_id
    games_df = pd.merge(home_data, away_data, on='game_id', how='inner')
    
    # Make sure we only have unique games (no duplicates)
    games_df = games_df.drop_duplicates(subset=['game_id'])
    
    # Create a game identifier for schedule dataframe to match with our combined data
    schedule_df['game_id'] = schedule_df['Box_Score_URL'].str.split('/').str[-1].str.split('.').str[0]
    
    # Merge with schedule data for additional details
    schedule_cols = ['Date', 'Time', 'Overtime', 'Attendance', 'Game_Duration', 'Arena', 'Notes', 'game_id']
    schedule_cols = [col for col in schedule_cols if col in schedule_df.columns]
    
    schedule_data = schedule_df[schedule_cols]
    
    # Perform the merge
    final_df = pd.merge(games_df, schedule_data, on='game_id', how='left')
    
    # Calculate point differential and advanced metrics
    final_df['Home_Point_Diff'] = final_df['Home_Score'] - final_df['Away_Score']
    final_df['Home_Won'] = final_df['Home_Point_Diff'] > 0
    final_df['Home_Won_Binary'] = final_df['Home_Point_Diff'].apply(lambda x: 1 if x > 0 else 0)
    final_df['Away_Won_Binary'] = final_df['Home_Point_Diff'].apply(lambda x: 0 if x > 0 else 1)
    
    # Calculate four factors differentials
    final_df['eFG_PCT_Diff'] = final_df['Home_eFG_PCT'].astype(float) - final_df['Away_eFG_PCT'].astype(float)
    final_df['TOV_PCT_Diff'] = final_df['Away_TOV_PCT'].astype(float) - final_df['Home_TOV_PCT'].astype(float)
    final_df['ORB_PCT_Diff'] = final_df['Home_ORB_PCT'].astype(float) - final_df['Away_ORB_PCT'].astype(float)
    final_df['FT_Rate_Diff'] = final_df['Home_FT_Rate'].astype(float) - final_df['Away_FT_Rate'].astype(float)
    
    # Standardize date format if not already done
    if 'Game_Date_ISO' not in final_df.columns and 'Date' in final_df.columns:
        try:
            final_df['Game_Date_ISO'] = pd.to_datetime(final_df['Date'], format='%a, %b %d, %Y').dt.strftime('%Y-%m-%d')
        except:
            pass  # Keep original if conversion fails
    
    # Organize columns in logical order
    col_order = [
        # Game info
        'Date', 'Game_Date_ISO', 'Time', 'Arena', 'Attendance', 'Game_Duration', 'Overtime',
        
        # Away team
        'Away_Team_Name', 'Away_Score', 'Away_Team_Won', 'Away_Won_Binary', 
        'Away_eFG_PCT', 'Away_TOV_PCT', 'Away_ORB_PCT', 'Away_FT_Rate', 'Away_ORtg',
        'Away_Opp_eFG_PCT', 'Away_Opp_TOV_PCT', 'Away_Opp_ORB_PCT', 
        'Away_Opp_FT_Rate', 'Away_Opp_ORtg',
        
        # Home team
        'Home_Team_Name', 'Home_Score', 'Home_Team_Won', 'Home_Won_Binary',
        'Home_eFG_PCT', 'Home_TOV_PCT', 'Home_ORB_PCT', 'Home_FT_Rate', 'Home_ORtg',
        'Home_Opp_eFG_PCT', 'Home_Opp_TOV_PCT', 'Home_Opp_ORB_PCT', 
        'Home_Opp_FT_Rate', 'Home_Opp_ORtg',
        
        # Game pace (shared)
        'Game_Pace',
        
        # Calculated metrics
        'Home_Point_Diff', 'Home_Won',
        'eFG_PCT_Diff', 'TOV_PCT_Diff', 'ORB_PCT_Diff', 'FT_Rate_Diff',
        
        # Source and other info
        'Box_Score_URL', 'Notes'
    ]
    
    # Keep only columns that exist
    col_order = [col for col in col_order if col in final_df.columns]
    
    # Add any columns we missed
    other_cols = [col for col in final_df.columns 
                  if col not in col_order and col != 'game_id']
    col_order.extend(other_cols)
    
    # Reorder columns
    final_df = final_df[col_order]
    
    # Save to CSV
    reporting_filename = f"{output_dir}/nba_four_factors_report.csv"
    final_df.to_csv(reporting_filename, index=False)
    print(f"Saved one-row-per-game reporting dataset to {reporting_filename}")
    
    return reporting_filename

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
    parser.add_argument('-b', '--batch', action='store_true', help='Run in batch mode (no prompts)')
    
    # Parse arguments
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("INTERACTIVE FOUR FACTORS SCRAPER WITH RETRY")
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
    
    # Process the schedule with interactive mode unless batch flag is set
    result = process_schedule(
        args.schedule,
        output_dir=args.output,
        limit=args.limit,
        start_date=args.start_date,
        end_date=args.end_date,
        force=args.force,
        interactive=not args.batch
    )
    
    if result:
        print("\nScraping completed successfully!")
    else:
        print("\nScraping completed with issues.")

if __name__ == "__main__":
    main()
