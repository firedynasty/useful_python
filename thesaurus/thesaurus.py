#!/usr/bin/env python3
"""
Simple Thesaurus CLI Application
Finds synonyms, antonyms, and related words using the Datamuse API or WordNet (offline)
"""

import requests
import sys
from typing import List, Dict, Set

# Try to import NLTK for offline mode
try:
    from nltk.corpus import wordnet
    WORDNET_AVAILABLE = True
except ImportError:
    WORDNET_AVAILABLE = False

class Thesaurus:
    """A simple thesaurus class using the Datamuse API or WordNet"""
    
    BASE_URL = "https://api.datamuse.com/words"
    
    def __init__(self, offline_mode: bool = False):
        """Initialize thesaurus with mode selection"""
        self.offline_mode = offline_mode
        if offline_mode and not WORDNET_AVAILABLE:
            print("Warning: NLTK WordNet not available. Install with: pip install nltk")
            print("Then run: python -c 'import nltk; nltk.download(\"wordnet\")'")
    
    def _get_wordnet_synonyms(self, word: str) -> Set[str]:
        """Get synonyms using WordNet"""
        if not WORDNET_AVAILABLE:
            return set()
        
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym.lower() != word.lower():
                    synonyms.add(synonym)
        return synonyms
    
    def _get_wordnet_antonyms(self, word: str) -> Set[str]:
        """Get antonyms using WordNet"""
        if not WORDNET_AVAILABLE:
            return set()
        
        antonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                if lemma.antonyms():
                    for ant in lemma.antonyms():
                        antonym = ant.name().replace('_', ' ')
                        antonyms.add(antonym)
        return antonyms
    
    def _get_wordnet_definitions(self, word: str) -> List[str]:
        """Get definitions using WordNet"""
        if not WORDNET_AVAILABLE:
            return []
        
        definitions = []
        for syn in wordnet.synsets(word):
            definitions.append(syn.definition())
        return definitions[:5]  # Return top 5
    
    def get_synonyms(self, word: str, max_results: int = 20) -> List[Dict[str, any]]:
        """Get synonyms for a word"""
        if self.offline_mode:
            synonyms = self._get_wordnet_synonyms(word)
            return [{'word': syn, 'score': 0} for syn in list(synonyms)[:max_results]]
        
        params = {'ml': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # Fallback to offline mode
            if WORDNET_AVAILABLE:
                synonyms = self._get_wordnet_synonyms(word)
                return [{'word': syn, 'score': 0} for syn in list(synonyms)[:max_results]]
            return []
    
    def get_antonyms(self, word: str, max_results: int = 20) -> List[Dict[str, any]]:
        """Get antonyms for a word"""
        if self.offline_mode:
            antonyms = self._get_wordnet_antonyms(word)
            return [{'word': ant, 'score': 0} for ant in list(antonyms)[:max_results]]
        
        params = {'rel_ant': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # Fallback to offline mode
            if WORDNET_AVAILABLE:
                antonyms = self._get_wordnet_antonyms(word)
                return [{'word': ant, 'score': 0} for ant in list(antonyms)[:max_results]]
            return []
    
    def get_related_words(self, word: str, max_results: int = 15) -> List[Dict[str, any]]:
        """Get related words (triggers) - online only"""
        if self.offline_mode:
            return []
        
        params = {'rel_trg': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
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
    
    def get_definitions(self, word: str) -> List[str]:
        """Get definitions - offline only for now"""
        return self._get_wordnet_definitions(word)


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
    # Auto-detect mode: try online first, fallback to offline
    offline = not WORDNET_AVAILABLE
    mode_str = "OFFLINE MODE (WordNet)" if offline else "ONLINE MODE (Datamuse API)"
    
    thesaurus = Thesaurus(offline_mode=offline)
    print_banner()
    print(f"Running in: \033[93m{mode_str}\033[0m")
    print("Enter a word to find synonyms, antonyms, and more!")
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
                if not WORDNET_AVAILABLE:
                    print("\033[91mWordNet not available. Install NLTK first.\033[0m\n")
                    continue
                offline = True
                thesaurus = Thesaurus(offline_mode=True)
                print("\033[93mSwitched to OFFLINE MODE (WordNet)\033[0m\n")
                continue
            
            if user_input == 'help':
                print("\nAvailable information for each word:")
                print("  • Synonyms (words with similar meaning)")
                print("  • Antonyms (words with opposite meaning)")
                if not offline:
                    print("  • Related words (associated terms) - online only")
                    print("  • Rhymes (words that rhyme) - online only")
                else:
                    print("  • Definitions")
                print("\nCommands:")
                print("  • 'online' - Switch to online mode (requires internet)")
                print("  • 'offline' - Switch to offline mode (uses WordNet)")
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
            
            # Get and display antonyms
            antonyms = thesaurus.get_antonyms(user_input)
            print_results("Antonyms", antonyms, "91")
            
            # Get and display related words (online only)
            if not offline:
                related = thesaurus.get_related_words(user_input)
                print_results("Related Words", related, "93")
                
                # Get and display rhymes
                rhymes = thesaurus.get_rhymes(user_input)
                print_results("Rhymes", rhymes, "95")
            else:
                # Show definitions in offline mode
                definitions = thesaurus.get_definitions(user_input)
                if definitions:
                    print(f"\n\033[1mDefinitions:\033[0m")
                    for i, defn in enumerate(definitions, 1):
                        print(f"  {i}. {defn}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using Python Thesaurus! Goodbye!\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def command_line_mode(word: str, offline: bool = False):
    """Run thesaurus for a single word"""
    thesaurus = Thesaurus(offline_mode=offline)
    
    mode_str = "OFFLINE" if offline else "ONLINE"
    print(f"\n[\033[93m{mode_str}\033[0m] Results for: \033[1m'{word}'\033[0m")
    print('='*50)
    
    synonyms = thesaurus.get_synonyms(word)
    print_results("Synonyms", synonyms, "94")
    
    antonyms = thesaurus.get_antonyms(word)
    print_results("Antonyms", antonyms, "91")
    
    if not offline:
        related = thesaurus.get_related_words(word)
        print_results("Related Words", related, "93")
    else:
        definitions = thesaurus.get_definitions(word)
        if definitions:
            print(f"\n\033[1mDefinitions:\033[0m")
            for i, defn in enumerate(definitions, 1):
                print(f"  {i}. {defn}")
    
    print()


def main():
    """Main entry point"""
    offline = '--offline' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != '--offline']
    
    if args:
        # Command-line mode with argument
        word = ' '.join(args).lower()
        command_line_mode(word, offline=offline)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
