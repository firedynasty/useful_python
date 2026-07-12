


# The _bible_audio_map function returns a pipe-delimited string with three parts:
#
#   folder|prefix|format
#
#   For example:
#   - romans|romans|01 → ~/bible/Romans/romans01.mp3
#   - 1_Corinthians|1_Corinthians|01 → ~/bible/1_Corinthians/1_Corinthians01.mp3
#   - Ruth|Ruth|1 → ~/bible/Ruth/Ruth1.mp3
#   - Obadiah|Obadiah|none → ~/bible/Obadiah/Obadiah.mp3
#
#   The three parts:
#
#   | Part   | Meaning                                | Examples                                                     |
#   |--------|----------------------------------------|--------------------------------------------------------------|
#   | folder | Directory name in ~/bible/             | Romans, 1_Corinthians, genesis                               |
#   | prefix | File name prefix before chapter number | romans, 1_Corinthians, FirstSamuel                           |
#   | format | How chapter number is formatted        | 01 = two-digit (01, 02), 1 = single (1, 2), none = no number |
#
#   Then in bibleaudio(), lines 348-355:
#
#   if [[ "$format" == "none" ]]; then
#     audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}.mp3"
#   elif [[ "$format" == "01" ]]; then
#     audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}$(printf "%02d" $chapter).mp3"
#   else
#     audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}${chapter}.mp3"
#   fi
#
#   I built this mapping by scanning what you actually have in each folder:
#   Romans/romans01.mp3          → romans|romans|01
#   1_Corinthians/1_Corinthians01.mp3 → 1_Corinthians|1_Corinthians|01
#   Ruth/Ruth1.mp3               → Ruth|Ruth|1
#   1_Samuel/FirstSamuel01.mp3   → 1_Samuel|FirstSamuel|01


#!/bin/bash
# Bible reading functions for terminal
# Source this file: source functions.sh

BIBLE_JSON="/Users/stanleytan/Documents/25-technical/46-python/grab_bible/en_web.json"
BIBLE_AUDIO_DIR="$HOME/bible"

# Book name to abbreviation mapping
_bible_abbrev() {
  local input=$(echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/^ *//;s/ *$//')
  case "$input" in
    # Genesis
    genesis|gen) echo "gn" ;;
    # Exodus
    exodus|exo|exod) echo "ex" ;;
    # Leviticus
    leviticus|lev) echo "lv" ;;
    # Numbers
    numbers|num) echo "nm" ;;
    # Deuteronomy
    deuteronomy|deut|deu) echo "dt" ;;
    # Joshua
    joshua|josh|jos) echo "js" ;;
    # Judges
    judges|judg) echo "jud" ;;
    # Ruth
    ruth) echo "rt" ;;
    # 1 Samuel
    "1 samuel"|"1samuel"|"1sam"|"1 sam"|"first samuel"|"i samuel") echo "1sm" ;;
    # 2 Samuel
    "2 samuel"|"2samuel"|"2sam"|"2 sam"|"second samuel"|"ii samuel") echo "2sm" ;;
    # 1 Kings
    "1 kings"|"1kings"|"1kgs"|"1 kgs"|"first kings"|"i kings") echo "1kgs" ;;
    # 2 Kings
    "2 kings"|"2kings"|"2kgs"|"2 kgs"|"second kings"|"ii kings") echo "2kgs" ;;
    # 1 Chronicles
    "1 chronicles"|"1chronicles"|"1chr"|"1 chr"|"first chronicles"|"i chronicles") echo "1ch" ;;
    # 2 Chronicles
    "2 chronicles"|"2chronicles"|"2chr"|"2 chr"|"second chronicles"|"ii chronicles") echo "2ch" ;;
    # Ezra
    ezra) echo "ezr" ;;
    # Nehemiah
    nehemiah|neh) echo "ne" ;;
    # Esther
    esther|est) echo "et" ;;
    # Job
    job) echo "job" ;;
    # Psalms
    psalms|psalm|psa|ps) echo "ps" ;;
    # Proverbs
    proverbs|prov|pro) echo "prv" ;;
    # Ecclesiastes
    ecclesiastes|eccl|ecc) echo "ec" ;;
    # Song of Solomon
    "song of solomon"|"song of songs"|"song"|"sos"|"songs") echo "so" ;;
    # Isaiah
    isaiah|isa) echo "is" ;;
    # Jeremiah
    jeremiah|jer) echo "jr" ;;
    # Lamentations
    lamentations|lam) echo "lm" ;;
    # Ezekiel
    ezekiel|ezek|eze) echo "ez" ;;
    # Daniel
    daniel|dan) echo "dn" ;;
    # Hosea
    hosea|hos) echo "ho" ;;
    # Joel
    joel) echo "jl" ;;
    # Amos
    amos) echo "am" ;;
    # Obadiah
    obadiah|oba|ob) echo "ob" ;;
    # Jonah
    jonah|jon) echo "jn" ;;
    # Micah
    micah|mic) echo "mi" ;;
    # Nahum
    nahum|nah) echo "na" ;;
    # Habakkuk
    habakkuk|hab) echo "hk" ;;
    # Zephaniah
    zephaniah|zeph|zep) echo "zp" ;;
    # Haggai
    haggai|hag) echo "hg" ;;
    # Zechariah
    zechariah|zech|zec) echo "zc" ;;
    # Malachi
    malachi|mal) echo "ml" ;;
    # Matthew
    matthew|matt|mat) echo "mt" ;;
    # Mark
    mark|mrk) echo "mk" ;;
    # Luke
    luke|luk) echo "lk" ;;
    # John (Gospel)
    john|joh|jn) echo "jo" ;;
    # Acts
    acts|act) echo "act" ;;
    # Romans
    romans|rom) echo "rm" ;;
    # 1 Corinthians
    "1 corinthians"|"1corinthians"|"1cor"|"1 cor"|"first corinthians"|"i corinthians") echo "1co" ;;
    # 2 Corinthians
    "2 corinthians"|"2corinthians"|"2cor"|"2 cor"|"second corinthians"|"ii corinthians") echo "2co" ;;
    # Galatians
    galatians|gal) echo "gl" ;;
    # Ephesians
    ephesians|eph) echo "eph" ;;
    # Philippians
    philippians|phil|php) echo "ph" ;;
    # Colossians
    colossians|col) echo "cl" ;;
    # 1 Thessalonians
    "1 thessalonians"|"1thessalonians"|"1thess"|"1 thess"|"first thessalonians"|"i thessalonians") echo "1ts" ;;
    # 2 Thessalonians
    "2 thessalonians"|"2thessalonians"|"2thess"|"2 thess"|"second thessalonians"|"ii thessalonians") echo "2ts" ;;
    # 1 Timothy
    "1 timothy"|"1timothy"|"1tim"|"1 tim"|"first timothy"|"i timothy") echo "1tm" ;;
    # 2 Timothy
    "2 timothy"|"2timothy"|"2tim"|"2 tim"|"second timothy"|"ii timothy") echo "2tm" ;;
    # Titus
    titus|tit) echo "tt" ;;
    # Philemon
    philemon|phm|phlm) echo "phm" ;;
    # Hebrews
    hebrews|heb) echo "hb" ;;
    # James
    james|jas|jam) echo "jm" ;;
    # 1 Peter
    "1 peter"|"1peter"|"1pet"|"1 pet"|"first peter"|"i peter") echo "1pe" ;;
    # 2 Peter
    "2 peter"|"2peter"|"2pet"|"2 pet"|"second peter"|"ii peter") echo "2pe" ;;
    # 1 John
    "1 john"|"1john"|"1jn"|"1 jn"|"first john"|"i john") echo "1jo" ;;
    # 2 John
    "2 john"|"2john"|"2jn"|"2 jn"|"second john"|"ii john") echo "2jo" ;;
    # 3 John
    "3 john"|"3john"|"3jn"|"3 jn"|"third john"|"iii john") echo "3jo" ;;
    # Jude
    jude) echo "jd" ;;
    # Revelation
    revelation|rev|revelations) echo "re" ;;
    # Already an abbreviation - pass through
    *) echo "$input" ;;
  esac
}

# Map book name to audio folder and file pattern
# Returns: folder|prefix|format
# format: 01 = two digit, 1 = single digit, none = no chapter number
_bible_audio_map() {
  local input=$(echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/^ *//;s/ *$//')
  case "$input" in
    genesis|gen|gn) echo "genesis|genesis|01" ;;
    exodus|exo|exod|ex) echo "exodus|exodus|01" ;;
    leviticus|lev|lv) echo "leviticus|Leviticus|01" ;;
    numbers|num|nm) echo "Numbers|Numbers|01" ;;
    deuteronomy|deut|deu|dt) echo "Deuteronomy|Deuteronomy|01" ;;
    joshua|josh|jos|js) echo "Joshua|Joshua|01" ;;
    judges|judg|jud) echo "Judges|Judges|01" ;;
    ruth|rt) echo "Ruth|Ruth|1" ;;
    "1 samuel"|"1samuel"|"1sam"|"1 sam"|"first samuel"|"i samuel"|1sm) echo "1_Samuel|FirstSamuel|01" ;;
    "2 samuel"|"2samuel"|"2sam"|"2 sam"|"second samuel"|"ii samuel"|2sm) echo "2_Samuel|SecondSamuel|01" ;;
    "1 kings"|"1kings"|"1kgs"|"1 kgs"|"first kings"|"i kings"|1kgs) echo "1_Kings|FirstKings|01" ;;
    "2 kings"|"2kings"|"2kgs"|"2 kgs"|"second kings"|"ii kings"|2kgs) echo "2_Kings|SecondKings|01" ;;
    "1 chronicles"|"1chronicles"|"1chr"|"1 chr"|"first chronicles"|"i chronicles"|1ch) echo "1_Chronicles|FirstChronicles|01" ;;
    "2 chronicles"|"2chronicles"|"2chr"|"2 chr"|"second chronicles"|"ii chronicles"|2ch) echo "2_Chronicles|SecondChronicles|01" ;;
    ezra|ezr) echo "Ezra|Ezra|01" ;;
    nehemiah|neh|ne) echo "Nehemiah|Nehemiah|01" ;;
    esther|est|et) echo "Esther|Esther|01" ;;
    job) echo "Job|Job|01" ;;
    psalms|psalm|psa|ps) echo "Psalms|Psalms|01" ;;
    proverbs|prov|pro|prv) echo "proverbs|Proverbs|01" ;;
    ecclesiastes|eccl|ecc|ec) echo "Ecclesiastes|Ecc|01" ;;
    "song of solomon"|"song of songs"|"song"|"sos"|"songs"|so) echo "Song_of_Solomon|Song|1" ;;
    isaiah|isa|is) echo "Isaiah|Isaiah|01" ;;
    jeremiah|jer|jr) echo "Jeremiah|Jeremiah|01" ;;
    lamentations|lam|lm) echo "Lamentations|Lamentations|1" ;;
    ezekiel|ezek|eze|ez) echo "Ezekiel|Ezekiel|01" ;;
    daniel|dan|dn) echo "Daniel|Daniel|01" ;;
    hosea|hos|ho) echo "Hosea|Hosea|01" ;;
    joel|jl) echo "joel|Joel|1" ;;
    amos|am) echo "amos|Amos|1" ;;
    obadiah|oba|ob) echo "Obadiah|Obadiah|none" ;;
    jonah|jon|jn) echo "Jonah|Jonah|1" ;;
    micah|mic|mi) echo "Micah|Micah|1" ;;
    nahum|nah|na) echo "Nahum|Nahum|1" ;;
    habakkuk|hab|hk) echo "Habakkuk|Habakkuk|1" ;;
    zephaniah|zeph|zep|zp) echo "Zephaniah|Zephaniah|1" ;;
    haggai|hag|hg) echo "Haggai|Haggai|1" ;;
    zechariah|zech|zec|zc) echo "Zechariah|Zechariah|01" ;;
    malachi|mal|ml) echo "Malachi|Malachi|1" ;;
    matthew|matt|mat|mt) echo "Matthew|matthew|01" ;;
    mark|mrk|mk) echo "Mark|Mark|01" ;;
    luke|luk|lk) echo "Luke|luke|01" ;;
    john|joh|jo) echo "john|john|01" ;;
    acts|act) echo "Acts|Acts|01" ;;
    romans|rom|rm) echo "Romans|romans|01" ;;
    "1 corinthians"|"1corinthians"|"1cor"|"1 cor"|"first corinthians"|"i corinthians"|1co) echo "1_Corinthians|1_Corinthians|01" ;;
    "2 corinthians"|"2corinthians"|"2cor"|"2 cor"|"second corinthians"|"ii corinthians"|2co) echo "2_Corinthians|2_corinthians|01" ;;
    galatians|gal|gl) echo "Galatians|galatians|1" ;;
    ephesians|eph) echo "Ephesians|ephesians|1" ;;
    philippians|phil|php|ph) echo "Philippians|philippians|1" ;;
    colossians|col|cl) echo "Colossians|colossians|1" ;;
    "1 thessalonians"|"1thessalonians"|"1thess"|"1 thess"|"first thessalonians"|"i thessalonians"|1ts) echo "1_Thessalonians|1_thessalonians|1" ;;
    "2 thessalonians"|"2thessalonians"|"2thess"|"2 thess"|"second thessalonians"|"ii thessalonians"|2ts) echo "2_Thessalonians|2_thessalonians|1" ;;
    "1 timothy"|"1timothy"|"1tim"|"1 tim"|"first timothy"|"i timothy"|1tm) echo "1_Timothy|1_timothy|1" ;;
    "2 timothy"|"2timothy"|"2tim"|"2 tim"|"second timothy"|"ii timothy"|2tm) echo "2_Timothy|2_timothy|1" ;;
    titus|tit|tt) echo "Titus|titus|1" ;;
    philemon|phm|phlm) echo "Philemon|57002 0_KJV_Bible-Philemon|none" ;;
    hebrews|heb|hb) echo "Hebrews|hebrews|01" ;;
    james|jas|jam|jm) echo "James|james|1" ;;
    "1 peter"|"1peter"|"1pet"|"1 pet"|"first peter"|"i peter"|1pe) echo "1_Peter|1-peter|1" ;;
    "2 peter"|"2peter"|"2pet"|"2 pet"|"second peter"|"ii peter"|2pe) echo "2_Peter|2-peter|1" ;;
    "1 john"|"1john"|"1jn"|"1 jn"|"first john"|"i john"|1jo) echo "1_John|1-john|1" ;;
    "2 john"|"2john"|"2jn"|"2 jn"|"second john"|"ii john"|2jo) echo "2_John|63007 0_KJV_Bible-2John|none" ;;
    "3 john"|"3john"|"3jn"|"3 jn"|"third john"|"iii john"|3jo) echo "3_john|64003 0_KJV_Bible-3John|none" ;;
    jude|jd) echo "Jude|Jude|1" ;;
    revelation|rev|revelations|re) echo "Revelation|Revelation|01" ;;
    *) echo "" ;;
  esac
}

# List all books
bible_books() {
  echo "Genesis (gen), Exodus (exo), Leviticus (lev), Numbers (num), Deuteronomy (deut)"
  echo "Joshua (josh), Judges (judg), Ruth, 1 Samuel (1sam), 2 Samuel (2sam)"
  echo "1 Kings (1kgs), 2 Kings (2kgs), 1 Chronicles (1chr), 2 Chronicles (2chr)"
  echo "Ezra, Nehemiah (neh), Esther (est), Job, Psalms (ps), Proverbs (prov)"
  echo "Ecclesiastes (ecc), Song of Solomon (song), Isaiah (isa), Jeremiah (jer)"
  echo "Lamentations (lam), Ezekiel (ezek), Daniel (dan), Hosea (hos), Joel, Amos"
  echo "Obadiah (oba), Jonah (jon), Micah (mic), Nahum (nah), Habakkuk (hab)"
  echo "Zephaniah (zeph), Haggai (hag), Zechariah (zech), Malachi (mal)"
  echo "Matthew (matt), Mark, Luke, John, Acts, Romans (rom)"
  echo "1 Corinthians (1cor), 2 Corinthians (2cor), Galatians (gal), Ephesians (eph)"
  echo "Philippians (phil), Colossians (col), 1 Thessalonians (1thess), 2 Thessalonians (2thess)"
  echo "1 Timothy (1tim), 2 Timothy (2tim), Titus (tit), Philemon (phm), Hebrews (heb)"
  echo "James (jas), 1 Peter (1pet), 2 Peter (2pet), 1 John (1jn), 2 John (2jn), 3 John (3jn)"
  echo "Jude, Revelation (rev)"
}

# State files for tracking current position
BIBLE_STATE="$HOME/.bible_state"
BIBLE_AUDIO_STATE="$HOME/.bible_audio_state"

# Get total chapters for a book
_bible_chapters() {
  local abbrev=$(_bible_abbrev "$1")
  jq -r --arg b "$abbrev" '.[] | select(.abbrev==$b) | .chapters | length' "$BIBLE_JSON"
}

# Read a chapter: bible genesis 1, bible gen 1, bible gn 1
# Also: bible next, bible prev
bible() {
  local book="$1"
  local chapter="${2:-1}"

  # Handle next/prev commands
  if [[ "$book" == "next" || "$book" == "prev" ]]; then
    if [[ ! -f "$BIBLE_STATE" ]]; then
      echo "No previous reading. Use: bible genesis 1"
      return 1
    fi
    source "$BIBLE_STATE"
    local total=$(_bible_chapters "$BIBLE_BOOK")
    if [[ "$book" == "next" ]]; then
      chapter=$((BIBLE_CHAPTER + 1))
      if [[ $chapter -gt $total ]]; then
        echo "End of $BIBLE_BOOK (chapter $total is the last)"
        return 1
      fi
    else
      chapter=$((BIBLE_CHAPTER - 1))
      if [[ $chapter -lt 1 ]]; then
        echo "Already at chapter 1"
        return 1
      fi
    fi
    book="$BIBLE_BOOK"
  fi

  local abbrev=$(_bible_abbrev "$book")

  # Save state
  echo "BIBLE_BOOK=\"$abbrev\"" > "$BIBLE_STATE"
  echo "BIBLE_CHAPTER=$chapter" >> "$BIBLE_STATE"

  # Display chapter
  echo "--- $abbrev $chapter ---"
  local output
  output=$(jq -r --arg b "$abbrev" --argjson c "$((chapter-1))" \
    '.[] | select(.abbrev==$b) | .chapters[$c] | to_entries | .[] | "\(.key+1). \(.value)"' \
    "$BIBLE_JSON" 2>&1)

  if [[ -z "$output" ]]; then
    echo "No content found for $abbrev chapter $chapter"
    echo "Debug: BIBLE_JSON=$BIBLE_JSON"
    echo "Debug: abbrev=$abbrev, chapter=$chapter"
    return 1
  fi

  echo "$output" | fold -s -w 80
}

# Search the Bible: bible_search "In the beginning"
bible_search() {
  jq -r --arg q "$1" \
    '.[] | .abbrev as $book | .chapters | to_entries[] | .key as $ch | .value | to_entries[] | select(.value | test($q; "i")) | "\($book) \($ch+1):\(.key+1) - \(.value)"' \
    "$BIBLE_JSON" | head -20
}

# Play Bible audio: bibleaudio genesis 1, bibleaudio gen 1
# Also: bibleaudio next, bibleaudio prev, bibleaudio stop
bibleaudio() {
  local book="$1"
  local chapter="${2:-1}"

  # Handle stop command
  if [[ "$book" == "stop" ]]; then
    pkill -f "afplay.*$BIBLE_AUDIO_DIR" 2>/dev/null && echo "Stopped playback" || echo "No audio playing"
    return 0
  fi

  # Handle next/prev commands
  if [[ "$book" == "next" || "$book" == "prev" ]]; then
    if [[ ! -f "$BIBLE_AUDIO_STATE" ]]; then
      echo "No previous audio. Use: bibleaudio genesis 1"
      return 1
    fi
    source "$BIBLE_AUDIO_STATE"

    if [[ "$book" == "next" ]]; then
      chapter=$((BIBLE_AUDIO_CHAPTER + 1))
    else
      chapter=$((BIBLE_AUDIO_CHAPTER - 1))
      if [[ $chapter -lt 1 ]]; then
        echo "Already at chapter 1"
        return 1
      fi
    fi
    book="$BIBLE_AUDIO_BOOK"
  fi

  # Get audio mapping
  local mapping=$(_bible_audio_map "$book")
  if [[ -z "$mapping" ]]; then
    echo "Unknown book: $book"
    echo "Use 'bible_books' to see available books"
    return 1
  fi

  local folder=$(echo "$mapping" | cut -d'|' -f1)
  local prefix=$(echo "$mapping" | cut -d'|' -f2)
  local format=$(echo "$mapping" | cut -d'|' -f3)

  # Build the file path
  local audio_file
  if [[ "$format" == "none" ]]; then
    audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}.mp3"
  elif [[ "$format" == "01" ]]; then
    audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}$(printf "%02d" $chapter).mp3"
  else
    audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}${chapter}.mp3"
  fi

  # Check if file exists
  if [[ ! -f "$audio_file" ]]; then
    echo "Audio file not found: $audio_file"
    # Try to list available files
    echo "Available chapters in $folder:"
    ls "$BIBLE_AUDIO_DIR/$folder/" 2>/dev/null | head -10
    return 1
  fi

  # Save state
  echo "BIBLE_AUDIO_BOOK=\"$book\"" > "$BIBLE_AUDIO_STATE"
  echo "BIBLE_AUDIO_CHAPTER=$chapter" >> "$BIBLE_AUDIO_STATE"

  # Stop any currently playing audio
  pkill -f "afplay.*$BIBLE_AUDIO_DIR" 2>/dev/null

  # Play the audio
  echo "Playing: $folder $chapter"
  echo "File: $audio_file"
  echo "(Press Ctrl+C to stop, or use 'bibleaudio stop')"

  afplay "$audio_file"
}

# Play audio in background
bibleaudio_bg() {
  local book="$1"
  local chapter="${2:-1}"

  # Stop any currently playing audio first
  pkill -f "afplay.*$BIBLE_AUDIO_DIR" 2>/dev/null

  # Get audio mapping
  local mapping=$(_bible_audio_map "$book")
  if [[ -z "$mapping" ]]; then
    echo "Unknown book: $book"
    return 1
  fi

  local folder=$(echo "$mapping" | cut -d'|' -f1)
  local prefix=$(echo "$mapping" | cut -d'|' -f2)
  local format=$(echo "$mapping" | cut -d'|' -f3)

  local audio_file
  if [[ "$format" == "none" ]]; then
    audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}.mp3"
  elif [[ "$format" == "01" ]]; then
    audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}$(printf "%02d" $chapter).mp3"
  else
    audio_file="$BIBLE_AUDIO_DIR/$folder/${prefix}${chapter}.mp3"
  fi

  if [[ ! -f "$audio_file" ]]; then
    echo "Audio file not found: $audio_file"
    return 1
  fi

  # Save state
  echo "BIBLE_AUDIO_BOOK=\"$book\"" > "$BIBLE_AUDIO_STATE"
  echo "BIBLE_AUDIO_CHAPTER=$chapter" >> "$BIBLE_AUDIO_STATE"

  echo "Playing in background: $folder $chapter"
  afplay "$audio_file" &
  echo "Use 'bibleaudio stop' to stop playback"
}

# Matthew Henry Commentary directory
MHC_DIR="$HOME/matthew_henry"

# Map book name to Matthew Henry book number (01-66)
_bible_mhc_book_num() {
  local input=$(echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/^ *//;s/ *$//')
  case "$input" in
    genesis|gen|gn) echo "01" ;;
    exodus|exo|exod|ex) echo "02" ;;
    leviticus|lev|lv) echo "03" ;;
    numbers|num|nm) echo "04" ;;
    deuteronomy|deut|deu|dt) echo "05" ;;
    joshua|josh|jos|js) echo "06" ;;
    judges|judg|jud) echo "07" ;;
    ruth|rt) echo "08" ;;
    "1 samuel"|"1samuel"|"1sam"|"1 sam"|"first samuel"|"i samuel"|1sm) echo "09" ;;
    "2 samuel"|"2samuel"|"2sam"|"2 sam"|"second samuel"|"ii samuel"|2sm) echo "10" ;;
    "1 kings"|"1kings"|"1kgs"|"1 kgs"|"first kings"|"i kings"|1kgs) echo "11" ;;
    "2 kings"|"2kings"|"2kgs"|"2 kgs"|"second kings"|"ii kings"|2kgs) echo "12" ;;
    "1 chronicles"|"1chronicles"|"1chr"|"1 chr"|"first chronicles"|"i chronicles"|1ch) echo "13" ;;
    "2 chronicles"|"2chronicles"|"2chr"|"2 chr"|"second chronicles"|"ii chronicles"|2ch) echo "14" ;;
    ezra|ezr) echo "15" ;;
    nehemiah|neh|ne) echo "16" ;;
    esther|est|et) echo "17" ;;
    job) echo "18" ;;
    psalms|psalm|psa|ps) echo "19" ;;
    proverbs|prov|pro|prv) echo "20" ;;
    ecclesiastes|eccl|ecc|ec) echo "21" ;;
    "song of solomon"|"song of songs"|"song"|"sos"|"songs"|so) echo "22" ;;
    isaiah|isa|is) echo "23" ;;
    jeremiah|jer|jr) echo "24" ;;
    lamentations|lam|lm) echo "25" ;;
    ezekiel|ezek|eze|ez) echo "26" ;;
    daniel|dan|dn) echo "27" ;;
    hosea|hos|ho) echo "28" ;;
    joel|jl) echo "29" ;;
    amos|am) echo "30" ;;
    obadiah|oba|ob) echo "31" ;;
    jonah|jon|jn) echo "32" ;;
    micah|mic|mi) echo "33" ;;
    nahum|nah|na) echo "34" ;;
    habakkuk|hab|hk) echo "35" ;;
    zephaniah|zeph|zep|zp) echo "36" ;;
    haggai|hag|hg) echo "37" ;;
    zechariah|zech|zec|zc) echo "38" ;;
    malachi|mal|ml) echo "39" ;;
    matthew|matt|mat|mt) echo "40" ;;
    mark|mrk|mk) echo "41" ;;
    luke|luk|lk) echo "42" ;;
    john|joh|jo) echo "43" ;;
    acts|act) echo "44" ;;
    romans|rom|rm) echo "45" ;;
    "1 corinthians"|"1corinthians"|"1cor"|"1 cor"|"first corinthians"|"i corinthians"|1co) echo "46" ;;
    "2 corinthians"|"2corinthians"|"2cor"|"2 cor"|"second corinthians"|"ii corinthians"|2co) echo "47" ;;
    galatians|gal|gl) echo "48" ;;
    ephesians|eph) echo "49" ;;
    philippians|phil|php|ph) echo "50" ;;
    colossians|col|cl) echo "51" ;;
    "1 thessalonians"|"1thessalonians"|"1thess"|"1 thess"|"first thessalonians"|"i thessalonians"|1ts) echo "52" ;;
    "2 thessalonians"|"2thessalonians"|"2thess"|"2 thess"|"second thessalonians"|"ii thessalonians"|2ts) echo "53" ;;
    "1 timothy"|"1timothy"|"1tim"|"1 tim"|"first timothy"|"i timothy"|1tm) echo "54" ;;
    "2 timothy"|"2timothy"|"2tim"|"2 tim"|"second timothy"|"ii timothy"|2tm) echo "55" ;;
    titus|tit|tt) echo "56" ;;
    philemon|phm|phlm) echo "57" ;;
    hebrews|heb|hb) echo "58" ;;
    james|jas|jam|jm) echo "59" ;;
    "1 peter"|"1peter"|"1pet"|"1 pet"|"first peter"|"i peter"|1pe) echo "60" ;;
    "2 peter"|"2peter"|"2pet"|"2 pet"|"second peter"|"ii peter"|2pe) echo "61" ;;
    "1 john"|"1john"|"1jn"|"1 jn"|"first john"|"i john"|1jo) echo "62" ;;
    "2 john"|"2john"|"2jn"|"2 jn"|"second john"|"ii john"|2jo) echo "63" ;;
    "3 john"|"3john"|"3jn"|"3 jn"|"third john"|"iii john"|3jo) echo "64" ;;
    jude|jd) echo "65" ;;
    revelation|rev|revelations|re) echo "66" ;;
    *) echo "" ;;
  esac
}



