#!/usr/bin/env python3
"""
Generate a tree of the notes folder structure for use as Claude chat context.

Usage:
    python generate_notes_tree.py
    python generate_notes_tree.py -i ~/Documents/notes -o notes_tree.txt
    python generate_notes_tree.py --depth 3
"""

import argparse
from pathlib import Path

DEFAULT_NOTES = Path.home() / "Documents" / "notes"


def build_tree(root: Path, depth: int, prefix: str = "", current_depth: int = 0) -> list[str]:
    """Build tree lines for a directory, like the tree command."""
    if current_depth >= depth:
        return []

    entries = sorted(
        [e for e in root.iterdir() if e.is_dir() and not e.name.startswith('.')],
        key=lambda p: p.name.lower()
    )

    lines = []
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        extension = "    " if is_last else "│   "
        lines.extend(build_tree(entry, depth, prefix + extension, current_depth + 1))

    return lines


def main():
    parser = argparse.ArgumentParser(
        description='Generate notes folder tree for Claude chat context')
    parser.add_argument('folder', nargs='?', type=Path, default=None,
                        help='Notes folder (positional, e.g. notestree .)')
    parser.add_argument('-i', '--input', type=Path, default=None,
                        help=f'Notes folder (default: {DEFAULT_NOTES})')
    parser.add_argument('-o', '--output', type=Path, default=None,
                        help='Output file (default: <input>/folders.txt)')
    parser.add_argument('--depth', type=int, default=2,
                        help='Directory depth (default: 2)')

    args = parser.parse_args()
    notes_dir = args.folder or args.input or DEFAULT_NOTES
    output_file = args.output or notes_dir / "folders.txt"

    if not notes_dir.exists():
        print(f"Folder not found: {notes_dir}")
        return

    lines = [f"{notes_dir.name}/"]
    lines.extend(build_tree(notes_dir, args.depth))
    lines.append(f"\n{len([l for l in lines if '── ' in l])} directories")

    tree_text = "\n".join(lines)

    with open(output_file, 'w') as f:
        f.write(tree_text)

    print(tree_text)
    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
