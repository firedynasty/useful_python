# Dropbox Folder Browser Script

This Python script is a command-line tool that lets you browse Dropbox folders and generate shareable links for files and folders. Here's what it does:

## Main Purpose
It connects to your Dropbox (via rclone) and lets you interactively select files or folders to get shareable links for them.

## Key Components

**Setup & Initialization**
The script starts by checking if rclone is installed. Rclone is a tool that syncs and manages files on cloud storage services like Dropbox. If it's not found, the script tells you to install it.

**URL/Path Conversion**
The `convert_url_to_path()` function is flexible about input—you can pass it a Dropbox URL (like `https://www.dropbox.com/home/chess`), a path like `/chess`, or just `chess`. It converts all these formats into a standard path that rclone understands.

**Listing Folder Contents**
The `list_folder()` function uses rclone's `lsjson` command to get a structured list of everything in a folder (both files and subfolders). It returns this as JSON data, which the script then parses.

**Getting Shareable Links**
The `get_link()` function uses rclone's `link` command to generate a shareable Dropbox link for whatever file or folder you select.

## How It Works in Practice

1. You run the script and provide a Dropbox path or URL
2. It lists all files (📄) and folders (📁) in that location, with file sizes
3. You pick a number corresponding to an item you want
4. The script generates a shareable link and copies it to your clipboard
5. For files, it also shows you a download link (changing `dl=0` to `dl=1`)
6. Repeat until you type 'q' to quit

## Helpful Details

The `format_size()` function converts raw bytes into readable sizes (KB, MB, GB, etc.). The `copy_to_clipboard()` function tries to copy the link automatically using the right system command for your OS—`pbcopy` on Mac, `xclip`/`xsel` on Linux, or `clip` on Windows.
