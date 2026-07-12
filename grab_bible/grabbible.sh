#!/bin/bash

grabbible() {
    local current_dir=$(pwd)
    local script_dir="/Users/stanleytan/Documents/25-technical/46-python/grab_bible"
    local bible_file="$script_dir/bible_text.txt"

    # Check if we have exactly 1 argument (bible reference)
    if [[ $# -ne 1 ]]; then
        echo "Usage: grabbible <bible_reference>"
        echo "Examples:"
        echo "  grabbible \"genesis 10\"      # Get Genesis chapter 10"
        echo "  grabbible \"genesis 10:5\"    # Get starting from Genesis 10:5"
        echo "  grabbible \"john 3\"          # Get John chapter 3"
        return 1
    fi

    local reference="$1"

    # Check if bible file exists
    if [[ ! -f "$bible_file" ]]; then
        echo "Error: Bible file not found at '$bible_file'"
        return 1
    fi

    # Run the Python script with the bible file and reference
    (cd "$script_dir" && python3 grab_bible.py "$bible_file" "$reference")
}
