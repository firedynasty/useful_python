import pandas as pd
import argparse
import os
import math

def split_csv(input_file, output_prefix=None, rows_per_file=30):
    """
    Split a CSV file into multiple files with specified number of rows per file.
    
    Args:
        input_file (str): Path to the input CSV file
        output_prefix (str, optional): Prefix for output files. If None, uses input filename
        rows_per_file (int): Number of rows per output file (default: 30)
    """
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Calculate the number of output files needed
    total_rows = len(df)
    num_files = math.ceil(total_rows / rows_per_file)
    
    # Create output directory if it doesn't exist
    if output_prefix is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_prefix = f"{base_name}_split"
    
    # Split the dataframe and save to separate CSV files
    for i in range(num_files):
        start_row = i * rows_per_file
        end_row = min((i + 1) * rows_per_file, total_rows)
        
        # Extract the chunk
        chunk = df.iloc[start_row:end_row]
        
        # Save the chunk to a CSV file
        output_file = f"{output_prefix}_{i+1}.csv"
        chunk.to_csv(output_file, index=False)
        print(f"Created file {output_file} with {len(chunk)} rows")

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Split a CSV file into smaller files')
    parser.add_argument('input_file', help='Path to the input CSV file')
    parser.add_argument('--output-prefix', help='Prefix for output files')
    parser.add_argument('--rows', type=int, default=30, help='Number of rows per output file (default: 30)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Split the CSV file
    split_csv(args.input_file, args.output_prefix, args.rows)
