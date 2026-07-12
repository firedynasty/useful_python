#!/usr/bin/env python3
"""
Get Dropbox links for image slideshow.
Outputs JavaScript imageSets format with images and audio.
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
    if url_or_path.startswith('/'):
        return url_or_path

    if url_or_path.startswith('dropbox:'):
        return url_or_path[8:] or '/'

    if 'dropbox.com' in url_or_path:
        if '/home/' in url_or_path:
            path = url_or_path.split('/home/')[-1]
            return '/' + path if path else '/'

    return '/' + url_or_path.lstrip('/')

def list_folder(path):
    """List contents of a Dropbox folder."""
    remote_path = f"dropbox:{path}"
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
    """Get shareable link for a file."""
    remote_path = f"dropbox:{path}"
    returncode, stdout, stderr = run_rclone_command(['link', remote_path])

    if returncode != 0:
        return None

    return stdout.strip()

def copy_to_clipboard(text):
    """Copy text to clipboard."""
    system = platform.system()

    try:
        if system == 'Darwin':
            subprocess.run(['pbcopy'], input=text, text=True, check=True)
            return True
        elif system == 'Linux':
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'],
                             input=text, text=True, check=True)
                return True
            except:
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

def natural_sort_key(name):
    """Sort key for natural sorting (handles numbers correctly)."""
    import re
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', name)]

def main():
    """Main function."""
    # Get input from command line or interactively
    if len(sys.argv) > 1:
        input_path = ' '.join(sys.argv[1:])
    else:
        print("Enter Dropbox URL or path:")
        input_path = input().strip()
        if not input_path:
            print("No path provided. Exiting.")
            sys.exit(1)

    path = convert_url_to_path(input_path)

    # Get set name from folder path
    set_name = os.path.basename(path.rstrip('/')) or 'my_set'
    set_name = set_name.replace(' ', '_').replace('-', '_')

    print(f"\nFolder: {path}")
    print(f"Set name: {set_name}")
    print("=" * 50)

    # List folder contents
    items = list_folder(path)

    if not items:
        print("Folder is empty or doesn't exist.")
        sys.exit(1)

    # Get only files (no folders)
    files = [item for item in items if not item.get('IsDir', False)]

    # Sort naturally
    files.sort(key=lambda x: natural_sort_key(x['Name']))

    # Separate images and audio
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg')
    audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac')

    image_files = []
    audio_files = []

    for f in files:
        name_lower = f['Name'].lower()
        if any(name_lower.endswith(ext) for ext in image_extensions):
            image_files.append(f)
        elif any(name_lower.endswith(ext) for ext in audio_extensions):
            audio_files.append(f)

    print(f"Found {len(image_files)} image(s) and {len(audio_files)} audio file(s)")
    print("=" * 50)

    # Get links for all files
    image_links = []
    audio_link = None

    total = len(image_files) + len(audio_files)
    current = 0

    # Get audio link first
    for audio_file in audio_files:
        current += 1
        item_path = os.path.join(path, audio_file['Name'])
        print(f"[{current}/{total}] {audio_file['Name']}...", end=' ', flush=True)

        link = get_link(item_path)
        if link:
            audio_link = link.replace('dl=0', 'raw=1') if 'dl=0' in link else link + '?raw=1'
            print("✓")
        else:
            print("✗")

    # Get image links
    for img_file in image_files:
        current += 1
        item_path = os.path.join(path, img_file['Name'])
        print(f"[{current}/{total}] {img_file['Name']}...", end=' ', flush=True)

        link = get_link(item_path)
        if link:
            download_link = link.replace('dl=0', 'raw=1') if 'dl=0' in link else link + '?raw=1'
            image_links.append(download_link)
            print("✓")
        else:
            print("✗")

    # Generate JS output
    lines = []
    lines.append("const imageSets = {")
    lines.append(f'    "{set_name}": {{')
    lines.append('        images: [')
    for i, img_url in enumerate(image_links):
        comma = "," if i < len(image_links) - 1 else ""
        lines.append(f'            "{img_url}"{comma}')
    lines.append('        ]' + (',' if audio_link else ''))
    if audio_link:
        lines.append(f'        audio: "{audio_link}"')
    lines.append('    }')
    lines.append('};')

    js_output = '\n'.join(lines)

    # Save to file
    output_file = 'imageSets.js'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(js_output)

    print("\n" + "=" * 50)
    print(f"✓ Saved to: {output_file}")

    # Copy to clipboard
    if copy_to_clipboard(js_output):
        print("✓ Copied to clipboard!")

    # Print the output
    print("\n" + js_output)

if __name__ == "__main__":
    main()
