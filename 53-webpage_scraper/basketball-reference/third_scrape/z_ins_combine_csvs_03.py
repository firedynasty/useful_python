#!/usr/bin/env python3
import pandas as pd
import argparse
import os
import sys
from datetime import datetime

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Concatenate multiple CSV files with the same columns and sort by date.')
    parser.add_argument('files', nargs='+', help='Input CSV files to concatenate')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file name')
    
    args = parser.parse_args()
    
    # Check if all input files exist
    for file in args.files:
        if not os.path.exists(file):
            print(f"Error: File {file} does not exist.", file=sys.stderr)
            sys.exit(1)
    
    # List to store dataframes
    dataframes = []
    
    # Load dataframes from each CSV file
    for file in args.files:
        try:
            df = pd.read_csv(file)
            print(f"Read CSV file: {file} with shape {df.shape}")
            dataframes.append(df)
        
        except Exception as e:
            print(f"Error processing file {file}: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    if not dataframes:
        print("Error: No data found in the input files.", file=sys.stderr)
        sys.exit(1)
    
    # Concatenate all dataframes
    try:
        combined_df = pd.concat(dataframes, ignore_index=True)
        print(f"Successfully concatenated {len(dataframes)} CSV files with shape {combined_df.shape}")
        
        # Check if Game_Date_ISO column exists, if not create it from Date column
        if 'Game_Date_ISO' not in combined_df.columns and 'Date' in combined_df.columns:
            try:
                # Convert Date to datetime object
                combined_df['Date'] = pd.to_datetime(combined_df['Date'])
                
                # Create Game_Date_ISO column in YYYY-MM-DD format
                combined_df['Game_Date_ISO'] = combined_df['Date'].dt.strftime('%Y-%m-%d')
                
                print("Created Game_Date_ISO column from Date column")
            except Exception as e:
                print(f"Warning: Could not create Game_Date_ISO column: {str(e)}", file=sys.stderr)
        
        # Also check if lowercase 'date' column exists, if not create Game_Date_ISO from it
        elif 'Game_Date_ISO' not in combined_df.columns and 'date' in combined_df.columns:
            try:
                # Convert date to datetime object
                combined_df['date'] = pd.to_datetime(combined_df['date'])
                
                # Create Game_Date_ISO column in YYYY-MM-DD format
                combined_df['Game_Date_ISO'] = combined_df['date'].dt.strftime('%Y-%m-%d')
                
                print("Created Game_Date_ISO column from lowercase date column")
            except Exception as e:
                print(f"Warning: Could not create Game_Date_ISO column: {str(e)}", file=sys.stderr)
        
        # Sort by Game_Date_ISO if it exists
        if 'Game_Date_ISO' in combined_df.columns:
            combined_df = combined_df.sort_values(by='Game_Date_ISO')
            print("Data sorted by Game_Date_ISO column")
        # Otherwise sort by Date if it exists
        elif 'Date' in combined_df.columns:
            try:
                if not pd.api.types.is_datetime64_dtype(combined_df['Date']):
                    combined_df['Date'] = pd.to_datetime(combined_df['Date'])
                combined_df = combined_df.sort_values(by='Date')
                print("Data sorted by Date column")
            except:
                print("Warning: Could not convert Date column to datetime for sorting", file=sys.stderr)
        # Otherwise sort by lowercase date if it exists
        elif 'date' in combined_df.columns:
            try:
                if not pd.api.types.is_datetime64_dtype(combined_df['date']):
                    combined_df['date'] = pd.to_datetime(combined_df['date'])
                combined_df = combined_df.sort_values(by='date')
                print("Data sorted by lowercase date column")
            except:
                print("Warning: Could not convert lowercase date column to datetime for sorting", file=sys.stderr)
        else:
            print("Warning: No date column found for sorting", file=sys.stderr)
        
        # Write the result to a new CSV file
        combined_df.to_csv(args.output, index=False)
        print(f"Output written to {args.output}")
        
    except Exception as e:
        print(f"Error processing data: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()