from pathlib import Path

def list_and_read_files():
    # List files in current directory
    current_dir = Path.cwd()
    files = list(current_dir.iterdir())
    
    # Filter out just the files (no directories)
    files = [file for file in files if file.is_file()]
    
    # Create a numbered list of files
    for i, file in enumerate(files, 1):
        print(f"{i}. {file.name}")
    
    # Get user input for which file to read
    try:
        choice = int(input("\nEnter the number of the file you want to read: "))
        if 1 <= choice <= len(files):
            selected_file = files[choice-1]
            
            print(f"\nReading {selected_file.name}:")
            
            # Determine how to read based on file extension
            if selected_file.suffix in ['.txt', '.md', '.py', '.html', '.css', '.js']:
                # Text files
                content = selected_file.read_text()
                print(content)
            else:
                print(f"File type {selected_file.suffix} might be binary. Displaying first 100 bytes as text:")
                try:
                    with open(selected_file, 'r') as f:
                        print(f.read(100) + "...")
                except UnicodeDecodeError:
                    print("This appears to be a binary file and cannot be displayed as text.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")

if __name__ == "__main__":
    list_and_read_files()
