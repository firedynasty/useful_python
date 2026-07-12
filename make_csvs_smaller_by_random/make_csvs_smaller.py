import pandas as pd
import numpy as np

def random_sample_csv(input_file, output_file=None, sample_size=1000, random_state=None):
    """
    Randomly samples rows from a CSV file.
    
    Parameters:
    -----------
    input_file : str
        Path to the input CSV file
    output_file : str, optional
        Path to save the sampled data. If None, only returns the sample without saving
    sample_size : int, default 1000
        Number of rows to randomly sample
    random_state : int, optional
        Seed for random number generator for reproducibility
    
    Returns:
    --------
    pandas.DataFrame
        The randomly sampled data
    """
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Check if we're asking for more rows than exist in the file
    actual_sample_size = min(sample_size, len(df))
    if actual_sample_size < sample_size:
        print(f"Warning: CSV only has {len(df)} rows. Sampling all rows.")
    
    # Take a random sample
    sampled_df = df.sample(n=actual_sample_size, random_state=random_state)
    
    # Save to output file if specified
    if output_file:
        sampled_df.to_csv(output_file, index=False)
        print(f"Sampled data saved to {output_file}")
    
    return sampled_df

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Randomly sample rows from a CSV file")
    parser.add_argument("input_file", help="Path to the input CSV file")
    parser.add_argument("--output_file", "-o", help="Path to save the sampled data")
    parser.add_argument("--sample_size", "-n", type=int, default=1000, 
                        help="Number of rows to randomly sample (default: 1000)")
    parser.add_argument("--seed", "-s", type=int, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    sampled_data = random_sample_csv(
        args.input_file, 
        args.output_file, 
        args.sample_size,
        args.seed
    )
    
    # Print the shape of the sampled data
    print(f"Randomly sampled {sampled_data.shape[0]} rows and {sampled_data.shape[1]} columns")
