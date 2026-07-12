#!/usr/bin/env python3
"""
Script to remove asterisks from formatted Bible chapter references.
Converts **Chapter X**: verses to Chapter X: verses
"""

import re
import sys

def remove_asterisks(text):
    """
    Remove asterisks from chapter references.
    
    Args:
        text (str): Input text with asterisks
        
    Returns:
        str: Text with asterisks removed
    """
    # Pattern to match **Chapter X**: and replace with Chapter X:
    # This handles the bold markdown formatting
    pattern = r'\*\*Chapter\s+(\d+)\*\*:'
    
    # Replace with Chapter X: (without asterisks)
    cleaned = re.sub(pattern, r'Chapter \1:', text)
    
    # Also remove any remaining standalone asterisks that might be around verse numbers
    # This is a safety measure for any other asterisk formatting
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    
    return cleaned

def process_file(input_file, output_file=None):
    """
    Process a file to remove asterisks from chapter references.
    
    Args:
        input_file (str): Path to input file
        output_file (str): Path to output file (optional)
    """
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        cleaned = remove_asterisks(content)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(cleaned)
            print(f"Cleaned text written to {output_file}")
        else:
            print(cleaned)
            
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
    except Exception as e:
        print(f"Error: {e}")

def process_text_directly(text):
    """
    Process text directly without file I/O.
    
    Args:
        text (str): Input text with asterisks
        
    Returns:
        str: Cleaned text
    """
    return remove_asterisks(text)

def main():
    # Example text from Ecclesiastes
    sample_text = """Here are the minimal key verses for each chapter of Ecclesiastes:

**Chapter 1**: 2, 14
**Chapter 2**: 11, 24-25
**Chapter 3**: 1, 11, 14
**Chapter 4**: 9-10
**Chapter 5**: 2, 10
**Chapter 6**: 12
**Chapter 7**: 20, 29
**Chapter 8**: 15, 17
**Chapter 9**: 10, 11
**Chapter 10**: 1
**Chapter 11**: 9
**Chapter 12**: 1, 13-14"""
    
    if len(sys.argv) > 1:
        # Process file from command line argument
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        process_file(input_file, output_file)
    else:
        # Process the sample text
        print("Original text with asterisks:")
        print("=" * 50)
        print(sample_text)
        print("=" * 50)
        print("\nCleaned text without asterisks:")
        print("=" * 50)
        cleaned = remove_asterisks(sample_text)
        print(cleaned)
        print("=" * 50)
        print("\nTo process a file, run:")
        print("  python remove_asterisks.py input.txt [output.txt]")

if __name__ == "__main__":
    main()
