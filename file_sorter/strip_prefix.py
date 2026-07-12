#!/usr/bin/env python3
"""
Strip Prefix - Remove redundant folder-name prefixes from filenames.

After smart_archive.py sorts files into category folders, filenames often
start with the folder name they're already in:
    skills_dribbling/skills_dribbling_trae_1.mp4

This script strips that redundant prefix:
    skills_dribbling/trae_1.mp4

Usage:
    python strip_prefix.py ~/notes/02-basketball_b
    python strip_prefix.py ~/notes/02-basketball_b --move
"""

import argparse
import sys
from pathlib import Path


def strip_prefix(root: Path, execute: bool = False):
    """Walk each subfolder and strip folder-name prefix from filenames."""
    if not root.is_dir():
        print(f"Not a directory: {root}")
        sys.exit(1)

    plan = []

    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        folder_prefix = folder.name + "_"
        folder_prefix_lower = folder_prefix.lower()

        for filepath in sorted(folder.iterdir()):
            if not filepath.is_file() or filepath.name.startswith("."):
                continue

            name = filepath.name
            if name.lower().startswith(folder_prefix_lower):
                new_name = name[len(folder_prefix):]
                # Don't strip if it would leave an empty or dot-only name
                if new_name and not new_name.startswith("."):
                    plan.append((filepath, folder / new_name))

    if not plan:
        print("No redundant prefixes found.")
        return

    print(f"Found {len(plan)} files with redundant prefixes:\n")

    for old, new in plan:
        print(f"  {old.parent.name}/{old.name}")
        print(f"    → {new.parent.name}/{new.name}")

    if not execute:
        print(f"\nDRY RUN — no files renamed. Add --move to execute.")
        return

    renamed = 0
    for old, new in plan:
        if new.exists():
            print(f"  SKIP (collision): {new.name}")
            continue
        try:
            old.rename(new)
            renamed += 1
        except OSError as e:
            print(f"  ERROR: {old.name} → {e}")

    print(f"\nRenamed {renamed} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Strip redundant folder-name prefixes from filenames.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("root", type=Path, help="Root directory with sorted subfolders")
    parser.add_argument("--move", action="store_true",
                        help="Actually rename files (default is dry-run)")

    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    strip_prefix(root, execute=args.move)


if __name__ == "__main__":
    main()
