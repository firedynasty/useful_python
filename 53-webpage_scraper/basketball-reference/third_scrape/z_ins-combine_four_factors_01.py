import pandas as pd
import os
import glob
import argparse

def combine_four_factors_data(four_factors_dir, schedule_file, output_file):
    """
    Combine multiple four factors CSV files with the NBA schedule into one reporting dataset.
    
    This reorganizes the data so each game appears as a single row with both teams' stats.
    
    Args:
        four_factors_dir (str): Directory containing four factors CSV files
        schedule_file (str): Path to the NBA schedule CSV file
        output_file (str): Path to save the combined data file
    """
    # Load schedule data
    print(f"Loading schedule from {schedule_file}...")
    schedule_df = pd.read_csv(schedule_file)
    
    # Find all four factors files
    pattern = os.path.join(four_factors_dir, "*four_factors.csv")
    four_factors_files = glob.glob(pattern)
    
    if not four_factors_files:
        print(f"No four factors files found in {four_factors_dir}")
        return None
    
    print(f"Found {len(four_factors_files)} four factors files")
    
    # Create a combined four factors dataframe
    all_data = []
    for file in four_factors_files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    if not all_data:
        print("No valid four factors data found")
        return None
    
    # Combine all four factors data
    four_factors_df = pd.concat(all_data, ignore_index=True)
    print(f"Loaded {len(four_factors_df)} rows of four factors data")
    
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
    
    # Select necessary columns from both dataframes
    # First, get all available columns from home and away teams
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
    
    # Select columns from each dataframe
    home_data = home_teams[home_cols]
    away_data = away_teams[away_cols]
    
    # Merge home and away data on game_id
    games_df = pd.merge(home_data, away_data, on='game_id', how='inner')
    
    # Make sure we only have unique games (no duplicates)
    games_df = games_df.drop_duplicates(subset=['game_id'])
    
    print(f"Created {len(games_df)} unique game rows with combined stats")
    
    # Create a game identifier for schedule dataframe to match with our combined data
    schedule_df['game_id'] = schedule_df['Box_Score_URL'].str.split('/').str[-1].str.split('.').str[0]
    
    # Merge with schedule data for additional details
    schedule_cols = ['Date', 'Time', 'Overtime', 'Attendance', 'Game_Duration', 'Arena', 'Notes', 'game_id']
    schedule_cols = [col for col in schedule_cols if col in schedule_df.columns]
    
    schedule_data = schedule_df[schedule_cols]
    
    # Perform the merge
    final_df = pd.merge(games_df, schedule_data, on='game_id', how='left')
    
    # Calculate point differential 
    final_df['Home_Point_Diff'] = final_df['Home_Score'] - final_df['Away_Score']
    
    # Add binary indicators if not already present
    if 'Home_Won_Binary' not in final_df.columns:
        final_df['Home_Won_Binary'] = final_df['Home_Point_Diff'].apply(lambda x: 1 if x > 0 else 0)
    
    if 'Away_Won_Binary' not in final_df.columns:
        final_df['Away_Won_Binary'] = final_df['Home_Point_Diff'].apply(lambda x: 0 if x > 0 else 1)
    
    # Calculate four factors differentials
    final_df['eFG_PCT_Diff'] = final_df['Home_eFG_PCT'].astype(float) - final_df['Away_eFG_PCT'].astype(float)
    final_df['TOV_PCT_Diff'] = final_df['Away_TOV_PCT'].astype(float) - final_df['Home_TOV_PCT'].astype(float)
    final_df['ORB_PCT_Diff'] = final_df['Home_ORB_PCT'].astype(float) - final_df['Away_ORB_PCT'].astype(float)
    final_df['FT_Rate_Diff'] = final_df['Home_FT_Rate'].astype(float) - final_df['Away_FT_Rate'].astype(float)
    
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
        'Home_Point_Diff',
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
    print(f"Saving {len(final_df)} games to {output_file}")
    final_df.to_csv(output_file, index=False)
    
    return final_df

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Combine NBA four factors data into a single reporting dataset')
    
    # Add arguments
    parser.add_argument('--four-factors-dir', '-f', required=True, 
                        help='Directory containing four factors CSV files')
    parser.add_argument('--schedule', '-s', required=True,
                        help='Path to NBA schedule CSV file')
    parser.add_argument('--output', '-o', default='nba_four_factors_report.csv',
                        help='Output file path (default: nba_four_factors_report.csv)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Combine data
    combine_four_factors_data(args.four_factors_dir, args.schedule, args.output)
    
    print("\nData combination completed!")

if __name__ == "__main__":
    main()
