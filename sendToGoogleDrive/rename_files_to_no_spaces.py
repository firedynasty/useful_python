#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def rename_spaces_to_underscores(directory_path, dry_run=False):
    """Rename all files and folders to replace spaces with underscores."""
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist.")
        return
    
    # Collect all items (files and folders) with their depths
    items_to_rename = []
    
    for root, dirs, files in os.walk(directory_path):
        root_path = Path(root)
        
        # Add files
        for file in files:
            file_path = root_path / file
            if ' ' in file:
                new_name = file.replace(' ', '_')
                items_to_rename.append((file_path, new_name, 'file'))
        
        # Add directories
        for dir_name in dirs:
            dir_path = root_path / dir_name
            if ' ' in dir_name:
                new_name = dir_name.replace(' ', '_')
                items_to_rename.append((dir_path, new_name, 'directory'))
    
    # Sort by depth (deepest first) to avoid path conflicts
    items_to_rename.sort(key=lambda x: len(x[0].parts), reverse=True)
    
    if not items_to_rename:
        print("No files or folders with spaces found.")
        return
    
    print(f"Found {len(items_to_rename)} items to rename:")
    
    for old_path, new_name, item_type in items_to_rename:
        new_path = old_path.parent / new_name
        
        if dry_run:
            print(f"  {item_type}: {old_path} -> {new_path}")
        else:
            try:
                old_path.rename(new_path)
                print(f"Renamed {item_type}: {old_path.name} -> {new_name}")
            except Exception as e:
                print(f"Error renaming {old_path}: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Rename files and folders by replacing spaces with underscores')
    parser.add_argument('directory', help='Directory path to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without actually doing it')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No actual changes will be made")
    
    rename_spaces_to_underscores(args.directory, args.dry_run)

if __name__ == "__main__":
    main()