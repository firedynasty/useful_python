import os
import sys
import glob
import argparse
import docx
from datetime import datetime

# Import pdfminer.six for PDF extraction
from pdfminer.high_level import extract_text as pm_extract_text

def extract_text(file_path):
    """Extract text from PDF, DOCX, TXT or MD files"""
    text = ""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            # Use pdfminer.six for PDF extraction
            text = pm_extract_text(file_path)
        
        elif file_ext == '.docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        
        elif file_ext in ['.txt', '.md']:
            # Handle both text and markdown files the same way
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                
        else:  # Try as plain text for other extensions
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                
        return text
    except Exception as e:
        print(f"Error extracting text from {file_path}: {str(e)}")
        return ""

def process_folder(folder_path, output_file, prompt_file=None, file_types=None, recursive=False):
    """Process all documents in a folder and extract their contents to a single file"""
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    # Default file types to process
    if not file_types:
        file_types = ["pdf", "docx", "txt", "md"]
        
    # Find all matching files
    files = []
    
    if recursive:
        # Walk through all subfolders
        for root, dirs, filenames in os.walk(folder_path):
            for ext in file_types:
                pattern = os.path.join(root, f"*.{ext}")
                files.extend(glob.glob(pattern))
    else:
        # Just process the top-level folder
        for ext in file_types:
            pattern = os.path.join(folder_path, f"*.{ext}")
            files.extend(glob.glob(pattern))
        
    if not files:
        print(f"No supported documents found in '{folder_path}'.")
        return
        
    print(f"Found {len(files)} document(s) to process.")
    
    # Create or open output file
    with open(output_file, 'w', encoding='utf-8') as out_file:
        # Add the custom template text at the beginning
        template = """I have extracted text from multiple documents using the following format:
///[filename]
'''
[document content]
'''
Please analyze each document and provide a concise summary for each one. For each file:

Identify the main topic or purpose
Summarize the key points, arguments, or information
Note any important conclusions or takeaways
Keep summaries to 3-5 sentences each

Please format your response as:
[filename]
[summary]
And separate each file summary with a divider line."""
        
        out_file.write(template + "\n\n")
        
        # Start with prompt text if provided
        if prompt_file and os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_text = f.read()
                out_file.write(prompt_text)
                
                # Add separator between prompt and documents
                out_file.write("\n\n")
            except Exception as e:
                print(f"Error reading prompt file: {str(e)}")
        
        # Process each file
        for file_path in files:
            filename = os.path.basename(file_path)
            print(f"Processing: {filename}")
            
            # Extract text
            text = extract_text(file_path)
            if not text:
                print(f"Skipping {filename} - could not extract text.")
                continue
            
            # Include relative path in output if recursive
            if recursive:
                rel_path = os.path.relpath(file_path, folder_path)
                identifier = rel_path
            else:
                identifier = filename
                
            # Write file separator and filename with triple quotes
            out_file.write(f"///{identifier}\n'''\n")
            
            # Write extracted text
            out_file.write(text)
            
            # Add closing triple quotes and spacing between files
            out_file.write("\n'''\n\n")
    
    print(f"All content has been saved to: {output_file}")
    
    # Copy to clipboard if requested
    return output_file

def copy_to_clipboard(file_path):
    """Copy the contents of a file to clipboard using pbcopy"""
    try:
        # Check if running on macOS (where pbcopy is available)
        if sys.platform == 'darwin':
            os.system(f"cat {file_path} | pbcopy")
            print(f"Content copied to clipboard")
        else:
            print("Clipboard copy is only supported on macOS")
    except Exception as e:
        print(f"Error copying to clipboard: {str(e)}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract content from all files in a folder')
    parser.add_argument('folder', help='Folder containing documents to extract content from')
    parser.add_argument('-o', '--output', default='output.txt', 
                        help='Output file (default: output.txt)')
    parser.add_argument('-t', '--types', nargs='+', default=['pdf', 'docx', 'txt', 'md'],
                        help='File types to process (default: pdf docx txt md)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process subfolders recursively')
    parser.add_argument('-p', '--prompt', 
                        help='Text file containing prompt to prepend to the output')
    
    parser.add_argument('--no-clipboard', action='store_true',
                        help='Disable automatic copying to clipboard')
    
    args = parser.parse_args()
    
    # Process folder
    output_file = process_folder(args.folder, args.output, args.prompt, args.types, args.recursive)
    
    # Copy to clipboard by default unless explicitly disabled
    if not args.no_clipboard and output_file:
        copy_to_clipboard(output_file)
    
if __name__ == "__main__":
    main()
