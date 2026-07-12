#!/usr/bin/env python3
"""
Simple Dropbox file downloader using rclone.
Takes a Dropbox URL or path and lets you choose files to download.
"""

import subprocess
import json
import sys
import os
import platform

def run_rclone_command(args, show_output=False):
    """Run an rclone command and return the result."""
    cmd = ['rclone'] + args
    try:
        if show_output:
            # Show progress for downloads
            result = subprocess.run(cmd, check=False)
            return result.returncode, "", ""
        else:
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

def download_file(remote_path, local_dir='.', use_move=False):
    """Download a file from Dropbox using rclone copy or move."""
    remote_full_path = f"dropbox:{remote_path}"

    # Use copy or move
    command = 'move' if use_move else 'copy'

    print(f"\nDownloading to: {os.path.abspath(local_dir)}")
    print("=" * 50)

    # Run rclone with progress
    args = [command, remote_full_path, local_dir, '--progress', '--verbose']
    returncode, stdout, stderr = run_rclone_command(args, show_output=True)

    if returncode == 0:
        filename = os.path.basename(remote_path)
        local_path = os.path.join(local_dir, filename)
        print("\n" + "=" * 50)
        print(f"✓ {'Moved' if use_move else 'Downloaded'}: {filename}")
        print(f"Location: {os.path.abspath(local_path)}")
        return True
    else:
        print(f"\n✗ Error downloading file")
        return False

def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    if size_bytes <= 0:
        return ""

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Download files from Dropbox using rclone')
    parser.add_argument('path', nargs='?', help='Dropbox URL or path')
    parser.add_argument('-o', '--output', default='.', help='Output directory (default: current directory)')
    parser.add_argument('-m', '--move', action='store_true',
                       help='Move files instead of copy (deletes from Dropbox after download)')

    args = parser.parse_args()

    # Get input from command line or interactively
    if args.path:
        input_path = args.path
    else:
        print("Enter Dropbox URL or path (e.g., 'chess', '/chess', 'dropbox:chess', or 'https://www.dropbox.com/home/chess'):")
        input_path = input().strip()
        if not input_path:
            print("No path provided. Exiting.")
            sys.exit(1)

    # Convert URL to path
    path = convert_url_to_path(input_path)

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        print(f"Created output directory: {args.output}")

    print(f"\nListing contents of: {path}")
    print("=" * 50)

    # List folder contents
    items = list_folder(path)

    if not items:
        print("Folder is empty or doesn't exist.")
        sys.exit(1)

    # Separate folders and files (only show files for downloading)
    files = [item for item in items if not item.get('IsDir', False)]

    # Sort by name
    files.sort(key=lambda x: x['Name'].lower())

    if not files:
        print("No files found in this folder (only subfolders).")
        sys.exit(1)

    # Display files with numbers
    print("\nAvailable files:")
    for i, file in enumerate(files, 1):
        size_str = format_size(file.get('Size', 0))
        print(f"{i}. 📄 {file['Name']} ({size_str})")

    print("=" * 50)

    # Warn if using move mode
    if args.move:
        print("\n⚠️  WARNING: Move mode enabled - files will be DELETED from Dropbox after download!")

    # Interactive selection loop
    while True:
        print(f"\nSelect a file to download (1-{len(files)}), 'a' for all, 'q' to quit:")
        choice = input().strip().lower()

        if choice in ['q', 'quit', 'exit']:
            print("Exiting...")
            break

        if choice == 'a':
            # Download all files
            print(f"\nDownloading all {len(files)} files...")
            for i, file in enumerate(files, 1):
                file_path = os.path.join(path, file['Name'])
                print(f"\n[{i}/{len(files)}] {file['Name']}")
                download_file(file_path, args.output, args.move)
            print(f"\n✓ Finished downloading all files to: {os.path.abspath(args.output)}")
            break

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                file = files[idx]
                file_path = os.path.join(path, file['Name'])
                download_file(file_path, args.output, args.move)
            else:
                print(f"Invalid number. Please enter 1-{len(files)}.")
        else:
            print(f"Invalid input. Enter a number (1-{len(files)}), 'a' for all, or 'q' to quit.")

if __name__ == "__main__":
    main()
