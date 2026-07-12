#!/usr/bin/env python3
"""
Extract lines from a file by line numbers and copy to clipboard.
Usage: 
  python grab_lines.py file.txt 500        # Get lines 1-500
  python grab_lines.py file.txt 500 1000   # Get lines 500-1000
"""

import sys
import os

def extract_lines(filename: str, start_line: int = 1, end_line: int = None) -> str:
    """Extract lines from file between start_line and end_line (inclusive)."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File '{filename}' not found")
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    
    # Validate line numbers
    if start_line < 1:
        start_line = 1
    if start_line > total_lines:
        raise ValueError(f"Start line {start_line} exceeds file length ({total_lines} lines)")
    
    if end_line is None:
        end_line = start_line
        start_line = 1
    elif end_line > total_lines:
        print(f"Warning: End line {end_line} exceeds file length. Using {total_lines} instead.")
        end_line = total_lines
    
    if start_line > end_line:
        raise ValueError(f"Start line ({start_line}) cannot be greater than end line ({end_line})")
    
    # Extract lines (convert to 0-based indexing)
    extracted_lines = lines[start_line-1:end_line]
    
    # Join lines into single string
    return ''.join(extracted_lines)

def copy_to_clipboard(text: str) -> bool:
    """Try to copy text to clipboard using various methods."""
    # Try pyperclip first
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass
    
    # Try pbcopy on macOS
    if sys.platform == "darwin":
        try:
            import subprocess
            subprocess.run("pbcopy", input=text.encode('utf-8'), check=True)
            return True
        except:
            pass
    
    # Try xclip on Linux
    if sys.platform.startswith("linux"):
        try:
            import subprocess
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode('utf-8'), check=True)
            return True
        except:
            pass
    
    # Try clip on Windows
    if sys.platform == "win32":
        try:
            import subprocess
            subprocess.run("clip", input=text.encode('utf-8'), check=True, shell=True)
            return True
        except:
            pass
    
    return False

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python grab_lines.py file.txt 500        # Get lines 1-500")
        print("  python grab_lines.py file.txt 500 1000   # Get lines 500-1000")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    try:
        if len(sys.argv) == 3:
            # Single number: get lines 1 to that number
            end_line = int(sys.argv[2])
            start_line = 1
        else:
            # Two numbers: get lines from start to end
            start_line = int(sys.argv[2])
            end_line = int(sys.argv[3])
        
        # Extract lines
        text = extract_lines(filename, start_line, end_line)
        
        # Display info
        with open(filename, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        
        if len(sys.argv) == 3:
            print(f"Extracting lines 1-{end_line} from '{filename}' ({total_lines} total lines)")
        else:
            print(f"Extracting lines {start_line}-{end_line} from '{filename}' ({total_lines} total lines)")
        
        # Calculate stats
        num_lines = end_line - start_line + 1
        num_chars = len(text)
        num_words = len(text.split())
        
        print(f"Extracted: {num_lines} lines, {num_words} words, {num_chars} characters")
        print("=" * 60)
        
        # Show preview (first and last few lines if long)
        preview_lines = text.splitlines()
        if len(preview_lines) <= 10:
            print(text)
        else:
            # Show first 3 and last 3 lines
            for i, line in enumerate(preview_lines[:3], start=start_line):
                print(f"{i:6d}  {line}")
            print("         ...")
            for i, line in enumerate(preview_lines[-3:], start=end_line-2):
                print(f"{i:6d}  {line}")
        
        print("=" * 60)
        
        # Try to copy to clipboard
        if copy_to_clipboard(text):
            print("\n✓ Text copied to clipboard")
        else:
            print("\n⚠ Could not copy to clipboard automatically")
            print("  Install pyperclip: pip install pyperclip")
            
            # Save to temp file as alternative
            temp_file = "grabbed_lines.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  Text saved to: {temp_file}")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
