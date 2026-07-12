#!/usr/bin/env python3
"""
Simple Thesaurus CLI Application
Works offline with built-in synonym database or online with Datamuse API
"""

import requests
import sys
from typing import List, Dict

# Built-in synonym database for offline mode
SYNONYM_DB = {
    'happy': ['joyful', 'cheerful', 'content', 'pleased', 'delighted', 'glad', 'merry', 'elated'],
    'sad': ['unhappy', 'sorrowful', 'dejected', 'melancholy', 'gloomy', 'depressed', 'miserable'],
    'good': ['excellent', 'fine', 'great', 'wonderful', 'superb', 'quality', 'nice', 'pleasant'],
    'bad': ['poor', 'awful', 'terrible', 'horrible', 'dreadful', 'inferior', 'unpleasant'],
    'big': ['large', 'huge', 'enormous', 'giant', 'massive', 'immense', 'vast', 'grand'],
    'small': ['tiny', 'little', 'minute', 'petite', 'compact', 'miniature', 'mini'],
    'fast': ['quick', 'rapid', 'swift', 'speedy', 'hasty', 'fleet', 'brisk'],
    'slow': ['sluggish', 'leisurely', 'gradual', 'unhurried', 'lazy', 'dawdling'],
    'smart': ['intelligent', 'clever', 'bright', 'brilliant', 'wise', 'sharp', 'astute'],
    'beautiful': ['pretty', 'lovely', 'gorgeous', 'attractive', 'stunning', 'elegant', 'handsome'],
    'ugly': ['unattractive', 'hideous', 'unsightly', 'plain', 'homely'],
    'strong': ['powerful', 'mighty', 'robust', 'sturdy', 'tough', 'muscular'],
    'weak': ['feeble', 'frail', 'fragile', 'delicate', 'powerless', 'ineffective'],
    'hot': ['warm', 'heated', 'burning', 'scorching', 'boiling', 'sweltering'],
    'cold': ['cool', 'chilly', 'freezing', 'icy', 'frigid', 'frosty'],
    'new': ['fresh', 'recent', 'modern', 'novel', 'latest', 'contemporary'],
    'old': ['ancient', 'aged', 'antique', 'elderly', 'vintage', 'archaic'],
    'love': ['adore', 'cherish', 'treasure', 'appreciate', 'admire', 'care for'],
    'hate': ['detest', 'loathe', 'despise', 'abhor', 'dislike'],
    'walk': ['stroll', 'saunter', 'amble', 'stride', 'march', 'hike'],
    'run': ['sprint', 'dash', 'race', 'jog', 'rush', 'hurry'],
    'talk': ['speak', 'converse', 'chat', 'discuss', 'communicate', 'say'],
    'think': ['ponder', 'consider', 'contemplate', 'reflect', 'meditate', 'reason'],
    'see': ['view', 'observe', 'watch', 'notice', 'spot', 'glimpse', 'perceive'],
    'hear': ['listen', 'overhear', 'detect', 'perceive'],
    'help': ['assist', 'aid', 'support', 'facilitate', 'enable'],
    'hurt': ['harm', 'injure', 'damage', 'wound', 'pain'],
    'make': ['create', 'build', 'construct', 'produce', 'manufacture', 'craft'],
    'break': ['shatter', 'smash', 'crack', 'fracture', 'destroy', 'demolish'],
    'easy': ['simple', 'effortless', 'straightforward', 'uncomplicated', 'basic'],
    'hard': ['difficult', 'challenging', 'tough', 'arduous', 'demanding', 'complex'],
    'important': ['significant', 'crucial', 'vital', 'essential', 'key', 'critical'],
    'unimportant': ['trivial', 'insignificant', 'minor', 'petty', 'negligible'],
}

ANTONYM_DB = {
    'happy': ['sad', 'unhappy', 'miserable', 'depressed'],
    'sad': ['happy', 'joyful', 'cheerful', 'glad'],
    'good': ['bad', 'poor', 'terrible', 'awful'],
    'bad': ['good', 'excellent', 'great', 'wonderful'],
    'big': ['small', 'tiny', 'little', 'minute'],
    'small': ['big', 'large', 'huge', 'enormous'],
    'fast': ['slow', 'sluggish', 'leisurely'],
    'slow': ['fast', 'quick', 'rapid', 'swift'],
    'hot': ['cold', 'cool', 'chilly', 'freezing'],
    'cold': ['hot', 'warm', 'heated', 'burning'],
    'new': ['old', 'ancient', 'aged', 'antique'],
    'old': ['new', 'fresh', 'recent', 'modern'],
    'love': ['hate', 'detest', 'loathe', 'despise'],
    'hate': ['love', 'adore', 'cherish', 'like'],
    'strong': ['weak', 'feeble', 'frail', 'fragile'],
    'weak': ['strong', 'powerful', 'mighty', 'robust'],
    'easy': ['hard', 'difficult', 'challenging', 'tough'],
    'hard': ['easy', 'simple', 'effortless'],
    'important': ['unimportant', 'trivial', 'insignificant'],
    'beautiful': ['ugly', 'unattractive', 'hideous'],
}


class Thesaurus:
    """A simple thesaurus class using Datamuse API or built-in database"""
    
    BASE_URL = "https://api.datamuse.com/words"
    
    def __init__(self, offline_mode: bool = False):
        """Initialize thesaurus with mode selection"""
        self.offline_mode = offline_mode
    
    def get_synonyms(self, word: str, max_results: int = 20) -> List[Dict[str, any]]:
        """Get synonyms for a word"""
        if self.offline_mode:
            synonyms = SYNONYM_DB.get(word.lower(), [])
            return [{'word': syn, 'score': 0} for syn in synonyms[:max_results]]
        
        params = {'ml': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # Fallback to offline mode
            synonyms = SYNONYM_DB.get(word.lower(), [])
            return [{'word': syn, 'score': 0} for syn in synonyms[:max_results]]
    
    def get_antonyms(self, word: str, max_results: int = 20) -> List[Dict[str, any]]:
        """Get antonyms for a word"""
        if self.offline_mode:
            antonyms = ANTONYM_DB.get(word.lower(), [])
            return [{'word': ant, 'score': 0} for ant in antonyms[:max_results]]
        
        params = {'rel_ant': word, 'max': max_results}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # Fallback to offline mode
            antonyms = ANTONYM_DB.get(word.lower(), [])
            return [{'word': ant, 'score': 0} for ant in antonyms[:max_results]]
    
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
    # Start with offline mode (built-in database)
    offline = True
    mode_str = "OFFLINE MODE (Built-in Database)"
    
    thesaurus = Thesaurus(offline_mode=offline)
    print_banner()
    print(f"Running in: \033[93m{mode_str}\033[0m")
    print("Enter a word to find synonyms and antonyms!")
    print("Commands: 'quit' or 'exit' to leave, 'help' for options")
    print("         'online' to try online mode, 'offline' for built-in database\n")
    
    while True:
        try:
            user_input = input("\033[92m🔍 Enter word: \033[0m").strip().lower()
            
            if user_input in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using Python Thesaurus! Goodbye!\n")
                break
            
            if user_input == 'online':
                offline = False
                thesaurus = Thesaurus(offline_mode=False)
                print("\033[93mSwitched to ONLINE MODE (Datamuse API)\033[0m")
                print("Note: Online mode requires internet connection\n")
                continue
            
            if user_input == 'offline':
                offline = True
                thesaurus = Thesaurus(offline_mode=True)
                print("\033[93mSwitched to OFFLINE MODE (Built-in Database)\033[0m\n")
                continue
            
            if user_input == 'help':
                print("\nAvailable information for each word:")
                print("  • Synonyms (words with similar meaning)")
                print("  • Antonyms (words with opposite meaning)")
                if not offline:
                    print("  • Related words (associated terms) - online only")
                    print("  • Rhymes (words that rhyme) - online only")
                print("\nCommands:")
                print("  • 'online' - Switch to online mode (requires internet)")
                print("  • 'offline' - Switch to offline mode (built-in database)")
                print("  • 'quit' or 'exit' - Exit the application")
                print("\nOffline database includes common words like:")
                print("  happy, sad, good, bad, big, small, fast, slow, etc.\n")
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
