#!/usr/bin/env python3
"""
Simple Thesaurus CLI Application
Finds synonyms and related words using the Datamuse API or Moby Thesaurus (offline)
"""

import requests
import sys
import os
from typing import List, Dict, Set

# Global thesaurus data
MOBY_THESAURUS = {}
MOBY_AVAILABLE = False

def load_moby_thesaurus():
    """Load the Moby thesaurus from words.txt"""
    global MOBY_THESAURUS, MOBY_AVAILABLE

    # Look for words.txt in parent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    words_file = os.path.join(script_dir, '..', 'words.txt')

    if not os.path.exists(words_file):
        return False

    try:
        with open(words_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    key = parts[0].lower()
                    synonyms = parts[1:]
                    MOBY_THESAURUS[key] = synonyms
        MOBY_AVAILABLE = True
        return True
    except Exception as e:
        print(f"Warning: Could not load Moby thesaurus: {e}")
        return False

# Load thesaurus on import
load_moby_thesaurus()


class Thesaurus:
    """A simple thesaurus class using the Datamuse API or Moby Thesaurus"""

    BASE_URL = "https://api.datamuse.com/words"

    def __init__(self, offline_mode: bool = False):
        """Initialize thesaurus with mode selection"""
        self.offline_mode = offline_mode
        if offline_mode and not MOBY_AVAILABLE:
            print("Warning: Moby thesaurus not available. Ensure words.txt exists in parent directory.")

    def _get_moby_synonyms(self, word: str) -> Set[str]:
        """Get synonyms using Moby Thesaurus"""
        if not MOBY_AVAILABLE:
            return set()

        word_lower = word.lower()
        synonyms = set()

        # Direct lookup
        if word_lower in MOBY_THESAURUS:
            for syn in MOBY_THESAURUS[word_lower]:
                if syn.lower() != word_lower:
                    synonyms.add(syn)

        return synonyms

    def _get_moby_related(self, word: str) -> Set[str]:
        """Get related words - words that have this word as a synonym"""
        if not MOBY_AVAILABLE:
            return set()

        word_lower = word.lower()
        related = set()

        # Find entries where this word appears as a synonym
        for key, syns in MOBY_THESAURUS.items():
            syns_lower = [s.lower() for s in syns]
            if word_lower in syns_lower and key != word_lower:
                related.add(key)

        return related

    def get_synonyms(self, word: str, max_results: int = 20) -> List[Dict[str, any]]:
        """Get synonyms for a word"""
        if self.offline_mode:
            synonyms = self._get_moby_synonyms(word)
            return [{'word': syn, 'score': 0} for syn in list(synonyms)[:max_results]]

        params = {'ml': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # Fallback to offline mode
            if MOBY_AVAILABLE:
                synonyms = self._get_moby_synonyms(word)
                return [{'word': syn, 'score': 0} for syn in list(synonyms)[:max_results]]
            return []

    def get_antonyms(self, word: str, max_results: int = 20) -> List[Dict[str, any]]:
        """Get antonyms for a word (online only - Moby doesn't distinguish antonyms)"""
        if self.offline_mode:
            return []  # Moby thesaurus doesn't separate antonyms

        params = {'rel_ant': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return []

    def get_related_words(self, word: str, max_results: int = 15) -> List[Dict[str, any]]:
        """Get related words"""
        if self.offline_mode:
            related = self._get_moby_related(word)
            return [{'word': rel, 'score': 0} for rel in list(related)[:max_results]]

        params = {'rel_trg': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if MOBY_AVAILABLE:
                related = self._get_moby_related(word)
                return [{'word': rel, 'score': 0} for rel in list(related)[:max_results]]
            return []

    def get_rhymes(self, word: str, max_results: int = 15) -> List[Dict[str, any]]:
        """Get words that rhyme - online only"""
        if self.offline_mode:
            return []

        params = {'rel_rhy': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return []


def print_results(title: str, results: List[Dict[str, any]], color_code: str = "94"):
    """Print formatted results"""
    if not results:
        print(f"\n{title}: None found")
        return
    
    print(f"\n\033[1m{title}:\033[0m")
    words = [item['word'] for item in results]
    
    # Print in columns
    for i in range(0, len(words), 5):
        row = words[i:i+5]
        formatted_row = [f"\033[{color_code}m{word}\033[0m" for word in row]
        print("  " + ", ".join(formatted_row))


def print_banner():
    """Print application banner"""
    banner = """
╔════════════════════════════════════════╗
║      📚 PYTHON THESAURUS APP 📚       ║
╚════════════════════════════════════════╝
"""
    print(banner)


def interactive_mode():
    """Run the thesaurus in interactive mode"""
    # Auto-detect mode: prefer offline with Moby thesaurus
    offline = MOBY_AVAILABLE
    mode_str = "OFFLINE MODE (Moby Thesaurus)" if offline else "ONLINE MODE (Datamuse API)"

    thesaurus = Thesaurus(offline_mode=offline)
    print_banner()
    print(f"Running in: \033[93m{mode_str}\033[0m")
    if MOBY_AVAILABLE:
        print(f"Loaded \033[96m{len(MOBY_THESAURUS):,}\033[0m word entries from Moby Thesaurus")
    print("Enter a word to find synonyms and related words!")
    print("Commands: 'quit' or 'exit' to leave, 'help' for options")
    print("         'online' to force online mode, 'offline' to force offline mode\n")

    while True:
        try:
            user_input = input("\033[92m🔍 Enter word: \033[0m").strip().lower()

            if user_input in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using Python Thesaurus! Goodbye!\n")
                break

            if user_input == 'online':
                offline = False
                thesaurus = Thesaurus(offline_mode=False)
                print("\033[93mSwitched to ONLINE MODE (Datamuse API)\033[0m\n")
                continue

            if user_input == 'offline':
                if not MOBY_AVAILABLE:
                    print("\033[91mMoby thesaurus not available. Ensure words.txt exists.\033[0m\n")
                    continue
                offline = True
                thesaurus = Thesaurus(offline_mode=True)
                print("\033[93mSwitched to OFFLINE MODE (Moby Thesaurus)\033[0m\n")
                continue

            if user_input == 'help':
                print("\nAvailable information for each word:")
                print("  • Synonyms (words with similar meaning)")
                if offline:
                    print("  • Related words (words that share this as synonym)")
                else:
                    print("  • Antonyms (words with opposite meaning)")
                    print("  • Related words (associated terms)")
                    print("  • Rhymes (words that rhyme)")
                print("\nCommands:")
                print("  • 'online' - Switch to online mode (requires internet)")
                print("  • 'offline' - Switch to offline mode (uses Moby Thesaurus)")
                print("  • 'quit' or 'exit' - Exit the application\n")
                continue

            if not user_input:
                continue

            print(f"\n{'='*50}")
            print(f"Results for: \033[1m'{user_input}'\033[0m")
            print('='*50)

            # Get and display synonyms
            synonyms = thesaurus.get_synonyms(user_input)
            print_results("Synonyms", synonyms, "94")

            # Get and display related words
            related = thesaurus.get_related_words(user_input)
            print_results("Related Words", related, "93")

            # Get and display antonyms and rhymes (online only)
            if not offline:
                antonyms = thesaurus.get_antonyms(user_input)
                print_results("Antonyms", antonyms, "91")

                rhymes = thesaurus.get_rhymes(user_input)
                print_results("Rhymes", rhymes, "95")

            print()

        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using Python Thesaurus! Goodbye!\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def command_line_mode(word: str, offline: bool = False):
    """Run thesaurus for a single word"""
    thesaurus = Thesaurus(offline_mode=offline)

    mode_str = "OFFLINE (Moby)" if offline else "ONLINE"
    print(f"\n[\033[93m{mode_str}\033[0m] Results for: \033[1m'{word}'\033[0m")
    print('='*50)

    synonyms = thesaurus.get_synonyms(word)
    print_results("Synonyms", synonyms, "94")

    related = thesaurus.get_related_words(word)
    print_results("Related Words", related, "93")

    if not offline:
        antonyms = thesaurus.get_antonyms(word)
        print_results("Antonyms", antonyms, "91")

    print()


def main():
    """Main entry point"""
    # Default to offline if Moby available and --online not specified
    online_forced = '--online' in sys.argv
    offline_forced = '--offline' in sys.argv

    if online_forced:
        offline = False
    elif offline_forced or MOBY_AVAILABLE:
        offline = True
    else:
        offline = False

    args = [arg for arg in sys.argv[1:] if arg not in ('--offline', '--online')]

    if args:
        # Command-line mode with argument
        word = ' '.join(args).lower()
        command_line_mode(word, offline=offline)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()

