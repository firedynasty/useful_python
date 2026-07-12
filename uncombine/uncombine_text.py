#!/usr/bin/env python3
"""
Script to split a combined text file into separate .txt files
based on the delimiter '###\n###'
"""

import os
import re

def clean_filename(filename):
    """Clean and validate filename"""
    # Remove file extension if present in the first line
    filename = filename.replace('.txt', '').replace('(txt)', '').strip()
    # Take only the first part before any special characters or spaces
    filename = filename.split()[0] if filename.split() else filename
    # Remove any remaining parentheses
    filename = re.sub(r'[()]', '', filename)
    return filename

def split_combined_file(input_file, output_dir='output_files'):
    """
    Split a combined text file into separate files based on delimiter
    
    Args:
        input_file: Path to the combined text file
        output_dir: Directory to save the split files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the entire file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by the delimiter pattern
    sections = content.split('###\n###')
    
    # Process each section
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
            
        # Split into lines
        lines = section.split('\n')
        if not lines:
            continue
            
        # Get the filename from the first line
        first_line = lines[0].strip()
        
        # Extract filename - handle different formats
        if '(' in first_line and 'txt' in first_line:
            # Format like "1main_links (txt)" or "2_links (txt)"
            filename = first_line.split('(')[0].strip()
        else:
            # Format like "achilles (txt)" or just "basketball"
            filename = first_line.split(';')[0].strip()
        
        filename = clean_filename(filename)
        
        # If filename is empty or too short, use a default
        if len(filename) < 2:
            filename = f"file_{i+1}"
        
        # Ensure .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Get the content (everything after the first line)
        content_lines = lines[1:] if len(lines) > 1 else []
        file_content = '\n'.join(content_lines).strip()
        
        # Save the file
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"Created: {output_path}")
        print(f"  First few characters: {file_content[:100]}...")
        print()

# Example content based on your provided text
example_content = """1main_links (txt)
https://codepen.io/Groundedelectron/pen/RwdZzNE/df4ad16309ab274b85db2e7261a09383; Pen Link
###
###
2_links (txt)
https://stanleysjourney.com/image_gallery/basketball/spin_move1/; spin move(image_gallery/basketball/spin_move1/)
https://stanleysjourney.com/video_gallery/basketball/players_at_gym; players_at_gym / video gallery (/basketball/players..)
###
###
4_out_basketball (txt)
basketball
so what it is, is this that you keep low and stay low with your hands out you can control the ball better move the ball behind your palm 
so pretty much it's this, and then get pressure you can pass it out behind you always, 
https://www.youtube.com/watch?v=BSjpPg7qJvY; 4 Out motion offense
###
###
achilles (txt)
Absolutely! Here's your updated summary with key preventative tips included:
---
## Notes: Upright Positioning & Achilles Injury Prevention in Basketball
### **Positioning"""

def main():
    import sys
    
    # Check if a file was provided as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        # Check if file exists
        if not os.path.exists(input_file):
            print(f"Error: File '{input_file}' not found!")
            return
    else:
        # Use the example content for demonstration
        input_file = 'combined.txt'
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(example_content)
        print("No input file provided. Using example content for demonstration.")
    
    # Set output directory
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'output_files'
    
    print(f"Processing: {input_file}")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    # Split the file
    split_combined_file(input_file, output_dir)
    
    print("-" * 50)
    print("File splitting complete!")
    print(f"\nAll files saved to: {os.path.abspath(output_dir)}/")
    print("\nUsage:")
    print("  python split_text_files.py <input_file> [output_directory]")
    print("  Example: python split_text_files.py combined.txt my_output_folder")

if __name__ == "__main__":
    main()
