import sys
import argparse
import csv
import json
import os

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Convert CSV files to JSON format')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('files', metavar='FILE', type=str, nargs='*', default=[],
                       help='CSV files to process')
    group.add_argument('-d', '--directory', type=str,
                       help='Directory containing CSV files to process')
    parser.add_argument('-o', '--output', type=str, default='output.js',
                        help='Output JavaScript file name (default: output.js)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize the result dictionary
    result = {}
    
    # Get list of files to process
    files_to_process = []
    if args.directory:
        # Process all CSV files in the specified directory
        if not os.path.isdir(args.directory):
            print(f"Error: {args.directory} is not a valid directory")
            sys.exit(1)
        for filename in os.listdir(args.directory):
            if filename.lower().endswith('.csv'):
                files_to_process.append(os.path.join(args.directory, filename))
        if not files_to_process:
            print(f"Warning: No CSV files found in {args.directory}")
            sys.exit(0)
    else:
        files_to_process = args.files
    
    # Process each file
    for i, file_path in enumerate(files_to_process, 1):
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Create a title by replacing underscores with spaces and capitalizing words
        title = base_name.replace('_', ' ').title()
        
        # Read CSV content
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Convert CSV to string representation
                rows = list(reader)
                if not rows:
                    print(f"Warning: {file_path} is empty")
                    continue
                    
                content = ""
                for row in rows:
                    content += ','.join(row) + '\n'
                content = content.rstrip('\n')  # Remove trailing newline
                
                # Add to result
                result[str(i)] = {
                    "title": title,
                    "content": content
                }
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Write the result to a JavaScript file
    with open(args.output, 'w', encoding='utf-8') as outfile:
        outfile.write(f"const json_file_variable = {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"Output written to {args.output}")

if __name__ == "__main__":
    main()