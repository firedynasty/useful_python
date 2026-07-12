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

def list_folder(path, recursive=False):
    """List contents of a Dropbox folder."""
    remote_path = f"dropbox:{path}"

    # Use lsjson for structured output
    cmd = ['lsjson', remote_path]
    if recursive:
        cmd.append('--recursive')
    returncode, stdout, stderr = run_rclone_command(cmd)

    if returncode != 0:
        print(f"Error listing folder: {stderr}")
        return []

    try:
        items = json.loads(stdout) if stdout.strip() else []
        if recursive:
            # lsjson --recursive returns Path with relative paths like "subfolder/file.mp4"
            # Update Name to include the relative path for display and link generation
            for item in items:
                if item.get('Path'):
                    item['Name'] = item['Path']
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

def get_all_file_links(path, files):
    """Get links for all files in a folder."""
    links_data = []
    total = len(files)

    print(f"\nGenerating links for {total} files...")
    print("=" * 50)

    for idx, file in enumerate(files, 1):
        item_path = os.path.join(path, file['Name'])
        print(f"[{idx}/{total}] Getting link for: {file['Name']}...", end=' ')

        link = get_link(item_path)

        if link:
            # Replace dl=0 with raw=1 for direct download links
            download_link = link.replace('dl=0', 'raw=1') if 'dl=0' in link else link + '?raw=1'
            links_data.append({
                'name': file['Name'],
                'size': file.get('Size', 0),
                'view_link': link,
                'download_link': download_link
            })
            print("✓")
        else:
            print("✗ Failed")

    return links_data

def save_links_to_file(links_data, output_file='dropbox_links.txt'):
    """Save links to a text file (one link per line)."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in links_data:
                f.write(f"{item['download_link']}\n")

        return True
    except Exception as e:
        print(f"Error saving to file: {e}")
        return False

def save_links_as_js(links_data, set_name, output_file='imageSets.js'):
    """Save links as JavaScript object format."""
    # Separate images and audio files
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg')
    audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac')

    images = []
    audio = None

    for item in links_data:
        name_lower = item['name'].lower()
        if any(name_lower.endswith(ext) for ext in image_extensions):
            images.append(item['download_link'])
        elif any(name_lower.endswith(ext) for ext in audio_extensions):
            audio = item['download_link']

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("const imageSets = {\n")
            f.write(f'    "{set_name}": {{\n')
            f.write('        images: [\n')
            for i, img_url in enumerate(images):
                comma = "," if i < len(images) - 1 else ""
                f.write(f'            "{img_url}"{comma}\n')
            f.write('        ]')
            if audio:
                f.write(',\n')
                f.write(f'        audio: "{audio}"\n')
            else:
                f.write('\n')
            f.write('    }\n')
            f.write('};\n')
        return True
    except Exception as e:
        print(f"Error saving JS file: {e}")
        return False

def generate_js_string(links_data, set_name):
    """Generate JavaScript object as a string."""
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg')
    audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac')

    images = []
    audio = None

    for item in links_data:
        name_lower = item['name'].lower()
        if any(name_lower.endswith(ext) for ext in image_extensions):
            images.append(item['download_link'])
        elif any(name_lower.endswith(ext) for ext in audio_extensions):
            audio = item['download_link']

    lines = []
    lines.append("const imageSets = {")
    lines.append(f'    "{set_name}": {{')
    lines.append('        images: [')
    for i, img_url in enumerate(images):
        comma = "," if i < len(images) - 1 else ""
        lines.append(f'            "{img_url}"{comma}')
    lines.append('        ]' + (',' if audio else ''))
    if audio:
        lines.append(f'        audio: "{audio}"')
    lines.append('    }')
    lines.append('};')

    return '\n'.join(lines)

def save_links_as_video_array(links_data, output_file='video_gallery.js'):
    """Save links as JavaScript video gallery array for CodePen."""
    video_extensions = ('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.m4v')

    videos = []
    for item in links_data:
        name_lower = item['name'].lower()
        if any(name_lower.endswith(ext) for ext in video_extensions):
            # Generate title from filename: strip extension, replace separators with spaces, title case
            title = os.path.splitext(item['name'])[0]
            title = title.replace('_', ' ').replace('-', ' ')
            # Clean up multiple spaces
            title = ' '.join(title.split())
            videos.append({'title': title, 'url': item['download_link']})

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("const videos = [\n")
            for i, vid in enumerate(videos):
                comma = "," if i < len(videos) - 1 else ""
                f.write(f'    {{ title: "{vid["title"]}", src: "{vid["url"]}" }}{comma}\n')
            f.write("];\n")
        return True
    except Exception as e:
        print(f"Error saving video array file: {e}")
        return False

def generate_video_array_string(links_data):
    """Generate JavaScript video gallery array as a string."""
    video_extensions = ('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.m4v')

    videos = []
    for item in links_data:
        name_lower = item['name'].lower()
        if any(name_lower.endswith(ext) for ext in video_extensions):
            title = os.path.splitext(item['name'])[0]
            title = title.replace('_', ' ').replace('-', ' ')
            title = ' '.join(title.split())
            videos.append({'title': title, 'url': item['download_link']})

    lines = []
    lines.append("const videos = [")
    for i, vid in enumerate(videos):
        comma = "," if i < len(videos) - 1 else ""
        lines.append(f'    {{ title: "{vid["title"]}", src: "{vid["url"]}" }}{comma}')
    lines.append("];")

    return '\n'.join(lines)

def save_links_as_csv(links_data, output_file='links.csv'):
    """Save links as CSV with name and URL columns."""
    import csv
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'url'])
            for item in links_data:
                name = os.path.splitext(item['name'])[0]
                writer.writerow([name, item['download_link']])
        return True
    except Exception as e:
        print(f"Error saving CSV file: {e}")
        return False

def prompt_output_format(links_data, path):
    """Prompt user for output format and save/copy accordingly."""
    print("\nOutput format:")
    print("  1. Plain text (one URL per line)")
    print("  2. JavaScript imageSets object")
    print("  3. JavaScript video gallery array")
    print("  4. CSV (name, url)")
    format_choice = input("Choose format (1/2/3/4) [default: 1]: ").strip()

    if format_choice == '2':
        default_name = os.path.basename(path.rstrip('/')) or 'my_set'
        set_name = input(f"Enter set name [{default_name}]: ").strip() or default_name
        set_name = set_name.replace(' ', '_').replace('-', '_')

        output_file = 'imageSets.js'
        if save_links_as_js(links_data, set_name, output_file):
            print(f"✓ Links saved to: {output_file}")

        js_string = generate_js_string(links_data, set_name)
        if copy_to_clipboard(js_string):
            print("✓ JavaScript code copied to clipboard!")
        else:
            print("(Could not copy to clipboard automatically)")

    elif format_choice == '3':
        output_file = 'video_gallery.js'
        if save_links_as_video_array(links_data, output_file):
            print(f"✓ Links saved to: {output_file}")

        js_string = generate_video_array_string(links_data)
        if copy_to_clipboard(js_string):
            print("✓ JavaScript video array copied to clipboard!")
        else:
            print("(Could not copy to clipboard automatically)")

    elif format_choice == '4':
        output_file = 'links.csv'
        if save_links_as_csv(links_data, output_file):
            print(f"✓ Links saved to: {output_file}")
        else:
            print("✗ Failed to save CSV file")

    else:
        # Default: plain text
        output_file = 'dropbox_links.txt'
        if save_links_to_file(links_data, output_file):
            print(f"✓ Links saved to: {output_file}")

            all_download_links = '\n'.join([item['download_link'] for item in links_data])
            if copy_to_clipboard(all_download_links):
                print("✓ All download links copied to clipboard!")
            else:
                print("(Could not copy to clipboard automatically)")
        else:
            print("✗ Failed to save links to file")

def main():
    """Main function."""
    # Check for flags
    all_mode = '--all' in sys.argv
    recursive_mode = '--recursive' in sys.argv
    args = [a for a in sys.argv[1:] if a not in ('--all', '--recursive')]

    # Get input from command line or interactively
    if args:
        input_path = ' '.join(args)
    else:
        if all_mode:
            print("No path provided. Exiting.")
            sys.exit(1)
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
    items = list_folder(path, recursive=recursive_mode)

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

    # Show folders (skip in recursive mode since all files are already listed)
    if not recursive_mode:
        for folder in folders:
            item_number += 1
            print(f"{item_number}. 📁 {folder['Name']}/")
            all_items.append((folder, True))

    if not all_items:
        print("No items found.")
        sys.exit(1)

    print("=" * 50)

    # Non-interactive --all mode: get all links and copy to clipboard
    if all_mode:
        if not files:
            print("No files to process.")
            sys.exit(1)
        links_data = get_all_file_links(path, files)
        if links_data:
            all_links = '\n'.join([item['download_link'] for item in links_data])
            print(f"\n✓ Successfully generated {len(links_data)} links!")
            if copy_to_clipboard(all_links):
                print("✓ All download links copied to clipboard!")
            else:
                print(all_links)
        else:
            print("No links were generated.")
        return

    # Check if there are files to process
    if files:
        print(f"\nFound {len(files)} file(s) in this folder.")
        print("Options:")
        print("  'all' - Get links for all files and save to a file")
        print("  'from N' - Get links starting from file number N (e.g., 'from 10')")
        print("  1-{} - Select individual file".format(len(all_items)))
        print("  'q' - Quit")

    # Interactive selection loop
    while True:
        print(f"\nEnter your choice:")
        choice = input().strip().lower()

        if choice in ['q', 'quit', 'exit']:
            print("Exiting...")
            break

        if choice == 'all':
            if not files:
                print("No files to process.")
                continue

            # Get links for all files
            links_data = get_all_file_links(path, files)

            if links_data:
                print(f"\n✓ Successfully generated {len(links_data)} links!")
                prompt_output_format(links_data, path)
            else:
                print("No links were generated.")

            break

        if choice.startswith('from '):
            # Get links starting from a specific file number
            try:
                start_num = int(choice.split(' ')[1])
                if start_num < 1 or start_num > len(files):
                    print(f"Invalid number. Please enter a number between 1 and {len(files)}.")
                    continue

                # Get files from the starting number onwards (only files, not folders)
                files_subset = files[start_num - 1:]
                print(f"\nProcessing {len(files_subset)} file(s) starting from file #{start_num}...")

                # Get links for the subset
                links_data = get_all_file_links(path, files_subset)

                if links_data:
                    print(f"\n✓ Successfully generated {len(links_data)} links!")
                    prompt_output_format(links_data, path)
                else:
                    print("No links were generated.")

                break
            except (ValueError, IndexError):
                print("Invalid format. Use 'from N' where N is a number (e.g., 'from 10').")
                continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_items):
                item, is_folder = all_items[idx]
                item_path = os.path.join(path, item['Name'])

                # Get shareable link
                print(f"\nGetting link for: {item['Name']}...")
                link = get_link(item_path)

                if link:
                    print(f"URL: {link}")

                    # If it's a file, also show download link
                    if not is_folder:
                        download_link = link.replace('dl=0', 'raw=1') if 'dl=0' in link else link + '?raw=1'
                        print(f"Download URL: {download_link}")

                    # Copy to clipboard
                    if copy_to_clipboard(link):
                        print("✓ Link copied to clipboard!")
                    else:
                        print("(Could not copy to clipboard automatically)")
                else:
                    print("Could not generate link.")
            else:
                print(f"Invalid number. Please enter 1-{len(all_items)}.")
        else:
            print(f"Invalid input. Enter 'all', 'from N', a number (1-{len(all_items)}), or 'q' to quit.")

if __name__ == "__main__":
    main()
