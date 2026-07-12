import os
import argparse
import sys

def extract_code_file(file_path, output_file="askAI1.txt"):
    """
    Extract code from a file and append it to the specified output file with a header.
    
    Args:
        file_path (str): Path to the code file (.py, .js, .html, etc.)
        output_file (str): Path to the output file (default: askAI1.txt)
    """
    try:
        # Check if input file exists
        if not os.path.isfile(file_path):
            print(f"Error: File '{file_path}' not found.")
            return False
        
        # Get absolute path for better identification
        abs_path = os.path.abspath(file_path)
        
        # Read the content of the input file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create header based on file type
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.py':
            header = f"# {abs_path}\n\n"
        elif file_extension == '.js':
            header = f"// {abs_path}\n\n"
        elif file_extension == '.html':
            header = f"<!-- {abs_path} -->\n\n"
        else:
            header = f"// {abs_path}\n\n"
        
        # Append content to output file
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(header)
            f.write(content)
            f.write("\n\n")
        
        print(f"Successfully appended code from '{file_path}' to '{output_file}'")
        return True
    
    except Exception as e:
        print(f"Error processing '{file_path}': {str(e)}")
        return False

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Extract code from files and append to a single file.')
    parser.add_argument('file_paths', nargs='+', help='Path(s) to code file(s) to extract')
    parser.add_argument('-o', '--output', default='askAI1.txt', 
                      help='Output file to append code to (default: askAI1.txt)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if output file exists and prompt for clearing
    output_file = args.output
    if os.path.exists(output_file):
        while True:
            response = input(f"The file '{output_file}' already exists. Do you want to clear it before appending? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                # Clear the file by opening it in write mode
                with open(output_file, 'w') as f:
                    pass
                print(f"Cleared the contents of '{output_file}'")
                break
            elif response in ['no', 'n']:
                print(f"Will append to the existing '{output_file}'")
                break
            else:
                print("Please enter 'yes' or 'no'")
    
    # Process each file
    success_count = 0
    for file_path in args.file_paths:
        if extract_code_file(file_path, output_file):
            success_count += 1
    
    # Print summary
    print(f"Processing complete. Processed {success_count} of {len(args.file_paths)} files.")

if __name__ == "__main__":
    main()