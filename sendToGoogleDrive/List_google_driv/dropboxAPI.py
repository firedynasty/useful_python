#!/usr/bin/env python3
"""
Simple Dropbox folder browser using rclone.
Takes a Dropbox URL or path and lets you choose files to get shareable links.
"""

import subprocess
import json
import sys
import os
import platform

def run_rclone_command(args):
    """Run an rclone command and return the result."""
    cmd = ['rclone'] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        print("Error: rclone not found. Please install rclone first.")
        print("Visit: https://rclone.org/install/")
        sys.exit(1)

def convert_url_to_path(url_or_path):
    """Convert Dropbox URL to rclone path format."""
    # If it's already a path starting with /, return as is
    if url_or_path.startswith('/'):
        return url_or_path

    # If it starts with dropbox:, strip it
    if url_or_path.startswith('dropbox:'):
        return url_or_path[8:] or '/'

    # Handle Dropbox URLs
    if 'dropbox.com' in url_or_path:
        # Extract path from URL
        if '/home/' in url_or_path:
            # Format: https://www.dropbox.com/home/chess
            path = url_or_path.split('/home/')[-1]
            return '/' + path if path else '/'
        elif '/scl/fo/' in url_or_path or '/scl/fi/' in url_or_path:
            # Shared folder/file format - harder to extract path
            print("Note: Shared links detected. Using root directory instead.")
            print("For shared folders, please use the path format instead.")
            return '/'

    # Default: treat as path
    return '/' + url_or_path.lstrip('/')

def list_folder(path):
    """List contents of a Dropbox folder."""
    remote_path = f"dropbox:{path}"

    # Use lsjson for structured output
    returncode, stdout, stderr = run_rclone_command(['lsjson', remote_path])

    if returncode != 0:
        print(f"Error listing folder: {stderr}")
        return []

    try:
        items = json.loads(stdout) if stdout.strip() else []
        return items
    except json.JSONDecodeError:
        print("Error parsing folder contents")
        return []

def get_link(path):
    """Get shareable link for a file or folder."""
    remote_path = f"dropbox:{path}"
    returncode, stdout, stderr = run_rclone_command(['link', remote_path])

    if returncode != 0:
        return None

    return stdout.strip()

def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    if size_bytes <= 0:
        return ""

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def copy_to_clipboard(text):
    """Copy text to clipboard using system commands."""
    system = platform.system()

    try:
        if system == 'Darwin':  # macOS
            subprocess.run(['pbcopy'], input=text, text=True, check=True)
            return True
        elif system == 'Linux':
            # Try xclip first
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'],
                             input=text, text=True, check=True)
                return True
            except:
                # Try xsel as fallback
                try:
                    subprocess.run(['xsel', '--clipboard', '--input'],
                                 input=text, text=True, check=True)
                    return True
                except:
                    pass
        elif system == 'Windows':
            subprocess.run(['clip'], input=text, text=True, check=True, shell=True)
            return True
    except:
        pass

    return False

def main():
    """Main function."""
    # Get input from command line or interactively
    if len(sys.argv) > 1:
        input_path = ' '.join(sys.argv[1:])
    else:
        print("Enter Dropbox URL or path (e.g., 'chess', '/chess', 'dropbox:chess', or 'https://www.dropbox.com/home/chess'):")
        input_path = input().strip()
        if not input_path:
            print("No path provided. Exiting.")
            sys.exit(1)

    # Convert URL to path
    path = convert_url_to_path(input_path)

    print(f"\nListing contents of: {path}")
    print("=" * 50)

    # List folder contents
    items = list_folder(path)

    if not items:
        print("Folder is empty or doesn't exist.")
        sys.exit(1)

    # Separate folders and files
    folders = [item for item in items if item.get('IsDir', False)]
    files = [item for item in items if not item.get('IsDir', False)]

    # Sort by name
    folders.sort(key=lambda x: x['Name'].lower())
    files.sort(key=lambda x: x['Name'].lower())

    # Display files with numbers
    all_items = []
    item_number = 0

    # Show files first
    for file in files:
        item_number += 1
        size_str = format_size(file.get('Size', 0))
        print(f"{item_number}. 📄 {file['Name']} ({size_str})")
        all_items.append((file, False))  # (item, is_folder)

    # Show folders
    for folder in folders:
        item_number += 1
        print(f"{item_number}. 📁 {folder['Name']}/")
        all_items.append((folder, True))

    if not all_items:
        print("No items found.")
        sys.exit(1)

    print("=" * 50)

    # Interactive selection loop
    while True:
        print(f"\nSelect an item (1-{len(all_items)}), 'q' to quit:")
        choice = input().strip().lower()

        if choice in ['q', 'quit', 'exit']:
            print("Exiting...")
            break

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_items):
                item, is_folder = all_items[idx]
                item_path = os.path.join(path, item['Name'])

                # Get shareable link
                print(f"\nGetting link for: {item['Name']}...")
                link = get_link(item_path)

                if link:
                    print(f"Original URL: {link}")

                    # For files, create raw link (raw=1 instead of dl=1)
                    link_to_copy = link
                    if not is_folder:
                        raw_link = link.replace('dl=0', 'raw=1') if 'dl=0' in link else link + '?raw=1'
                        print(f"Raw URL: {raw_link}")
                        link_to_copy = raw_link

                    # Copy to clipboard (raw link for files, original for folders)
                    if copy_to_clipboard(link_to_copy):
                        print("✓ Link copied to clipboard!")
                    else:
                        print("(Could not copy to clipboard automatically)")
                else:
                    print("Could not generate link.")
            else:
                print(f"Invalid number. Please enter 1-{len(all_items)}.")
        else:
            print(f"Invalid input. Enter a number (1-{len(all_items)}) or 'q' to quit.")

if __name__ == "__main__":
    main()
