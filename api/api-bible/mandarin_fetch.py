#!/usr/bin/env python3
"""
Fetch Bible verses from the local zh_cuv_no_spaces.json file (Chinese Union Version).
Usage: python mandarin_fetch.py john 3:16
       python mandarin_fetch.py psalm 23:1-6
       python mandarin_fetch.py 1 john 1:9
"""

import json
import os
import re
import subprocess
import sys

# Path to the CUV JSON file (default, can be overridden via CUV_BIBLE_JSON env var)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON_PATH = os.path.join(SCRIPT_DIR, "bibles", "zh_cuv_no_spaces.json")
JSON_PATH = os.environ.get("CUV_BIBLE_JSON", DEFAULT_JSON_PATH)

# Book name to abbreviation mapping (matching JSON format)
BOOK_ABBREV = {
    # Old Testament
    "genesis": "gn", "gen": "gn", "gn": "gn",
    "exodus": "ex", "exo": "ex", "exod": "ex", "ex": "ex",
    "leviticus": "lv", "lev": "lv", "lv": "lv",
    "numbers": "nm", "num": "nm", "nm": "nm",
    "deuteronomy": "dt", "deut": "dt", "deu": "dt", "dt": "dt",
    "joshua": "js", "josh": "js", "jos": "js", "js": "js",
    "judges": "jud", "judg": "jud", "jdg": "jud", "jud": "jud",
    "ruth": "rt", "rut": "rt", "rt": "rt",
    "1 samuel": "1sm", "1samuel": "1sm", "1sam": "1sm", "1 sam": "1sm", "1sm": "1sm",
    "first samuel": "1sm", "i samuel": "1sm",
    "2 samuel": "2sm", "2samuel": "2sm", "2sam": "2sm", "2 sam": "2sm", "2sm": "2sm",
    "second samuel": "2sm", "ii samuel": "2sm",
    "1 kings": "1kgs", "1kings": "1kgs", "1kgs": "1kgs", "1 kgs": "1kgs",
    "first kings": "1kgs", "i kings": "1kgs",
    "2 kings": "2kgs", "2kings": "2kgs", "2kgs": "2kgs", "2 kgs": "2kgs",
    "second kings": "2kgs", "ii kings": "2kgs",
    "1 chronicles": "1ch", "1chronicles": "1ch", "1chr": "1ch", "1 chr": "1ch", "1ch": "1ch",
    "first chronicles": "1ch", "i chronicles": "1ch",
    "2 chronicles": "2ch", "2chronicles": "2ch", "2chr": "2ch", "2 chr": "2ch", "2ch": "2ch",
    "second chronicles": "2ch", "ii chronicles": "2ch",
    "ezra": "ezr", "ezr": "ezr",
    "nehemiah": "ne", "neh": "ne", "ne": "ne",
    "esther": "et", "est": "et", "et": "et",
    "job": "job", "jb": "job",
    "psalms": "ps", "psalm": "ps", "psa": "ps", "ps": "ps",
    "proverbs": "prv", "prov": "prv", "pro": "prv", "prv": "prv",
    "ecclesiastes": "ec", "eccl": "ec", "ecc": "ec", "ec": "ec",
    "song of solomon": "so", "song of songs": "so", "song": "so", "sos": "so", "songs": "so", "so": "so",
    "isaiah": "is", "isa": "is", "is": "is",
    "jeremiah": "jr", "jer": "jr", "jr": "jr",
    "lamentations": "lm", "lam": "lm", "lm": "lm",
    "ezekiel": "ez", "ezek": "ez", "eze": "ez", "ez": "ez",
    "daniel": "dn", "dan": "dn", "dn": "dn",
    "hosea": "ho", "hos": "ho", "ho": "ho",
    "joel": "jl", "jol": "jl", "jl": "jl",
    "amos": "am", "amo": "am", "am": "am",
    "obadiah": "ob", "oba": "ob", "ob": "ob",
    "jonah": "jn", "jon": "jn", "jnh": "jn",  # Note: jn is Jonah, not John
    "micah": "mi", "mic": "mi", "mi": "mi",
    "nahum": "na", "nah": "na", "na": "na",
    "habakkuk": "hk", "hab": "hk", "hk": "hk",
    "zephaniah": "zp", "zeph": "zp", "zep": "zp", "zp": "zp",
    "haggai": "hg", "hag": "hg", "hg": "hg",
    "zechariah": "zc", "zech": "zc", "zec": "zc", "zc": "zc",
    "malachi": "ml", "mal": "ml", "ml": "ml",
    # New Testament
    "matthew": "mt", "matt": "mt", "mat": "mt", "mt": "mt",
    "mark": "mk", "mrk": "mk", "mk": "mk",
    "luke": "lk", "luk": "lk", "lk": "lk",
    "john": "jo", "joh": "jo", "jo": "jo",  # Gospel of John
    "acts": "act", "act": "act",
    "romans": "rm", "rom": "rm", "rm": "rm",
    "1 corinthians": "1co", "1corinthians": "1co", "1cor": "1co", "1 cor": "1co", "1co": "1co",
    "first corinthians": "1co", "i corinthians": "1co",
    "2 corinthians": "2co", "2corinthians": "2co", "2cor": "2co", "2 cor": "2co", "2co": "2co",
    "second corinthians": "2co", "ii corinthians": "2co",
    "galatians": "gl", "gal": "gl", "gl": "gl",
    "ephesians": "eph", "eph": "eph",
    "philippians": "ph", "phil": "ph", "php": "ph", "ph": "ph",
    "colossians": "cl", "col": "cl", "cl": "cl",
    "1 thessalonians": "1ts", "1thessalonians": "1ts", "1thess": "1ts", "1 thess": "1ts", "1th": "1ts", "1ts": "1ts",
    "first thessalonians": "1ts", "i thessalonians": "1ts",
    "2 thessalonians": "2ts", "2thessalonians": "2ts", "2thess": "2ts", "2 thess": "2ts", "2th": "2ts", "2ts": "2ts",
    "second thessalonians": "2ts", "ii thessalonians": "2ts",
    "1 timothy": "1tm", "1timothy": "1tm", "1tim": "1tm", "1 tim": "1tm", "1ti": "1tm", "1tm": "1tm",
    "first timothy": "1tm", "i timothy": "1tm",
    "2 timothy": "2tm", "2timothy": "2tm", "2tim": "2tm", "2 tim": "2tm", "2ti": "2tm", "2tm": "2tm",
    "second timothy": "2tm", "ii timothy": "2tm",
    "titus": "tt", "tit": "tt", "tt": "tt",
    "philemon": "phm", "phm": "phm", "phlm": "phm",
    "hebrews": "hb", "heb": "hb", "hb": "hb",
    "james": "jm", "jas": "jm", "jam": "jm", "jm": "jm",
    "1 peter": "1pe", "1peter": "1pe", "1pet": "1pe", "1 pet": "1pe", "1pe": "1pe",
    "first peter": "1pe", "i peter": "1pe",
    "2 peter": "2pe", "2peter": "2pe", "2pet": "2pe", "2 pet": "2pe", "2pe": "2pe",
    "second peter": "2pe", "ii peter": "2pe",
    "1 john": "1jo", "1john": "1jo", "1jn": "1jo", "1 jn": "1jo", "1jo": "1jo",
    "first john": "1jo", "i john": "1jo",
    "2 john": "2jo", "2john": "2jo", "2jn": "2jo", "2 jn": "2jo", "2jo": "2jo",
    "second john": "2jo", "ii john": "2jo",
    "3 john": "3jo", "3john": "3jo", "3jn": "3jo", "3 jn": "3jo", "3jo": "3jo",
    "third john": "3jo", "iii john": "3jo",
    "jude": "jd", "jud": "jd", "jd": "jd",
    "revelation": "re", "rev": "re", "revelations": "re", "re": "re",
}

# Full book names for display (Chinese)
BOOK_NAMES = {
    "gn": "創世記", "ex": "出埃及記", "lv": "利未記", "nm": "民數記", "dt": "申命記",
    "js": "約書亞記", "jud": "士師記", "rt": "路得記", "1sm": "撒母耳記上", "2sm": "撒母耳記下",
    "1kgs": "列王紀上", "2kgs": "列王紀下", "1ch": "歷代志上", "2ch": "歷代志下",
    "ezr": "以斯拉記", "ne": "尼希米記", "et": "以斯帖記", "job": "約伯記", "ps": "詩篇",
    "prv": "箴言", "ec": "傳道書", "so": "雅歌", "is": "以賽亞書",
    "jr": "耶利米書", "lm": "耶利米哀歌", "ez": "以西結書", "dn": "但以理書",
    "ho": "何西阿書", "jl": "約珥書", "am": "阿摩司書", "ob": "俄巴底亞書", "jn": "約拿書",
    "mi": "彌迦書", "na": "那鴻書", "hk": "哈巴谷書", "zp": "西番雅書", "hg": "哈該書",
    "zc": "撒迦利亞書", "ml": "瑪拉基書", "mt": "馬太福音", "mk": "馬可福音", "lk": "路加福音",
    "jo": "約翰福音", "act": "使徒行傳", "rm": "羅馬書", "1co": "哥林多前書", "2co": "哥林多後書",
    "gl": "加拉太書", "eph": "以弗所書", "ph": "腓立比書", "cl": "歌羅西書",
    "1ts": "帖撒羅尼迦前書", "2ts": "帖撒羅尼迦後書", "1tm": "提摩太前書", "2tm": "提摩太後書",
    "tt": "提多書", "phm": "腓利門書", "hb": "希伯來書", "jm": "雅各書", "1pe": "彼得前書",
    "2pe": "彼得後書", "1jo": "約翰一書", "2jo": "約翰二書", "3jo": "約翰三書", "jd": "猶大書",
    "re": "啟示錄",
}

# Cache for Bible data
_bible_data = None


def load_bible_data():
    """Load the Bible JSON data (cached)."""
    global _bible_data
    if _bible_data is None:
        with open(JSON_PATH, "r", encoding="utf-8-sig") as f:
            _bible_data = json.load(f)
    return _bible_data


def get_book_abbrev(book_name):
    """Convert book name to JSON abbreviation."""
    key = book_name.lower().strip()
    return BOOK_ABBREV.get(key, key)


def find_book_index(abbrev, bible_data):
    """Find the index of a book by its abbreviation."""
    for i, book in enumerate(bible_data):
        if book["abbrev"] == abbrev:
            return i
    return None


def get_verse(reference):
    """
    Fetch a specific verse or passage.

    Args:
        reference: e.g., "john 3:16", "gen 1:1", "psalm 23:1-6"

    Returns:
        dict with verse text and metadata
    """
    # Parse reference: "john 3:16" or "1 john 1:9" or "psalm 23:1-6"
    match = re.match(r'^(\d?\s*\w+(?:\s+\w+)?)\s+(\d+):(\d+)(?:-(\d+))?$', reference.strip(), re.IGNORECASE)
    if not match:
        return {"error": f"Invalid reference format: {reference}. Use 'book chapter:verse' (e.g., 'john 3:16')"}

    book_name = match.group(1)
    chapter = int(match.group(2))
    verse_start = int(match.group(3))
    verse_end = int(match.group(4)) if match.group(4) else verse_start

    book_abbrev = get_book_abbrev(book_name)
    bible_data = load_bible_data()

    book_index = find_book_index(book_abbrev, bible_data)
    if book_index is None:
        return {"error": f"Book not found: {book_name} (abbrev: {book_abbrev})"}

    book = bible_data[book_index]

    # Chapters are 0-indexed in JSON
    chapter_index = chapter - 1
    if chapter_index < 0 or chapter_index >= len(book["chapters"]):
        return {"error": f"Chapter {chapter} not found in {BOOK_NAMES.get(book_abbrev, book_name)}"}

    verses = book["chapters"][chapter_index]

    # Verses are 0-indexed in JSON
    if verse_start < 1 or verse_start > len(verses):
        return {"error": f"Verse {verse_start} not found in {BOOK_NAMES.get(book_abbrev, book_name)} {chapter}"}

    if verse_end > len(verses):
        verse_end = len(verses)

    # Extract verse(s)
    verse_texts = []
    for v in range(verse_start, verse_end + 1):
        verse_texts.append(verses[v - 1])

    text = " ".join(verse_texts)

    # Build reference string
    full_book_name = BOOK_NAMES.get(book_abbrev, book_name.title())
    if verse_start == verse_end:
        ref_str = f"{full_book_name} {chapter}:{verse_start}"
    else:
        ref_str = f"{full_book_name} {chapter}:{verse_start}-{verse_end}"

    return {
        "reference": ref_str,
        "text": text,
        "book": full_book_name,
        "chapter": chapter,
        "verse": verse_start if verse_start == verse_end else f"{verse_start}-{verse_end}"
    }


def speak_text(text):
    """
    Speak text using gtts-cli with Chinese language and sox for slowing down.
    """
    if not text:
        return

    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', text).strip()

    if not normalized:
        return

    # Chunk by 500 characters for TTS
    chunk_size = 500
    text_length = len(normalized)
    total_chunks = (text_length + chunk_size - 1) // chunk_size

    for i in range(0, text_length, chunk_size):
        chunk = normalized[i:i + chunk_size]
        chunk_num = (i // chunk_size) + 1

        if total_chunks > 1:
            print(f"\nChunk {chunk_num} of {total_chunks}...")

        try:
            # Generate TTS with gtts-cli in Chinese (slow mode)
            gtts_proc = subprocess.Popen(
                ["/Users/stanleytan/anaconda3/bin/gtts-cli", "-l", "zh", "--slow", chunk, "--output", "/tmp/temp.mp3"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            gtts_proc.wait()

            # Slow down the audio using sox
            sox_proc = subprocess.Popen(
                ["/opt/homebrew/bin/sox", "/tmp/temp.mp3", "/tmp/temp_slow.mp3", "tempo", "0.75"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            sox_proc.wait()

            # Play the slowed down file
            mpg123_proc = subprocess.Popen(
                ["/opt/homebrew/bin/mpg123", "-q", "/tmp/temp_slow.mp3"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            mpg123_proc.wait()

            # Clean up
            try:
                os.remove("/tmp/temp_slow.mp3")
            except OSError:
                pass

        except FileNotFoundError as e:
            print(f"TTS error: {e}", file=sys.stderr)
            print("Make sure gtts-cli, sox, and mpg123 are installed.", file=sys.stderr)
            break
        except Exception as e:
            print(f"TTS error: {e}", file=sys.stderr)
            break


if __name__ == "__main__":
    # Check for --speak flag
    speak = False
    args = sys.argv[1:]
    if "--speak" in args:
        speak = True
        args.remove("--speak")

    if len(args) < 1:
        print("Usage: python mandarin_fetch.py [--speak] <book> <chapter>:<verse>", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python mandarin_fetch.py john 3:16", file=sys.stderr)
        print("  python mandarin_fetch.py --speak john 3:16  (--speak will speak)", file=sys.stderr)
        print("  python mandarin_fetch.py psalm 23:1-6", file=sys.stderr)
        print("  python mandarin_fetch.py 1 john 1:9", file=sys.stderr)
        sys.exit(1)

    reference = " ".join(args)
    result = get_verse(reference)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"{result['reference']} (CUV)")
    print(result['text'])
    print("mandarinspeak will speak")

    if speak:
        speak_text(result['text'])
