#!/usr/bin/env python3
"""
Outline to XMind Converter

Converts indented numbered outlines to XMind (.xmind) files.
Supports arbitrary nesting depth based on indentation.

Input format (3-space indent per level):
    1. getting a job
       1. requires patience
    2. get your resume ready
       1. use resume.io

Usage:
    python md_to_xmind.py sample_outline.md
    python md_to_xmind.py sample_outline.md -t "My Mind Map"
    python md_to_xmind.py sample_outline.md -o output.xmind
"""

import argparse
import re
import sys
import os
from pathlib import Path
from xmind import XMindGenerator


def parse_outline(text):
    """Parse indented numbered outline into a nested structure.

    Returns a list of (title, children) tuples.
    """
    lines = text.strip().splitlines()
    if not lines:
        return []

    # Parse each line into (indent_level, title)
    parsed = []
    for line in lines:
        if not line.strip():
            continue
        # Count leading spaces
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        # Remove numbering prefix like "1. " or "a. " or "- "
        title = re.sub(r'^[\d]+\.\s+', '', stripped)
        title = re.sub(r'^[a-z]\.\s+', '', title)
        title = re.sub(r'^[-*]\s+', '', title)
        title = title.strip()
        if not title:
            continue
        parsed.append((indent, title))

    if not parsed:
        return []

    # Build tree from flat (indent, title) list
    def build_tree(items, start, level_indent):
        """Build nested list from items at a given indent level."""
        result = []
        i = start
        while i < len(items):
            indent, title = items[i]
            if indent < level_indent:
                # Back to parent level
                break
            if indent == level_indent:
                # Sibling at this level — collect children
                children, i = build_tree(items, i + 1, indent + 1)
                result.append((title, children))
            else:
                # Deeper than expected — treat as child of current level
                children, i = build_tree(items, i, indent)
                if result:
                    # Attach as children of last sibling
                    prev_title, prev_children = result[-1]
                    result[-1] = (prev_title, prev_children + children)
                else:
                    # No parent yet, promote them
                    for c in children:
                        result.append(c)
        return result, i

    min_indent = parsed[0][0]
    tree, _ = build_tree(parsed, 0, min_indent)
    return tree


def tree_to_topics(generator, tree, id_prefix="topic"):
    """Convert parsed tree into XMind topic elements."""
    topics = []
    for idx, (title, children) in enumerate(tree, 1):
        topic_id = f"{id_prefix}_{idx}"
        subtopics = None
        if children:
            subtopics = tree_to_topics(generator, children, id_prefix=topic_id)
        topics.append(generator.create_topic(title, topic_id=topic_id, subtopics=subtopics))
    return topics


def main():
    parser = argparse.ArgumentParser(
        description='Convert indented outline to XMind file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python md_to_xmind.py sample_outline.md
  python md_to_xmind.py sample_outline.md -t "Career Planning"
  python md_to_xmind.py notes.txt -o my_mindmap.xmind
        '''
    )
    parser.add_argument('input_file', help='Input outline file (.md or .txt)')
    parser.add_argument('-o', '--output', help='Output .xmind filename (default: same name as input)')
    parser.add_argument('-t', '--title', help='Central topic title (default: filename)')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: '{args.input_file}' not found")
        sys.exit(1)

    # Read input
    with open(args.input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Parse outline
    tree = parse_outline(text)
    if not tree:
        print("Error: no outline content found")
        sys.exit(1)

    # Central topic title
    input_path = Path(args.input_file)
    title = args.title or input_path.stem.replace('_', ' ').title()

    # Output filename
    if args.output:
        output = args.output if args.output.endswith('.xmind') else args.output + '.xmind'
    else:
        output = input_path.stem + '.xmind'

    # Generate xmind
    generator = XMindGenerator()
    branches = tree_to_topics(generator, tree)
    mind_map = generator.create_mind_map(title, branches)
    generator.save_xmind_file(mind_map, output)

    print(f"  Input:  {args.input_file}")
    print(f"  Title:  {title}")
    print(f"  Output: {output}")
    print(f"  Topics: {sum(1 for _ in _count_topics(tree))}")


def _count_topics(tree):
    """Count total topics in tree."""
    for title, children in tree:
        yield title
        if children:
            yield from _count_topics(children)


if __name__ == "__main__":
    main()
