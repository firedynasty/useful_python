#!/usr/bin/env python3
"""
Script to format Bible chapter references with line breaks.
Takes text with chapters on one line and outputs each chapter on a new line.
"""

import re
import sys

def format_chapters_with_breaks(text):
    """
    Takes text with chapter references and formats each chapter on a new line.
    
    Args:
        text (str): Input text with chapter references
        
    Returns:
        str: Formatted text with each chapter on a new line
    """
    # Pattern to match "Chapter X: verse-ranges" or "**Chapter X**: verse-ranges"
    # This pattern captures:
    # - Optional markdown bold (**) before/after Chapter
    # - Chapter and number
    # - The verse ranges after the colon
    # - Stops at the next "Chapter" or end of string
    pattern = r'(\*{0,2}Chapter\s+\d+\*{0,2}:\s+[\d\s,\-]+?)(?=\s+\*{0,2}Chapter|\s*$)'
    
    # Find all matches
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Join with newlines
    formatted = '\n'.join(match.strip() for match in matches)
    
    return formatted

def process_file(input_file, output_file=None):
    """
    Process a file containing chapter references.
    
    Args:
        input_file (str): Path to input file
        output_file (str): Path to output file (optional)
    """
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        formatted = format_chapters_with_breaks(content)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(formatted)
            print(f"Formatted text written to {output_file}")
        else:
            print(formatted)
            
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Example text from Numbers
    sample_text = """Here are the minimal key verses for each chapter in the book of Numbers:
Chapter 1: 1-3, 44-46 Chapter 2: 1-2, 32-34 Chapter 3: 1-3, 11-13, 44-51 Chapter 4: 1-3, 46-49 Chapter 5: 1-4, 11-15, 29-31 Chapter 6: 1-8, 22-27 Chapter 7: 1-3, 84-89 Chapter 8: 1-4, 23-26 Chapter 9: 1-5, 15-23 Chapter 10: 11-13, 29-36 Chapter 11: 1-3, 4-6, 16-17, 24-25, 31-35 Chapter 12: 1-3, 9-15 Chapter 13: 1-3, 17-20, 25-33 Chapter 14: 1-4, 10-12, 20-24, 26-35 Chapter 15: 1-2, 32-36, 37-41 Chapter 16: 1-3, 19-22, 28-35, 41-50 Chapter 17: 1-11 Chapter 18: 1-7, 20-24 Chapter 19: 1-10 Chapter 20: 1-13, 22-29 Chapter 21: 4-9, 21-35 Chapter 22: 1-6, 21-35 Chapter 23: 7-10, 18-24 Chapter 24: 2-9, 15-19 Chapter 25: 1-9, 10-13 Chapter 26: 1-4, 51, 63-65 Chapter 27: 1-11, 12-23 Chapter 28: 1-2 Chapter 29: 1, 7, 12, 35 Chapter 30: 1-2 Chapter 31: 1-12, 25-54 Chapter 32: 1-5, 16-27, 33 Chapter 33: 1-3, 50-56 Chapter 34: 1-2, 13-15 Chapter 35: 1-8, 9-15, 25, 33-34 Chapter 36: 1-9"""
    
    if len(sys.argv) > 1:
        # Process file from command line argument
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        process_file(input_file, output_file)
    else:
        # Process the sample text
        print("Processing sample text from Numbers:\n")
        print("=" * 50)
        formatted = format_chapters_with_breaks(sample_text)
        print(formatted)
        print("=" * 50)
        print("\nTo process a file, run:")
        print("  python format_chapters.py input.txt [output.txt]")

if __name__ == "__main__":
    main()
