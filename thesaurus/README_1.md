# Python Thesaurus App 📚

A simple command-line thesaurus application that finds synonyms, antonyms, related words, and rhymes. Works both **online** (using Datamuse API) and **offline** (using built-in database).

## Two Versions Available

### 1. **thesaurus_simple.py** (Recommended)
- ✅ Works offline with built-in synonym/antonym database
- ✅ Auto-fallback when internet unavailable
- ✅ 30+ common words pre-loaded
- ✅ Perfect for learning and basic use

### 2. **thesaurus.py** (Advanced)
- Supports NLTK WordNet for extensive offline database
- Includes definitions
- Requires additional setup (see below)

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

## Advanced Version (thesaurus.py)

For more comprehensive offline support, use `thesaurus.py` with NLTK:

```bash
# Install NLTK
pip install nltk

# Download WordNet database
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

# Run
python thesaurus.py
```

This version includes:
- Access to 155,000+ words via WordNet
- Word definitions
- More comprehensive synonym/antonym lists

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
- NLTK WordNet (thesaurus.py) - 155,000+ words with definitions

## Requirements

- Python 3.6 or higher
- `requests` library
- Internet connection (for online mode)
- Optional: `nltk` library (for advanced offline mode)

## Tips

- **For beginners**: Use `thesaurus_simple.py` in offline mode
- **For writers**: Use online mode for extensive synonym lists
- **No internet**: Both versions auto-fallback to offline databases
- **Best experience**: Start with online mode, fallback to offline when needed

## License

Free to use and modify!
