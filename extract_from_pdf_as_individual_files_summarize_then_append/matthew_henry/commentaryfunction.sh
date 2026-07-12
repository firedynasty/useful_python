# Enhanced commentary function with section extraction
commentary() {
  local book="$1"
  local chapter="${2:-1}"
  local section="${3:-}"

  if [[ -z "$book" ]]; then
    echo "Usage: commentary <book> [chapter] [section|open]"
    echo "Examples:"
    echo "  commentary genesis 1           # Interactive section prompt"
    echo "  commentary gen 5 2             # Extract section 2 to clipboard"
    echo "  commentary genesis 1 open      # Open in browser"
    echo "  commentary exodus 0            # preface"
    echo "Use 'bible_books' to see available books"
    return 1
  fi

  # Get MHC book number
  local book_num=$(_bible_mhc_book_num "$book")
  if [[ -z "$book_num" ]]; then
    echo "Unknown book: $book"
    echo "Use 'bible_books' to see available books"
    return 1
  fi

  # Pad chapter to 3 digits
  local chapter_padded=$(printf "%03d" "$chapter")

  # Build filename
  local filename="MHC${book_num}${chapter_padded}.HTM"
  local filepath="$MHC_DIR/$filename"

  # Check if file exists
  if [[ ! -f "$filepath" ]]; then
    echo "Commentary not found: $filepath"
    echo "Available chapters for book $book_num:"
    ls "$MHC_DIR/" 2>/dev/null | grep "^MHC${book_num}" | head -10
    return 1
  fi

  # If section is "open" or not provided, show interactive prompt
  if [[ "$section" == "open" ]]; then
    echo "Opening Matthew Henry Commentary: $book chapter $chapter"
    echo "File: $filename"
    open "$filepath"
    return 0
  fi

  # If no section provided, show interactive menu
  if [[ -z "$section" ]]; then
    echo "Matthew Henry Commentary: $book chapter $chapter"
    echo ""
    echo "Options:"
    echo "  1-10    Extract specific section to clipboard"
    echo "  open    Open full chapter in browser"
    echo "  all     Copy entire chapter to clipboard"
    echo ""
    echo -n "Enter choice: "
    read section
  fi

  # Handle "open" choice
  if [[ "$section" == "open" ]]; then
    echo "Opening in browser..."
    open "$filepath"
    return 0
  fi

  # Handle "all" or specific section
  _commentary_extract "$filepath" "$section" "$book" "$chapter"
}

# Extract section from HTML commentary and copy to clipboard
_commentary_extract() {
  local filepath="$1"
  local section="$2"
  local book="$3"
  local chapter="$4"

  # Convert HTML to text
  local text=""
  
  # Try different HTML to text converters (in order of preference)
  if command -v pandoc &> /dev/null; then
    text=$(pandoc -f html -t plain "$filepath" 2>/dev/null)
  elif command -v lynx &> /dev/null; then
    text=$(lynx -dump -nolist "$filepath" 2>/dev/null)
  elif command -v w3m &> /dev/null; then
    text=$(w3m -dump "$filepath" 2>/dev/null)
  elif command -v textutil &> /dev/null; then
    # macOS built-in converter
    text=$(textutil -convert txt -stdout "$filepath" 2>/dev/null)
  else
    echo "Error: No HTML converter found. Install pandoc, lynx, w3m, or use macOS textutil"
    return 1
  fi

  if [[ -z "$text" ]]; then
    echo "Error: Could not extract text from HTML"
    return 1
  fi

  # Handle different section requests
  if [[ "$section" == "all" ]]; then
    echo "$text" | pbcopy
    echo "✓ Copied entire commentary to clipboard"
    echo "Book: $book, Chapter: $chapter"
    return 0
  fi

  # Extract specific section (assuming sections are numbered or have headers)
  # Matthew Henry often uses "Verses 1-5" type headers
  # This regex looks for common section patterns
  local section_text=""
  
  # Try to find section by number (adjustable based on actual HTML structure)
  # This attempts to split by common MHC section markers
  section_text=$(echo "$text" | awk -v sec="$section" '
    BEGIN { 
      in_section = 0
      section_count = 0
      content = ""
    }
    # Look for verse range headers like "Verses 1-3" or section numbers
    /^[[:space:]]*(Verses|Ver\.|Section|Part|[IVX]+\.)/ {
      section_count++
      if (section_count == sec) {
        in_section = 1
        content = $0 "\n"
        next
      } else if (in_section) {
        exit
      }
    }
    # Collect content if in target section
    in_section { content = content $0 "\n" }
    END { print content }
  ')

  if [[ -n "$section_text" ]]; then
    echo "$section_text" | pbcopy
    echo "✓ Copied section $section to clipboard"
    echo "Book: $book, Chapter: $chapter"
  else
    # If structured extraction fails, fall back to paragraph splitting
    echo "$text" | awk -v sec="$section" -v RS="" "NR==$sec" | pbcopy
    if [[ $? -eq 0 ]]; then
      echo "✓ Copied paragraph $section to clipboard"
      echo "Book: $book, Chapter: $chapter"
    else
      echo "Error: Could not find section $section"
      echo "Try 'commentary $book $chapter open' to view in browser"
      return 1
    fi
  fi
}

# Quick clipboard view of what was copied
commentary_view() {
  echo "=== Clipboard Content ==="
  pbpaste | head -50
  echo ""
  echo "(Use 'pbpaste' to see full content or 'pbpaste | less' to page through)"
}
