#!/usr/bin/env python3

import pandas as pd
import argparse
import os
import sys

def clean_nba_schedule(input_file):
    """
    Load NBA schedule CSV, drop rows with empty Box_Score_URL, and save the result.
    
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

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Clean NBA schedule by removing rows with empty Box_Score_URL')
    parser.add_argument('input_file', help='Input CSV file to process')
    
    args = parser.parse_args()
    
    # Run the function with provided arguments
    clean_nba_schedule(args.input_file)