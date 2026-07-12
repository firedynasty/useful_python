#!/usr/bin/env python3
"""
Simple Dropbox file uploader using rclone.
Lists files in current directory and lets you choose which to upload.
"""

import subprocess
import sys
import os
import glob

def run_rclone_command(args, show_output=False):
    """Run an rclone command and return the result."""
    cmd = ['rclone'] + args
    try:
        if show_output:
            # Show progress for uploads
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

def list_local_files(directory='.', pattern='*'):
    """List files in local directory."""
    files = []

    # Get all files matching pattern
    search_path = os.path.join(directory, pattern)
    all_paths = glob.glob(search_path)

    # Also get hidden files if pattern includes them
    if pattern == '*':
        hidden_paths = glob.glob(os.path.join(directory, '.*'))
        all_paths.extend(hidden_paths)

    for path in all_paths:
        if os.path.isfile(path):
            filename = os.path.basename(path)
            size = os.path.getsize(path)
            files.append({
                'name': filename,
                'path': path,
                'size': size
            })

    # Sort by name
    files.sort(key=lambda x: x['name'].lower())
    return files

def upload_file(local_path, remote_path):
    """Upload a file to Dropbox using rclone copy."""
    remote_full_path = f"dropbox:{remote_path}"

    print(f"\nUploading: {os.path.basename(local_path)}")
    print(f"To: {remote_path}")
    print("=" * 50)

    # Run rclone with progress
    args = ['copy', local_path, remote_full_path, '--progress', '--verbose']
    returncode, stdout, stderr = run_rclone_command(args, show_output=True)

    if returncode == 0:
        print("\n" + "=" * 50)
        print(f"✓ Uploaded: {os.path.basename(local_path)}")
        return True
    else:
        print(f"\n✗ Error uploading file")
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

def use_fzf(files):
    """Use fzf for file selection if available."""
    try:
        # Create list of files for fzf
        file_list = '\n'.join([f['name'] for f in files])

        # Run fzf
        result = subprocess.run(
            ['fzf', '--multi', '--prompt=Select files to upload (TAB to select multiple): '],
            input=file_list,
            text=True,
            capture_output=True,
            check=True
        )

        # Get selected files
        selected_names = result.stdout.strip().split('\n')
        selected_files = [f for f in files if f['name'] in selected_names]
        return selected_files
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Upload files to Dropbox using rclone')
    parser.add_argument('destination', nargs='?', help='Dropbox destination path or URL')
    parser.add_argument('-s', '--source', default='.', help='Source directory (default: current directory)')
    parser.add_argument('-p', '--pattern', default='*', help='File pattern to match (default: *)')
    parser.add_argument('--no-fzf', action='store_true', help='Disable fzf even if available')

    args = parser.parse_args()

    # Get destination path
    if args.destination:
        dest_path = args.destination
    else:
        print("Enter Dropbox destination path (e.g., 'chess', '/chess', or 'https://www.dropbox.com/home/chess'):")
        dest_path = input().strip()
        if not dest_path:
            print("No destination provided. Exiting.")
            sys.exit(1)

    # Convert URL to path
    dropbox_path = convert_url_to_path(dest_path)

    print(f"\nScanning files in: {os.path.abspath(args.source)}")
    print(f"Destination: dropbox:{dropbox_path}")
    print("=" * 50)

    # List local files
    files = list_local_files(args.source, args.pattern)

    if not files:
        print(f"No files found matching pattern: {args.pattern}")
        sys.exit(1)

    # Try fzf first if available and not disabled
    selected_files = None
    if not args.no_fzf:
        print("\nAttempting to use fzf for file selection...")
        selected_files = use_fzf(files)

    # If fzf not available or disabled, use numbered selection
    if selected_files is None:
        if not args.no_fzf:
            print("fzf not available, using numbered selection instead.\n")

        print(f"\nFound {len(files)} file(s):")
        for i, file in enumerate(files, 1):
            size_str = format_size(file['size'])
            print(f"{i}. 📄 {file['name']} ({size_str})")

        print("=" * 50)

        # Interactive selection loop
        selected_files = []
        while True:
            print(f"\nSelect files to upload (1-{len(files)}), 'a' for all, 'done' when finished, 'q' to quit:")
            choice = input().strip().lower()

            if choice in ['q', 'quit', 'exit']:
                print("Exiting...")
                sys.exit(0)

            if choice in ['done', 'd']:
                if selected_files:
                    break
                else:
                    print("No files selected yet. Select at least one file or 'q' to quit.")
                    continue

            if choice == 'a':
                selected_files = files.copy()
                print(f"Selected all {len(files)} files.")
                break

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    file = files[idx]
                    if file not in selected_files:
                        selected_files.append(file)
                        print(f"✓ Added: {file['name']} (Total: {len(selected_files)} selected)")
                    else:
                        print(f"Already selected: {file['name']}")
                else:
                    print(f"Invalid number. Please enter 1-{len(files)}.")
            else:
                print(f"Invalid input. Enter a number (1-{len(files)}), 'a' for all, 'done' when finished, or 'q' to quit.")

    # Upload selected files
    if not selected_files:
        print("No files selected. Exiting.")
        sys.exit(0)

    print(f"\n{'='*50}")
    print(f"Uploading {len(selected_files)} file(s) to: dropbox:{dropbox_path}")
    print(f"{'='*50}")

    success_count = 0
    fail_count = 0

    for i, file in enumerate(selected_files, 1):
        print(f"\n[{i}/{len(selected_files)}]")
        if upload_file(file['path'], dropbox_path):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print(f"\n{'='*50}")
    print("UPLOAD SUMMARY")
    print(f"{'='*50}")
    print(f"✓ Successful: {success_count}")
    if fail_count > 0:
        print(f"✗ Failed: {fail_count}")
    print(f"Destination: dropbox:{dropbox_path}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
