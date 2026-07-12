#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def collect_directories_with_prefix(directory_path, prefix):
    """Collect only directories that begin with the specified prefix (case-insensitive)."""
    directories = []
    
    # Walk the entire directory tree
    for root, dirs, files in os.walk(directory_path):
        root_path = Path(root)
        
        # Check each directory in the current level
        for dir_name in dirs:
            if dir_name.lower().startswith(prefix.lower()):
                dir_path = root_path / dir_name
                # Calculate depth for sorting
                depth = len(dir_path.relative_to(directory_path).parts)
                directories.append((dir_path, dir_name, depth))
    
    return directories

def rename_directories_with_prefix(directory_path, old_prefix, new_prefix, dry_run=False):
    """Rename directories by replacing the prefix."""
    directory_path = Path(directory_path).resolve()
    
    if not directory_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist.")
        return
    
    # Collect directories that need renaming
    directories_to_rename = collect_directories_with_prefix(directory_path, old_prefix)
    
    if not directories_to_rename:
        print(f"No directories beginning with '{old_prefix}' found.")
        return
    
    # Sort by depth (deepest first) to avoid path conflicts
    directories_to_rename.sort(key=lambda x: (-x[2], str(x[0])))
    
    print(f"Found {len(directories_to_rename)} directories to rename:")
    
    # Track renamed paths for updating references
    path_mapping = {}
    
    for old_path, old_name, depth in directories_to_rename:
        # Check if any parent directory was already renamed
        current_path = old_path
        for old_parent, new_parent in path_mapping.items():
            try:
                relative_path = old_path.relative_to(old_parent)
                current_path = new_parent / relative_path
                break
            except ValueError:
                continue
        
        # Create new name by replacing the prefix (case-insensitive)
        old_name_lower = old_name.lower()
        old_prefix_lower = old_prefix.lower()
        
        if old_name_lower.startswith(old_prefix_lower):
            # Replace the prefix with the new prefix
            new_name = new_prefix + old_name[len(old_prefix):]
            new_path = current_path.parent / new_name
            
            if dry_run:
                print(f"  directory (depth {depth}): {current_path} -> {new_path}")
            else:
                try:
                    if current_path.exists():
                        current_path.rename(new_path)
                        path_mapping[old_path] = new_path
                        print(f"Renamed directory: {current_path.name} -> {new_name}")
                    else:
                        print(f"Skipped directory (path no longer exists): {current_path}")
                except Exception as e:
                    print(f"Error renaming directory {current_path}: {e}")
    
    if not dry_run:
        print(f"\nSuccessfully renamed {len(directories_to_rename)} directories.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Rename directories by replacing a prefix')
    parser.add_argument('-i', '--input', required=True, help='Directory path to process')
    parser.add_argument('-p', '--old-prefix', required=True, help='Old prefix to replace')
    parser.add_argument('-o', '--new-prefix', required=True, help='New prefix to replace with')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without actually doing it')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No actual changes will be made")
    
    rename_directories_with_prefix(args.input, args.old_prefix, args.new_prefix, args.dry_run)

if __name__ == "__main__":
    main()