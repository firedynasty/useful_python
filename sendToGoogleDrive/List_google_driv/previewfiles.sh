
previewfiles() {
    echo "Search recursively through subdirectories? (r/m)"
    echo "r = recursive (all subdirectories)"
    echo "m = max depth 1 (current directory only)"
    echo -n "Enter choice (r/m): "
    read choice
    
    # Function to extract preview text based on file type
    get_preview() {
        local file="$1"
        local preview=""
        
        case "${file##*.}" in
            rtf)
                # Extract text from RTF using textutil (macOS)
                if command -v textutil >/dev/null 2>&1; then
                    preview=$(textutil -convert txt -stdout "$file" 2>/dev/null | head -c 300 | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' || echo "[Could not extract RTF content]")
                else
                    preview="[textutil command not found - cannot read RTF files]"
                fi
                ;;
            docx)
                # Extract text from docx using pandoc
                if command -v pandoc >/dev/null 2>&1; then
                    preview=$(pandoc -t plain "$file" 2>/dev/null | head -c 300 | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' || echo "[Could not extract docx content]")
                else
                    preview="[pandoc command not found - cannot read docx files]"
                fi
                ;;
            pdf)
                # Extract text from PDF using pdftotext or pandoc
                if command -v pdftotext >/dev/null 2>&1; then
                    preview=$(pdftotext "$file" - 2>/dev/null | head -c 300 | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' || echo "[Could not extract PDF content]")
                elif command -v pandoc >/dev/null 2>&1; then
                    preview=$(pandoc -t plain "$file" 2>/dev/null | head -c 300 | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' || echo "[Could not extract PDF content]")
                else
                    preview="[pdftotext or pandoc command not found - cannot read PDF files]"
                fi
                ;;
            csv)
                # Show first few rows of CSV
                preview=$(head -5 "$file" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')
                ;;
            txt|md)
                preview=$(head -c 300 "$file" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')
                ;;
            *)
                preview="[Unsupported file type]"
                ;;
        esac
        echo "$preview"
    }
    
    case $choice in
        r|R)
            echo "Searching recursively..."
            echo "========================"
            find . -name "*.txt" -o -name "*.md" -o -name "*.docx" -o -name "*.pdf" -o -name "*.csv" -o -name "*.rtf" | sort | while read file; do
                if [[ -f "$file" ]]; then
                    echo "$file"
                    echo "***_______"
                    # Get preview based on file type
                    preview=$(get_preview "$file")
                    if [[ ${#preview} -gt 200 ]]; then
                        # Try to break at a sentence
                        echo "${preview:0:200}" | sed 's/\(.*\)\. .*/\1./'
                        echo "..."
                    else
                        echo "$preview"
                    fi
                    echo -e "\n"
                fi
            done
            ;;
        m|M)
            echo "Searching current directory only..."
            echo "==================================="
            # Set nullglob to handle cases where no files match the pattern
            setopt nullglob 2>/dev/null || shopt -s nullglob 2>/dev/null
            
            for file in *.txt *.md *.docx *.pdf *.csv *.rtf; do
                if [[ -f "$file" ]]; then
                    echo "$file"
                    echo "***_______"
                    # Get preview based on file type
                    preview=$(get_preview "$file")
                    if [[ ${#preview} -gt 200 ]]; then
                        # Try to break at a sentence
                        echo "${preview:0:200}" | sed 's/\(.*\)\. .*/\1./'
                        echo "..."
                    else
                        echo "$preview"
                    fi
                    echo -e "\n"
                fi
            done
            
            # Reset nullglob
            unsetopt nullglob 2>/dev/null || shopt -u nullglob 2>/dev/null
            ;;
        *)
            echo "Invalid choice. Please enter 'r' for recursive or 'm' for max depth 1."
            previewfiles
            ;;
    esac
}


copy() {
    # Check if at least one argument is provided
    if [ $# -eq 0 ]; then
        echo "Error: require argument" >&2
        return 1
    fi
    
    local all_contents=""
    
    # Loop through all arguments
    for file in "$@"; do
        # Check if file exists
        if [ ! -f "$file" ]; then
            echo "Warning: '$file' does not exist, skipping..." >&2
            continue
        fi
        
        local filename=$(basename "$file")
        local file_extension="${filename##*.}"
        
        # Add file header
        all_contents+="=== $filename ===${NL}"
        
        # Handle different file types
        case "$file_extension" in
            rtf)
                # Convert RTF to plain text
                if command -v textutil &> /dev/null; then
                    all_contents+="$(textutil -convert txt -stdout "$file" 2>/dev/null)"
                else
                    echo "Warning: textutil not found, skipping '$file'" >&2
                    continue
                fi
                ;;
            docx)
                # Convert DOCX using LibreOffice or other tools
                if [ -e "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
                    local temp_txt="${file%.*}.txt"
                    /Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to txt "$file" &>/dev/null
                    all_contents+="$(cat "$temp_txt" 2>/dev/null)"
                    rm -f "$temp_txt"
                elif command -v pandoc &> /dev/null; then
                    all_contents+="$(pandoc -t plain "$file" 2>/dev/null)"
                else
                    echo "Warning: No DOCX converter found, skipping '$file'" >&2
                    continue
                fi
                ;;
            txt|md|*)
                # Read text files directly
                all_contents+="$(cat "$file" 2>/dev/null)"
                ;;
        esac
        
        # Add spacing between files
        all_contents+="${NL}${NL}"
    done
    
    # Copy to clipboard
    if [ -n "$all_contents" ]; then
        echo -n "$all_contents" | pbcopy
        echo "✓ ${#@} file(s) copied to clipboard"
    else
        echo "Error: No content to copy" >&2
        return 1
    fi
}

# Define newline variable for better readability
NL=$'\n'
