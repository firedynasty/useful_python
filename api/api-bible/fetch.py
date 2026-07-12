import os
import re
import sys
import subprocess
import requests

API_KEY = os.environ.get("API_BIBLE_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://rest.api.bible/v1"

# CEV Bible ID (cached after first lookup)
CEV_BIBLE_ID = None

# Book name to API abbreviation mapping
BOOK_ABBREV = {
    "genesis": "GEN", "gen": "GEN", "gn": "GEN",
    "exodus": "EXO", "exo": "EXO", "exod": "EXO", "ex": "EXO",
    "leviticus": "LEV", "lev": "LEV", "lv": "LEV",
    "numbers": "NUM", "num": "NUM", "nm": "NUM",
    "deuteronomy": "DEU", "deut": "DEU", "deu": "DEU", "dt": "DEU",
    "joshua": "JOS", "josh": "JOS", "jos": "JOS", "js": "JOS",
    "judges": "JDG", "judg": "JDG", "jdg": "JDG",
    "ruth": "RUT", "rut": "RUT", "rt": "RUT",
    "1 samuel": "1SA", "1samuel": "1SA", "1sam": "1SA", "1 sam": "1SA", "1sm": "1SA",
    "2 samuel": "2SA", "2samuel": "2SA", "2sam": "2SA", "2 sam": "2SA", "2sm": "2SA",
    "1 kings": "1KI", "1kings": "1KI", "1kgs": "1KI", "1 kgs": "1KI",
    "2 kings": "2KI", "2kings": "2KI", "2kgs": "2KI", "2 kgs": "2KI",
    "1 chronicles": "1CH", "1chronicles": "1CH", "1chr": "1CH", "1 chr": "1CH", "1ch": "1CH",
    "2 chronicles": "2CH", "2chronicles": "2CH", "2chr": "2CH", "2 chr": "2CH", "2ch": "2CH",
    "ezra": "EZR", "ezr": "EZR",
    "nehemiah": "NEH", "neh": "NEH", "ne": "NEH",
    "esther": "EST", "est": "EST", "et": "EST",
    "job": "JOB",
    "psalms": "PSA", "psalm": "PSA", "psa": "PSA", "ps": "PSA",
    "proverbs": "PRO", "prov": "PRO", "pro": "PRO", "prv": "PRO",
    "ecclesiastes": "ECC", "eccl": "ECC", "ecc": "ECC", "ec": "ECC",
    "song of solomon": "SNG", "song of songs": "SNG", "song": "SNG", "sos": "SNG", "songs": "SNG", "so": "SNG",
    "isaiah": "ISA", "isa": "ISA", "is": "ISA",
    "jeremiah": "JER", "jer": "JER", "jr": "JER",
    "lamentations": "LAM", "lam": "LAM", "lm": "LAM",
    "ezekiel": "EZK", "ezek": "EZK", "eze": "EZK", "ez": "EZK",
    "daniel": "DAN", "dan": "DAN", "dn": "DAN",
    "hosea": "HOS", "hos": "HOS", "ho": "HOS",
    "joel": "JOL", "jol": "JOL", "jl": "JOL",
    "amos": "AMO", "amo": "AMO", "am": "AMO",
    "obadiah": "OBA", "oba": "OBA", "ob": "OBA",
    "jonah": "JON", "jon": "JON",
    "micah": "MIC", "mic": "MIC", "mi": "MIC",
    "nahum": "NAM", "nah": "NAM", "na": "NAM",
    "habakkuk": "HAB", "hab": "HAB", "hk": "HAB",
    "zephaniah": "ZEP", "zeph": "ZEP", "zep": "ZEP", "zp": "ZEP",
    "haggai": "HAG", "hag": "HAG", "hg": "HAG",
    "zechariah": "ZEC", "zech": "ZEC", "zec": "ZEC", "zc": "ZEC",
    "malachi": "MAL", "mal": "MAL", "ml": "MAL",
    "matthew": "MAT", "matt": "MAT", "mat": "MAT", "mt": "MAT",
    "mark": "MRK", "mrk": "MRK", "mk": "MRK",
    "luke": "LUK", "luk": "LUK", "lk": "LUK",
    "john": "JHN", "joh": "JHN", "jn": "JHN", "jo": "JHN", "jhn": "JHN",
    "acts": "ACT", "act": "ACT",
    "romans": "ROM", "rom": "ROM", "rm": "ROM",
    "1 corinthians": "1CO", "1corinthians": "1CO", "1cor": "1CO", "1 cor": "1CO", "1co": "1CO",
    "2 corinthians": "2CO", "2corinthians": "2CO", "2cor": "2CO", "2 cor": "2CO", "2co": "2CO",
    "galatians": "GAL", "gal": "GAL", "gl": "GAL",
    "ephesians": "EPH", "eph": "EPH",
    "philippians": "PHP", "phil": "PHP", "php": "PHP", "ph": "PHP",
    "colossians": "COL", "col": "COL", "cl": "COL",
    "1 thessalonians": "1TH", "1thessalonians": "1TH", "1thess": "1TH", "1 thess": "1TH", "1th": "1TH", "1ts": "1TH",
    "2 thessalonians": "2TH", "2thessalonians": "2TH", "2thess": "2TH", "2 thess": "2TH", "2th": "2TH", "2ts": "2TH",
    "1 timothy": "1TI", "1timothy": "1TI", "1tim": "1TI", "1 tim": "1TI", "1ti": "1TI", "1tm": "1TI",
    "2 timothy": "2TI", "2timothy": "2TI", "2tim": "2TI", "2 tim": "2TI", "2ti": "2TI", "2tm": "2TI",
    "titus": "TIT", "tit": "TIT", "tt": "TIT",
    "philemon": "PHM", "phm": "PHM", "phlm": "PHM",
    "hebrews": "HEB", "heb": "HEB", "hb": "HEB",
    "james": "JAS", "jas": "JAS", "jam": "JAS", "jm": "JAS",
    "1 peter": "1PE", "1peter": "1PE", "1pet": "1PE", "1 pet": "1PE", "1pe": "1PE",
    "2 peter": "2PE", "2peter": "2PE", "2pet": "2PE", "2 pet": "2PE", "2pe": "2PE",
    "1 john": "1JN", "1john": "1JN", "1jn": "1JN", "1 jn": "1JN", "1jo": "1JN",
    "2 john": "2JN", "2john": "2JN", "2jn": "2JN", "2 jn": "2JN", "2jo": "2JN",
    "3 john": "3JN", "3john": "3JN", "3jn": "3JN", "3 jn": "3JN", "3jo": "3JN",
    "jude": "JUD", "jud": "JUD", "jd": "JUD",
    "revelation": "REV", "rev": "REV", "revelations": "REV", "re": "REV",
}

def get_book_abbrev(book_name):
    """Convert book name to API abbreviation."""
    key = book_name.lower().strip()
    return BOOK_ABBREV.get(key, key.upper())

def get_bibles():
    """Fetch list of available bibles."""
    headers = {"api-key": API_KEY}
    response = requests.get(f"{BASE_URL}/bibles", headers=headers)
    response.raise_for_status()
    return response.json().get("data", [])

def get_books(bible_id):
    """Fetch list of books for a specific bible."""
    headers = {"api-key": API_KEY}
    response = requests.get(f"{BASE_URL}/bibles/{bible_id}/books", headers=headers)
    response.raise_for_status()
    return response.json().get("data", [])

def list_books(bible_id=None):
    """
    List books from a bible.
    If no bible_id provided, uses the first available bible (typically KJV or similar).
    """
    if bible_id is None:
        bibles = get_bibles()
        if not bibles:
            return []
        bible_id = bibles[0]["id"]

    return get_books(bible_id)

def get_english_bibles():
    """Fetch English bibles only."""
    headers = {"api-key": API_KEY}
    response = requests.get(f"{BASE_URL}/bibles", headers=headers, params={"language": "eng"})
    response.raise_for_status()
    return response.json().get("data", [])

def find_bible_by_abbreviation(abbreviation):
    """Find a specific bible by abbreviation (e.g., 'CEV', 'GNT', 'MSG', 'KJV')."""
    bibles = get_english_bibles()
    for bible in bibles:
        if abbreviation.upper() in bible.get("abbreviation", "").upper():
            return bible
    return None

def get_cev_bible_id():
    """Get the CEV Bible ID (cached)."""
    global CEV_BIBLE_ID
    if CEV_BIBLE_ID is None:
        bible = find_bible_by_abbreviation("CEV")
        if bible:
            CEV_BIBLE_ID = bible["id"]
    return CEV_BIBLE_ID

def get_verse(reference, bible_id=None):
    """
    Fetch a specific verse or passage.

    Args:
        reference: e.g., "john 3:16", "gen 1:1", "psalm 23:1-6"
        bible_id: Optional bible ID, defaults to CEV

    Returns:
        dict with verse text and metadata
    """
    if bible_id is None:
        bible_id = get_cev_bible_id()

    if not bible_id:
        return {"error": "Could not find CEV Bible"}

    # Parse reference: "john 3:16" or "1 john 1:9" or "psalm 23:1-6"
    # Handle numbered books like "1 john", "2 kings"
    match = re.match(r'^(\d?\s*\w+(?:\s+\w+)?)\s+(\d+):(\d+)(?:-(\d+))?$', reference.strip(), re.IGNORECASE)
    if not match:
        return {"error": f"Invalid reference format: {reference}. Use 'book chapter:verse' (e.g., 'john 3:16')"}

    book_name = match.group(1)
    chapter = match.group(2)
    verse_start = match.group(3)
    verse_end = match.group(4)

    book_abbrev = get_book_abbrev(book_name)

    # Build verse ID: JHN.3.16 or JHN.3.16-JHN.3.20
    if verse_end:
        verse_id = f"{book_abbrev}.{chapter}.{verse_start}-{book_abbrev}.{chapter}.{verse_end}"
    else:
        verse_id = f"{book_abbrev}.{chapter}.{verse_start}"

    headers = {"api-key": API_KEY}
    params = {"content-type": "text", "include-notes": "false", "include-titles": "false"}

    response = requests.get(f"{BASE_URL}/bibles/{bible_id}/passages/{verse_id}", headers=headers, params=params)

    if response.status_code == 404:
        return {"error": f"Verse not found: {reference}"}

    response.raise_for_status()
    data = response.json().get("data", {})

    # Clean up the text (remove verse numbers and extra whitespace)
    content = data.get("content", "")
    # Remove [verse_num] patterns and clean whitespace
    content = re.sub(r'\[\d+\]\s*', '', content)
    content = re.sub(r'\s+', ' ', content).strip()

    return {
        "reference": data.get("reference", reference),
        "text": content,
        "book": book_name,
        "chapter": chapter,
        "verse": verse_start if not verse_end else f"{verse_start}-{verse_end}"
    }

def get_chapter(book, chapter, bible_id=None):
    """
    Fetch an entire chapter.

    Args:
        book: Book name (e.g., "john", "genesis")
        chapter: Chapter number
        bible_id: Optional bible ID, defaults to CEV
    """
    if bible_id is None:
        bible_id = get_cev_bible_id()

    if not bible_id:
        return {"error": "Could not find CEV Bible"}

    book_abbrev = get_book_abbrev(book)
    chapter_id = f"{book_abbrev}.{chapter}"

    headers = {"api-key": API_KEY}
    params = {"content-type": "text", "include-notes": "false", "include-titles": "true"}

    response = requests.get(f"{BASE_URL}/bibles/{bible_id}/chapters/{chapter_id}", headers=headers, params=params)

    if response.status_code == 404:
        return {"error": f"Chapter not found: {book} {chapter}"}

    response.raise_for_status()
    data = response.json().get("data", {})

    return {
        "reference": data.get("reference", f"{book} {chapter}"),
        "text": data.get("content", ""),
        "book": book,
        "chapter": chapter
    }

def speak_text(text):
    """
    Speak text using gtts-cli and mpg123.
    Chunks text into 500-character segments for better TTS handling.
    """
    if not text:
        return

    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', text).strip()

    if not normalized:
        return

    # Chunk by 500 characters (same as playclipboard)
    chunk_size = 500
    text_length = len(normalized)
    total_chunks = (text_length + chunk_size - 1) // chunk_size

    for i in range(0, text_length, chunk_size):
        chunk = normalized[i:i + chunk_size]
        chunk_num = (i // chunk_size) + 1

        if total_chunks > 1:
            print(f"\nChunk {chunk_num} of {total_chunks}...")

        try:
            # Use gtts-cli piped to mpg123 (same as playclipboard)
            gtts_proc = subprocess.Popen(
                ["/Users/stanleytan/anaconda3/bin/gtts-cli", chunk],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            mpg123_proc = subprocess.Popen(
                ["/opt/homebrew/bin/mpg123", "-q", "-"],
                stdin=gtts_proc.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            gtts_proc.stdout.close()
            mpg123_proc.wait()
        except FileNotFoundError as e:
            print(f"TTS error: {e}", file=sys.stderr)
            print("Make sure gtts-cli and mpg123 are installed.", file=sys.stderr)
            break
        except Exception as e:
            print(f"TTS error: {e}", file=sys.stderr)
            break

def parse_reference(reference):
    """Parse a reference string into components."""
    match = re.match(r'^(\d?\s*\w+(?:\s+\w+)?)\s+(\d+):(\d+)(?:-(\d+))?$', reference.strip(), re.IGNORECASE)
    if not match:
        return None
    return {
        'book': match.group(1),
        'chapter': int(match.group(2)),
        'verse_start': int(match.group(3)),
        'verse_end': int(match.group(4)) if match.group(4) else int(match.group(3))
    }

def interactive_verse_mode(initial_reference):
    """Fetch verses with pagination for large ranges."""
    CHUNK_SIZE = 5

    parsed = parse_reference(initial_reference)
    if not parsed:
        print(f"Error: Invalid reference format: {initial_reference}", file=sys.stderr)
        sys.exit(1)

    book = parsed['book']
    chapter = parsed['chapter']
    current_start = parsed['verse_start']
    final_end = parsed['verse_end']

    while True:
        # Calculate chunk end
        verse_count = final_end - current_start + 1
        if verse_count > CHUNK_SIZE:
            current_end = current_start + CHUNK_SIZE - 1
        else:
            current_end = final_end

        # Build reference for this chunk
        if current_start == current_end:
            ref = f"{book} {chapter}:{current_start}"
        else:
            ref = f"{book} {chapter}:{current_start}-{current_end}"

        result = get_verse(ref)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            break

        print(f"\n{result['reference']} (CEV)")
        print(result['text'])

        # Speak the verse
        speak_text(result['text'])

        # Check if we've finished the requested range
        if current_end >= final_end:
            # Offer to continue to next verses
            print("\n[Enter] next verses | [r] repeat | [q] quit")
            try:
                choice = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == 'q':
                break
            elif choice == 'r':
                current_start = parsed['verse_start']
                final_end = parsed['verse_end']
                continue
            else:
                # Continue to next chunk after the original range
                current_start = final_end + 1
                final_end = current_start + CHUNK_SIZE - 1
        else:
            # More verses in the original range
            print(f"\n[Enter] continue ({current_end + 1}-{final_end}) | [r] repeat | [q] quit")
            try:
                choice = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == 'q':
                break
            elif choice == 'r':
                continue
            else:
                current_start = current_end + 1

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        # verse mode: python fetch.py john 3:16
        reference = " ".join(sys.argv[1:])

        # Check if it's a large range (more than 5 verses)
        parsed = parse_reference(reference)
        if parsed and (parsed['verse_end'] - parsed['verse_start'] + 1) > 5:
            interactive_verse_mode(reference)
            sys.exit(0)

        result = get_verse(reference)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"{result['reference']} (CEV)")
        print(result['text'])

        # Read the verse aloud
        speak_text(result['text'])

        # Offer to continue
        print("\n[Enter] next verses | [r] repeat | [q] quit")
        try:
            choice = input().strip().lower()
            if choice == 'r':
                speak_text(result['text'])
            elif choice != 'q':
                # Continue to next verses
                if parsed:
                    next_start = parsed['verse_end'] + 1
                    next_ref = f"{parsed['book']} {parsed['chapter']}:{next_start}"
                    interactive_verse_mode(next_ref)
        except (EOFError, KeyboardInterrupt):
            pass

        sys.exit(0)
    # Preferred translations (easy to read)
    preferred = ["CEV", "GNT", "MSG", "KJV", "NIV"]

    print("Fetching English bibles...")
    bibles = get_english_bibles()

    print(f"\nFound {len(bibles)} English bibles.")
    print("\nAvailable translations:")
    for b in bibles:
        print(f"  - {b['abbreviation']}: {b['name']}")

    # Try to find a preferred translation
    selected = None
    for abbr in preferred:
        for bible in bibles:
            if abbr.upper() in bible.get("abbreviation", "").upper():
                selected = bible
                break
        if selected:
            break

    if not selected and bibles:
        selected = bibles[0]

    if selected:
        print(f"\n--- Using: {selected['name']} ({selected['abbreviation']}) ---")

        books = get_books(selected["id"])
        print(f"\nBooks ({len(books)}):")
        for book in books:
            print(f"  - {book['name']} ({book['id']})")
    else:
        print("No bibles found.")
