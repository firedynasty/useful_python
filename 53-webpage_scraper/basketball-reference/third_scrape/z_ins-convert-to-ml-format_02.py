import pandas as pd
import argparse

def convert_to_ml_format(input_file, output_file):
    """
    Convert the detailed nba_report.csv format to the simpler format used by the ML model.
    Also converts full team names to abbreviations.
    
    Args:
        input_file (str): Path to the input CSV file (nba_report.csv format)
        output_file (str): Path to save the converted CSV file
    """
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    print(f"Converting {len(df)} games to ML format...")
    
    # Create a new dataframe with the ML model's expected structure
    ml_data = pd.DataFrame()
    
    # Map the columns to match nba_games_stats_copy.csv format
    ml_data['date'] = df['Game_Date_ISO']
    ml_data['visitor_team'] = df['Away_Team_Name'].apply(team_name_to_abbr)
    ml_data['visitor_score'] = df['Away_Score']
    ml_data['home_team'] = df['Home_Team_Name'].apply(team_name_to_abbr)
    ml_data['home_score'] = df['Home_Score']
    
    # Use Game_Pace for both home_pace and visitor_pace as requested
    ml_data['visitor_pace'] = df['Game_Pace']
    ml_data['home_pace'] = df['Game_Pace']
    
    # Four Factors metrics
    ml_data['visitor_efg'] = df['Away_eFG_PCT']
    ml_data['visitor_tov_pct'] = df['Away_TOV_PCT']
    ml_data['visitor_orb_pct'] = df['Away_ORB_PCT']
    ml_data['visitor_ft_rate'] = df['Away_FT_Rate']
    ml_data['visitor_ortg'] = df['Away_ORtg']
    
    ml_data['home_efg'] = df['Home_eFG_PCT']
    ml_data['home_tov_pct'] = df['Home_TOV_PCT']
    ml_data['home_orb_pct'] = df['Home_ORB_PCT']
    ml_data['home_ft_rate'] = df['Home_FT_Rate']
    ml_data['home_ortg'] = df['Home_ORtg']
    
    # Win indicator
    ml_data['home_win'] = df['Home_Won_Binary']
    
    # Save to CSV
    print(f"Saving {len(ml_data)} games to {output_file}")
    ml_data.to_csv(output_file, index=False)
    
    return ml_data

def team_name_to_abbr(full_name):
    """
    Convert a full team name to its abbreviation.
    """
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
    
    # Return the abbreviation if found, otherwise return the original name
    return team_mapping.get(full_name, full_name)

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Convert NBA four factors data to ML format')
    
    # Add arguments
    parser.add_argument('--input', '-i', required=True, 
                        help='Input file path (nba_report.csv format)')
    parser.add_argument('--output', '-o', default='nba_games_stats.csv',
                        help='Output file path (default: nba_games_stats.csv)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Convert data
    convert_to_ml_format(args.input, args.output)
    
    print("\nData conversion completed!")

if __name__ == "__main__":
    main()
