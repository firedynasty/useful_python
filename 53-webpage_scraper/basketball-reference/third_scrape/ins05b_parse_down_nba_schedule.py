#the argument is python duplicate_checker.py schedule_file.csv report_file.csv
# NBA Schedule and Report Comparison Script
# report_file.csv is data/converted_report.csv

import pandas as pd
import datetime

def check_duplicates_and_missing_games(schedule_file, report_file):
    """
    Compare games between NBA schedule and converted report files.
    Identifies duplicates and missing games between the two files.
    
    Args:
        schedule_file (str): Path to NBA schedule CSV file
        report_file (str): Path to converted report CSV file
        
    Returns:
        dict: Results of the comparison
    """
    # Define team mapping (full names to abbreviations)
    team_mapping = {
        'Atlanta Hawks': 'ATL',
        'Boston Celtics': 'BOS',
        'Brooklyn Nets': 'BKN',
        'Charlotte Hornets': 'CHO',
        'Chicago Bulls': 'CHI',
        'Cleveland Cavaliers': 'CLE',
        'Dallas Mavericks': 'DAL',
        'Denver Nuggets': 'DEN',
        'Detroit Pistons': 'DET',
        'Golden State Warriors': 'GSW',
        'Houston Rockets': 'HOU',
        'Indiana Pacers': 'IND',
        'Los Angeles Clippers': 'LAC',
        'Los Angeles Lakers': 'LAL',
        'Memphis Grizzlies': 'MEM',
        'Miami Heat': 'MIA',
        'Milwaukee Bucks': 'MIL',
        'Minnesota Timberwolves': 'MIN',
        'New Orleans Pelicans': 'NOP',
        'New York Knicks': 'NYK',
        'Oklahoma City Thunder': 'OKC',
        'Orlando Magic': 'ORL',
        'Philadelphia 76ers': 'PHI',
        'Phoenix Suns': 'PHX',
        'Portland Trail Blazers': 'POR',
        'Sacramento Kings': 'SAC',
        'San Antonio Spurs': 'SAS',
        'Toronto Raptors': 'TOR',
        'Utah Jazz': 'UTA',
        'Washington Wizards': 'WAS'
    }
    
    # Load both files
    print(f"Loading schedule data from {schedule_file}")
    schedule_df = pd.read_csv(schedule_file)
    
    print(f"Loading report data from {report_file}")
    report_df = pd.read_csv(report_file)
    
    # Print initial counts
    print(f"Schedule file has {len(schedule_df)} games")
    print(f"Report file has {len(report_df)} games")
    
    # Convert schedule dates to YYYYMMDD format
    def convert_schedule_date(date_str):
        try:
            # Parse date like "Sat, Mar 1, 2025"
            dt = pd.to_datetime(date_str, format='%a, %b %d, %Y')
            return dt.strftime('%Y%m%d')
        except:
            return None
    
    # Convert report dates to YYYYMMDD format
    def convert_report_date(date_str):
        try:
            # Parse date like "2025-03-01"
            dt = pd.to_datetime(date_str)
            return dt.strftime('%Y%m%d')
        except:
            return None
    
    # Map team names to abbreviations for schedule file
    def map_team_to_abbrev(team_name):
        return team_mapping.get(team_name, team_name)
    
    # Create game_id in schedule_df: YYYYMMDD_VISITOR_HOME
    schedule_df['date_yyyymmdd'] = schedule_df['Date'].apply(convert_schedule_date)
    schedule_df['visitor_abbrev'] = schedule_df['Visitor_Team'].apply(map_team_to_abbrev)
    schedule_df['home_abbrev'] = schedule_df['Home_Team'].apply(map_team_to_abbrev)
    schedule_df['game_id'] = schedule_df['date_yyyymmdd'] + '_' + schedule_df['visitor_abbrev'] + '_' + schedule_df['home_abbrev']
    
    # Create game_id in report_df: YYYYMMDD_VISITOR_HOME
    # For the report file, the team names are already in abbreviated form
    report_df['date_yyyymmdd'] = report_df['date'].apply(convert_report_date)
    report_df['game_id'] = report_df['date_yyyymmdd'] + '_' + report_df['visitor_team'] + '_' + report_df['home_team']
    
    # Find games in schedule but not in report
    schedule_only = schedule_df[~schedule_df['game_id'].isin(report_df['game_id'])]
    
    # Find games in report but not in schedule
    report_only = report_df[~report_df['game_id'].isin(schedule_df['game_id'])]
    
    # Print results
    print(f"\nGames in schedule but not in report: {len(schedule_only)}")
    print(f"Games in report but not in schedule: {len(report_only)}")
    
    # Check for invalid game_ids (possible date parsing failures)
    invalid_schedule_ids = schedule_df[schedule_df['date_yyyymmdd'].isna()]['Date'].tolist()
    invalid_report_ids = report_df[report_df['date_yyyymmdd'].isna()]['date'].tolist()
    
    print(f"\nInvalid dates in schedule: {len(invalid_schedule_ids)}")
    if invalid_schedule_ids:
        print(f"Sample invalid schedule dates: {invalid_schedule_ids[:5]}")
        
    print(f"Invalid dates in report: {len(invalid_report_ids)}")
    if invalid_report_ids:
        print(f"Sample invalid report dates: {invalid_report_ids[:5]}")
    
    # Print examples of missing games
    if len(schedule_only) > 0:
        print("\nSample games in schedule but not in report:")
        sample_schedule_only = schedule_only[['Date', 'Visitor_Team', 'Home_Team', 'game_id']].head()
        print(sample_schedule_only.to_string())
    
    if len(report_only) > 0:
        print("\nSample games in report but not in schedule:")
        sample_report_only = report_only[['date', 'visitor_team', 'home_team', 'game_id']].head()
        print(sample_report_only.to_string())
    
    # Check for games with box score URLs but not in report
    playable_games = schedule_df[schedule_df['Box_Score_URL'].notna() & (schedule_df['Box_Score_URL'] != '')]
    playable_games_missing = playable_games[~playable_games['game_id'].isin(report_df['game_id'])]
    
    print(f"\nGames with box score URLs but not in report: {len(playable_games_missing)}")
    
    if len(playable_games_missing) > 0:
        print("\nSample games with box score URLs missing from report:")
        sample_missing = playable_games_missing[['Date', 'Visitor_Team', 'Home_Team', 'game_id', 'Box_Score_URL']].head()
        print(sample_missing.to_string())
    
    # Output to CSV files for further analysis
    import os
    current_dir = os.getcwd()
    
    # Define output files
    schedule_only_file = 'games_in_schedule_only.csv'
    report_only_file = 'games_in_report_only.csv'
    playable_missing_file = 'games_with_boxscore_missing_from_report.csv'
    
    # Save files
    schedule_only.to_csv(schedule_only_file, index=False)
    report_only.to_csv(report_only_file, index=False)
    playable_games_missing.to_csv(playable_missing_file, index=False)
    
    # Get full paths
    schedule_only_path = os.path.join(current_dir, schedule_only_file)
    report_only_path = os.path.join(current_dir, report_only_file)
    playable_missing_path = os.path.join(current_dir, playable_missing_file)
    
    # Return results as a dictionary
    return {
        'schedule_total': len(schedule_df),
        'report_total': len(report_df),
        'in_schedule_only': len(schedule_only),
        'in_report_only': len(report_only),
        'invalid_schedule_dates': len(invalid_schedule_ids),
        'invalid_report_dates': len(invalid_report_ids),
        'playable_games_missing': len(playable_games_missing),
        'schedule_only_path': schedule_only_path,
        'report_only_path': report_only_path,
        'playable_missing_path': playable_missing_path
    }

# Example usage:
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python duplicate_checker.py schedule_file.csv report_file.csv")
        sys.exit(1)
    
    schedule_file = sys.argv[1]
    report_file = sys.argv[2]
    
    results = check_duplicates_and_missing_games(schedule_file, report_file)
    
    print("\nSummary:")
    print(f"Total games in schedule: {results['schedule_total']}")
    print(f"Total games in report: {results['report_total']}")
    print(f"Games only in schedule: {results['in_schedule_only']}")
    print(f"Games only in report: {results['in_report_only']}")
    print(f"Games with box scores missing from report: {results['playable_games_missing']}")
    
    print("\nOutput Files:")
    print(f"1. Games in schedule only: {results['schedule_only_path']}")
    print(f"2. Games in report only: {results['report_only_path']}")
    print(f"3. Games with box scores missing from report: {results['playable_missing_path']}")
