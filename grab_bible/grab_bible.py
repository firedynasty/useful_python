#!/usr/bin/env python3
"""
Extract Bible text segments starting from a specified verse.
Usage: python extract_bible_segment.py bible.txt "Genesis 1"
       python extract_bible_segment.py bible.txt "Genesis 10:5"
"""

import sys
import re
from typing import List, Tuple, Optional

def parse_bible_reference(reference: str) -> Tuple[str, int, Optional[int]]:
    """
    Parse a Bible reference like "Genesis 1" or "Genesis 10:5"
    Returns (book, chapter, verse) where verse is None if not specified
    """
    # Clean up the reference
    reference = reference.strip()
    
    # Match patterns like "Genesis 1" or "Genesis 1:5"
    match = re.match(r'^(\w+(?:\s+\w+)*)\s+(\d+)(?::(\d+))?$', reference, re.IGNORECASE)
    
    if not match:
        raise ValueError(f"Invalid Bible reference format: {reference}")
    
    book = match.group(1)
    chapter = int(match.group(2))
    verse = int(match.group(3)) if match.group(3) else None
    
    return book, chapter, verse

def extract_bible_entries(filename: str) -> List[Tuple[str, str]]:
    """
    Parse Bible text file and return list of (reference, text) tuples.
    Expected format: verse reference with tab on one line, text on next line
    """
    entries = []

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]  # Don't strip yet, need to check for tab
        line_stripped = line.strip()

        # Skip empty lines and headers
        if not line_stripped or line_stripped.startswith('The Holy Bible') or 'Berean' in line_stripped or line_stripped.startswith('This text') or line.startswith('Verse\t'):
            i += 1
            continue

        # Check if this line is a verse reference (contains tab)
        if '\t' in line:
            reference = line.split('\t')[0].strip()
            # Check if reference matches pattern like "Genesis 1:1"
            if re.match(r'^(\w+(?:\s+\w+)*)\s+\d+:\d+$', reference):
                # Get the text from the next line
                if i + 1 < len(lines):
                    text = lines[i + 1].strip()
                    if reference and text:
                        entries.append((reference, text))
                i += 2  # Skip both reference and text lines
                continue

        i += 1

    return entries

def find_starting_index(entries: List[Tuple[str, str]], book: str, chapter: int, verse: Optional[int]) -> int:
    """
    Find the index of the starting verse in the entries list.
    """
    for i, (reference, _) in enumerate(entries):
        # Parse the reference from the file
        ref_match = re.match(r'^(\w+(?:\s+\w+)*)\s+(\d+):(\d+)$', reference, re.IGNORECASE)
        if ref_match:
            ref_book = ref_match.group(1)
            ref_chapter = int(ref_match.group(2))
            ref_verse = int(ref_match.group(3))
            
            # Case-insensitive book comparison
            if ref_book.lower() == book.lower() and ref_chapter == chapter:
                # If no specific verse was requested, start at verse 1
                if verse is None and ref_verse == 1:
                    return i
                # If specific verse was requested, find it
                elif verse is not None and ref_verse == verse:
                    return i
    
    # If exact match not found, try to find the chapter start
    if verse is None:
        for i, (reference, _) in enumerate(entries):
            if reference.lower().startswith(f"{book.lower()} {chapter}:"):
                return i
    
    raise ValueError(f"Could not find {book} {chapter}{':' + str(verse) if verse else ''} in the text")

def extract_segment(entries: List[Tuple[str, str]], start_idx: int, num_lines: int = 500) -> List[Tuple[str, str]]:
    """
    Extract a segment of entries starting from start_idx.
    """
    end_idx = min(start_idx + num_lines, len(entries))
    return entries[start_idx:end_idx]

def format_for_prompt(segment: List[Tuple[str, str]]) -> str:
    """
    Format the segment for use in a prompt.
    """
    # Combine all text without verse references
    combined_text = " ".join(text for _, text in segment)
    
    return combined_text

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_bible_segment.py bible.txt \"Genesis 1\"")
        print("       python extract_bible_segment.py bible.txt \"Genesis 10:5\"")
        sys.exit(1)
    
    filename = sys.argv[1]
    reference = sys.argv[2]
    
    # Allow custom number of lines
    num_lines = 500
    for arg in sys.argv[3:]:
        if arg.startswith("--lines="):
            try:
                num_lines = int(arg.split("=")[1])
            except:
                pass
    
    try:
        # Parse the reference
        book, chapter, verse = parse_bible_reference(reference)
        
        # Extract all entries from the file
        print(f"Reading Bible text from {filename}...")
        entries = extract_bible_entries(filename)
        print(f"Found {len(entries)} verses total")
        
        # Find starting point
        start_idx = find_starting_index(entries, book, chapter, verse)
        
        # Extract segment
        segment = extract_segment(entries, start_idx, num_lines)
        
        if not segment:
            print(f"No verses found starting from {reference}")
            return
        
        # Display the segment with formatting
        print(f"\nExtracting {len(segment)} verses starting from {reference}")
        print("=" * 60)
        
        # Show first and last verses for reference
        first_ref, first_text = segment[0]
        last_ref, last_text = segment[-1]
        print(f"First verse: {first_ref}")
        print(f"Last verse: {last_ref}")
        print("=" * 60)
        
        # Display verses grouped by chapter
        current_chapter = None
        for ref, text in segment[:20]:  # Show first 20 for preview
            chapter_match = re.match(r'^(\w+(?:\s+\w+)*\s+\d+):', ref)
            if chapter_match:
                chapter_part = chapter_match.group(1)
                if chapter_part != current_chapter:
                    if current_chapter is not None:
                        print()  # Add blank line between chapters
                    print(f"\n[{chapter_part}]")
                    current_chapter = chapter_part
            print(f"{ref}: {text[:100]}..." if len(text) > 100 else f"{ref}: {text}")
        
        if len(segment) > 20:
            print(f"\n... and {len(segment) - 20} more verses ...")
        
        print("=" * 60)
        
        # Format for prompt and copy to clipboard
        formatted_text = format_for_prompt(segment)
        
        # Show word count
        word_count = len(formatted_text.split())
        print(f"\nTotal words: {word_count}")
        
        # Copy to clipboard
        try:
            import pyperclip
            pyperclip.copy(formatted_text)
            print("\n[Text copied to clipboard]")
        except ImportError:
            print("\n[pyperclip not available - install with: pip install pyperclip]")
            print("\nFormatted text (first 500 chars):")
            print(formatted_text[:500] + "..." if len(formatted_text) > 500 else formatted_text)
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
