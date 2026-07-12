#!/usr/bin/env python3
"""
Convert HTML to text while preserving formatting.
Particularly suited for Shakespeare texts from MIT.
"""

from bs4 import BeautifulSoup
import re
import sys

def html_to_text_preserve_format(html_file_path, output_file_path=None):
    """
    Convert HTML to text, preserving the formatting of Shakespeare plays.
    
    Args:
        html_file_path: Path to input HTML file
        output_file_path: Path to output text file (optional)
    """
    
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Preserve line breaks and spacing
    # Split by lines and clean up
    lines = text.split('\n')
    
    # Remove excessive blank lines (more than 2 consecutive)
    cleaned_lines = []
    blank_count = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_count += 1
            if blank_count <= 2:  # Allow up to 2 blank lines
                cleaned_lines.append('')
        else:
            blank_count = 0
            # Preserve indentation for dialogue
            if line.startswith('    '):  # Likely dialogue
                cleaned_lines.append('    ' + stripped)
            elif line.startswith('  '):  # Likely stage directions or character names
                cleaned_lines.append('  ' + stripped)
            else:
                cleaned_lines.append(stripped)
    
    # Join the lines
    formatted_text = '\n'.join(cleaned_lines)
    
    # Clean up any remaining issues
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)  # Max 2 newlines
    formatted_text = formatted_text.strip()
    
    # Save to file if output path provided
    if output_file_path:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(formatted_text)
        print(f"Text saved to {output_file_path}")
    else:
        # If no output file specified, create one with .txt extension
        output_file_path = html_file_path.replace('.html', '.txt')
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(formatted_text)
        print(f"Text saved to {output_file_path}")
    
    return formatted_text

def main():
    if len(sys.argv) < 2:
        print("Usage: python html_to_text_converter.py <input.html> [output.txt]")
        print("\nExample:")
        print("  python html_to_text_converter.py tempest.html tempest.txt")
        print("\nIf output file is not specified, it will create one with .txt extension")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        html_to_text_preserve_format(input_file, output_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
