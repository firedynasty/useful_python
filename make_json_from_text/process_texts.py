#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import csv
import re
import argparse

def extract_title_from_file(file_path):
    """Extract a title from the file content or file name."""
    file_name = os.path.basename(file_path)
    
    # Extract page number for elementary_chinese files
    if file_name.startswith("elementary_chinese_pg"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # Try to find a title in the content
        lines = content.split('\n')
        for line in lines:
            if '|' in line:
                # Extract the part after the pipe which typically contains the title
                title = line.split('|', 1)[1].strip()
                return f"Elementary Chinese ({file_name}) - {title}"
        
        # If no title found, use the file name
        page_num = file_name.replace("elementary_chinese_pg", "").replace(".txt", "")
        return f"Elementary Chinese (Page {page_num})"
    
    # For other files, just use the filename without extension
    base_name = os.path.splitext(file_name)[0]
    return f"{base_name} ({os.path.splitext(file_name)[1][1:]})"

def process_txt_file(file_path):
    """Process a text file and extract its content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Basic processing of content to make it more structured
    lines = content.split('\n')
    processed_lines = []
    
    # Simple formatting for elementary_chinese files to extract vocab
    in_vocab_section = False
    vocab_entries = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines with URLs or interactive elements
        if "http" in line or "interactive" in line:
            continue
            
        # Look for vocabulary sections
        if "Chinese" in line and "Pinyin" in line or "English" in line:
            in_vocab_section = True
            continue
            
        if in_vocab_section:
            # Try to extract vocabulary entries
            if re.match(r'^\s*\d+\s*$', line):  # Skip line numbers
                continue
                
            vocab_entries.append(line)
    
    # If we found vocab entries, format them
    if vocab_entries:
        return "\n".join(vocab_entries)
    
    # Otherwise return the content as is
    return content

def process_csv_file(file_path):
    """Process a CSV file and extract its content."""
    content_lines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:  # Skip empty rows
                    content_lines.append(",".join(row))
    except Exception as e:
        return f"Error reading CSV: {str(e)}"
        
    return "\n".join(content_lines)

def process_directory(texts_dir, output_path=None):
    """Process all text files in the given directory."""
    # Dictionary to store all processed files
    json_data = {}
    counter = 1
    
    # Process all .txt files
    txt_files = [f for f in os.listdir(texts_dir) if f.endswith('.txt')]
    
    # Custom sorting function to handle numeric page numbers correctly
    def extract_page_number(filename):
        match = re.search(r'pg(\d+)', filename)
        if match:
            # Convert to integer for proper numeric sorting
            return int(match.group(1))
        return filename
    
    for file_name in sorted(txt_files, key=extract_page_number):
        file_path = os.path.join(texts_dir, file_name)
        title = extract_title_from_file(file_path)
        content = process_txt_file(file_path)
        
        if content:  # Only add non-empty content
            json_data[str(counter)] = {
                "title": title,
                "content": content
            }
            counter += 1
    
    # Process all .csv files
    csv_files = [f for f in os.listdir(texts_dir) if f.endswith('.csv')]
    for file_name in sorted(csv_files, key=extract_page_number):
        file_path = os.path.join(texts_dir, file_name)
        title = extract_title_from_file(file_path)
        content = process_csv_file(file_path)
        
        if content:  # Only add non-empty content
            json_data[str(counter)] = {
                "title": title,
                "content": content
            }
            counter += 1
    
    # Output the JSON data
    output_js = f"const json_file_variable = {json.dumps(json_data, ensure_ascii=False, indent=2)}"
    
    # Determine output path
    if output_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, "vocabulary_data.js")
    
    # Save to a JS file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_js)
    
    print(f"Generated vocabulary data with {len(json_data)} entries to {output_path}")
    
    return json_data

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process Chinese text files into a JSON structure.')
    parser.add_argument('-i', '--input', default='./chinese_texts',
                        help='Directory containing the text files (default: ./chinese_texts)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output file path (default: ./vocabulary_data.js)')
    
    args = parser.parse_args()
    
    # Process the directory
    process_directory(args.input, args.output)

if __name__ == "__main__":
    main()