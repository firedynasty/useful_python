
playclipboard() {
    # Get clipboard content
    local text=$(pbpaste)
    
    # Check if clipboard is empty
    if [[ -z "$text" ]]; then
        echo "Clipboard is empty."
        return 1
    fi
    
    # Determine mode
    local continuous=false
    if [[ "$1" == "all" || "$1" == "a" ]]; then
        continuous=true
    fi
    
    # Split text into sentences
    # Split on . ! ? when followed by space and a capital letter starting a real word (Capital+lowercase)
    # This avoids splitting on: I. (roman numerals), 1. (numbers), Ps. (abbreviations)
    local sentences=$(echo "$text" | tr '\n' ' ' | sed -E 's/([.!?]) +([A-Z][a-z])/\1\n\2/g')
    
    # Read sentences into array and filter empty ones
    local sentence_array=()
    while IFS= read -r line; do
        local trimmed=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -n "$trimmed" ]]; then
            sentence_array+=("$trimmed")
        fi
    done <<< "$sentences"
    
    # Check if we have any sentences
    if [[ ${#sentence_array[@]} -eq 0 ]]; then
        echo "No text to speak."
        return 1
    fi
    
    # Group sentences into chunks of 5
    local chunk_size=5
    local total_sentences=${#sentence_array[@]}
    local chunk_num=0
    local total_chunks=$(( (total_sentences + chunk_size - 1) / chunk_size ))
    
    for ((i=0; i<total_sentences; i+=chunk_size)); do
        ((chunk_num++))
        
        # Get chunk of up to 5 sentences
        local chunk=""
        local sentences_in_chunk=0
        for ((j=0; j<chunk_size && i+j<total_sentences; j++)); do
            chunk+="${sentence_array[i+j]} "
            ((sentences_in_chunk++))
        done
        
        # Print the chunk first, then speak it
        echo "Speaking chunk $chunk_num of $total_chunks ($sentences_in_chunk sentences)..."
        echo ""
        echo "$chunk"
        echo ""
        
        # Speak the chunk
        /Users/stanleytan/anaconda3/bin/gtts-cli "$(printf %s "$chunk")" 2>/dev/null | /opt/homebrew/bin/mpg123 -q - 2>/dev/null
        
        # If not in continuous mode and not the last chunk, wait for Enter
        if ! $continuous && [[ $chunk_num -lt $total_chunks ]]; then
            echo ""
            echo "Press Enter to continue to next chunk (or Ctrl+C to stop)..."
            read
        fi
    done
    
    echo ""
    echo "Finished speaking $total_sentences sentences in $total_chunks chunks."
}

