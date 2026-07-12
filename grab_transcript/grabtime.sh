

grabtime() {
    local current_dir=$(pwd)
    local script_dir="/Users/stanleytan/Documents/25-technical/46-python/grab_transcript"
    
    # Check if we have 2 or 3 arguments (filename, timestamp, and optional question)
    if [[ $# -lt 2 ]] || [[ $# -gt 3 ]]; then
        echo "Usage: grabtime <transcript_file> <timestamp> [custom_question]"
        echo "Examples:"
        echo "  grabtime transcript.txt 1:23                    # Get 1 minute before 1:23 (default question)"
        echo "  grabtime video.txt 45:30                        # Get 1 minute before 45:30 (default question)"
        echo "  grabtime lecture.txt 1:15:45                    # Get 1 minute before 1:15:45 (default question)"
        echo "  grabtime transcript.txt 1:23 \"What are the main themes?\"  # Custom question"
        return 1
    fi
    
    local file_path="$1"
    local timestamp="$2"
    local custom_question="$3"
    
    # Make file path absolute if it's relative
    if [[ "$file_path" != /* ]]; then
        # Check if file exists in current directory
        if [[ -f "$current_dir/$file_path" ]]; then
            file_path="$current_dir/$file_path"
        elif [[ ! -f "$file_path" ]]; then
            echo "Error: File '$file_path' not found"
            return 1
        fi
    fi
    
    # Check if file exists
    if [[ ! -f "$file_path" ]]; then
        echo "Error: File '$file_path' not found"
        return 1
    fi
    
    # Validate timestamp format (M:SS, MM:SS, H:MM:SS, or HH:MM:SS)
    if ! [[ "$timestamp" =~ ^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$ ]]; then
        echo "Error: Invalid timestamp format '$timestamp'"
        echo "Use MM:SS (e.g., 1:23) or HH:MM:SS (e.g., 1:15:45)"
        return 1
    fi
    
    # Run the Python script with the absolute file path, timestamp, and optional custom question
    if [[ -n "$custom_question" ]]; then
        (cd "$script_dir" && python3 extract_transcript_segment.py "$file_path" "$timestamp" "$custom_question")
    else
        (cd "$script_dir" && python3 extract_transcript_segment.py "$file_path" "$timestamp")
    fi
}
