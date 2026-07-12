# Python Thesaurus App 📚

A simple command-line thesaurus application that finds synonyms, antonyms, related words, and rhymes. Works both **online** (using Datamuse API) and **offline** (using Moby Thesaurus).

## Two Versions Available

### 1. **thesaurus_simple.py** (Simple)

- ✅ Works offline with built-in synonym/antonym database
- ✅ Auto-fallback when internet unavailable
- ✅ 30+ common words pre-loaded
- ✅ Perfect for learning and basic use

### 2. **thesaurus.py** (Recommended - Full Moby Thesaurus)

- ✅ Uses the comprehensive Moby Thesaurus (words.txt)
- ✅ 30,000+ word entries with extensive synonym lists
- ✅ No additional setup required - uses local words.txt
- ✅ Works completely offline

## Features

- 🔍 Find **synonyms** for any word
- ⚡ Find **antonyms** (opposites)
- 🔗 Discover **related words** (online only)
- 🎵 Get **rhyming words** (online only)
- 💾 **Offline mode** with built-in database
- 💬 Interactive mode or single-word lookup
- 🎨 Colorful, formatted output

## Quick Start

### Installation

1. Make sure you have Python 3.6+ installed
2. Install dependencies:

```bash
pip install requests
```

### Usage

#### Interactive Mode (Recommended for Beginners)

Run without arguments to enter interactive mode:

```bash
python thesaurus_simple.py
```

Type any word and press Enter to see results. Type `quit` to exit.

#### Command-Line Mode

Look up a single word:

```bash
python thesaurus_simple.py happy
python thesaurus_simple.py beautiful
python thesaurus_simple.py --offline good
```

### Example Output

```bash
$ python thesaurus_simple.py happy

[ONLINE] Results for: 'happy'
==================================================

Synonyms:
  joyful, cheerful, content, pleased, delighted
  glad, merry, elated

Antonyms:
  sad, unhappy, miserable, depressed

Related Words: None found
```

## Offline Mode

The `thesaurus_simple.py` version includes a built-in database with 30+ common words:

- happy, sad, good, bad, big, small, fast, slow
- smart, beautiful, ugly, strong, weak, hot, cold
- new, old, love, hate, walk, run, talk, think
- see, hear, help, hurt, make, break, easy, hard
- important, unimportant

To force offline mode:

```bash
python thesaurus_simple.py --offline word
```

Or switch modes in interactive mode:

- Type `online` to use internet (Datamuse API)
- Type `offline` to use built-in database

## Full Version (thesaurus.py)

For comprehensive offline support with Moby Thesaurus:

```bash
# Simply run - no setup needed!
python thesaurus.py
```

This version includes:

- Access to 30,000+ word entries via Moby Thesaurus
- Extensive synonym lists (many words have 50+ synonyms)
- Related word lookup (words that share synonyms)
- Automatic fallback to online API if words.txt not found

## Commands (Interactive Mode)

- Type any word to search
- `help` - Show available information
- `online` - Switch to online mode (Datamuse API)
- `offline` - Switch to offline mode (built-in database)
- `quit` or `exit` - Exit the application

## How It Works

### Online Mode

Uses the free [Datamuse API](https://www.datamuse.com/api/) to fetch:

- **Synonyms**: Words with similar meanings
- **Antonyms**: Words with opposite meanings  
- **Related Words**: Words that are frequently associated
- **Rhymes**: Words that sound similar

### Offline Mode

Uses either:

- Built-in dictionary (thesaurus_simple.py) - 30+ common words
- Moby Thesaurus (thesaurus.py) - 30,000+ word entries with extensive synonyms

## Requirements

- Python 3.6 or higher
- `requests` library (for online mode only)
- Internet connection (for online mode only)
- `words.txt` in parent directory (for thesaurus.py offline mode)

## Tips

- **For beginners**: Use `thesaurus_simple.py` in offline mode
- **For writers**: Use online mode for extensive synonym lists
- **No internet**: Both versions auto-fallback to offline databases
- **Best experience**: Start with online mode, fallback to offline when needed

## License

Free to use and modify!
