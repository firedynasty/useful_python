#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def collect_files_with_prefix(directory_path, prefix):
    """Collect only files that begin with the specified prefix (case-insensitive)."""
    files = []
    
    # Walk the entire directory tree
    for root, dirs, file_names in os.walk(directory_path):
        root_path = Path(root)
        
        # Check each file in the current level
        for file_name in file_names:
            if file_name.lower().startswith(prefix.lower()):
                file_path = root_path / file_name
                # Calculate depth for sorting
                depth = len(file_path.relative_to(directory_path).parts)
                files.append((file_path, file_name, depth))
    
    return files

def rename_files_with_prefix(directory_path, old_prefix, new_prefix, dry_run=False):
    """Rename files by replacing the prefix."""
    directory_path = Path(directory_path).resolve()
    
    if not directory_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist.")
        return
    
    # Collect files that need renaming
    files_to_rename = collect_files_with_prefix(directory_path, old_prefix)
    
    if not files_to_rename:
        print(f"No files beginning with '{old_prefix}' found.")
        return
    
    # Sort by depth (deepest first) to avoid path conflicts
    files_to_rename.sort(key=lambda x: (-x[2], str(x[0])))
    
    print(f"Found {len(files_to_rename)} files to rename:")
    
    for file_path, old_name, depth in files_to_rename:
        # Create new name by replacing the prefix (case-insensitive)
        old_name_lower = old_name.lower()
        old_prefix_lower = old_prefix.lower()
        
        if old_name_lower.startswith(old_prefix_lower):
            # Replace the prefix with the new prefix
            new_name = new_prefix + old_name[len(old_prefix):]
            new_path = file_path.parent / new_name
            
            if dry_run:
                print(f"  file (depth {depth}): {file_path} -> {new_path}")
            else:
                try:
                    if file_path.exists():
                        file_path.rename(new_path)
                        print(f"Renamed file: {file_path.name} -> {new_name}")
                    else:
                        print(f"Skipped file (path no longer exists): {file_path}")
                except Exception as e:
                    print(f"Error renaming file {file_path}: {e}")
    
    if not dry_run:
        print(f"\nSuccessfully renamed {len(files_to_rename)} files.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Rename files by replacing a prefix')
    parser.add_argument('-i', '--input', required=True, help='Directory path to process')
    parser.add_argument('-p', '--old-prefix', required=True, help='Old prefix to replace')
    parser.add_argument('-o', '--new-prefix', required=True, help='New prefix to replace with')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without actually doing it')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No actual changes will be made")
    
    rename_files_with_prefix(args.input, args.old_prefix, args.new_prefix, args.dry_run)

if __name__ == "__main__":
    main()