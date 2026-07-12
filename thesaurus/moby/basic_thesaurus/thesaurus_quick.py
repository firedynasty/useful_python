#!/usr/bin/env python3
"""
Quick thesaurus lookup - returns plain text output for GUI dialogs
Usage: python thesaurus_quick.py <word>
"""

import sys
import os

# Add parent directory to path for words.txt access
script_dir = os.path.dirname(os.path.abspath(__file__))
words_file = os.path.join(script_dir, '..', 'words.txt')

def load_thesaurus():
    """Load the Moby thesaurus"""
    thesaurus = {}
    if not os.path.exists(words_file):
        return thesaurus

    try:
        with open(words_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    key = parts[0].lower()
                    thesaurus[key] = parts[1:]
    except Exception:
        pass
    return thesaurus

def get_synonyms(word, thesaurus):
    """Get synonyms for a word"""
    word_lower = word.lower()
    if word_lower in thesaurus:
        return [s for s in thesaurus[word_lower] if s.lower() != word_lower]
    return []

def main():
    if len(sys.argv) < 2:
        print("Usage: python thesaurus_quick.py [--list] <word>")
        sys.exit(1)

    # Check for --list flag (raw comma-separated output)
    list_mode = '--list' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--list']

    word = ' '.join(args).strip().lower()
    thesaurus = load_thesaurus()

    if not thesaurus:
        print("Error: Could not load thesaurus (words.txt not found)")
        sys.exit(1)

    synonyms = get_synonyms(word, thesaurus)

    if synonyms:
        if list_mode:
            # Raw comma-separated for AppleScript
            print(", ".join(synonyms))
        else:
            print(f"Synonyms for '{word}':")
            print(", ".join(synonyms))
    else:
        if not list_mode:
            print(f"No synonyms found for '{word}'")

if __name__ == "__main__":
    main()
