#!/bin/bash

# Concatenate all MP3 files in a folder into one output file
# Usage: ./concat_mp3s.sh [input_folder] [output_file]
# Example: ./concat_mp3s.sh ./Psalms Psalms_complete.mp3

concatAllMp3sInFolder() {
    local input_folder="${1:-.}"
    local output_file="${2:-output_combined.mp3}"
    local temp_list="/tmp/ffmpeg_concat_list.txt"

    # Check if input folder exists
    if [[ ! -d "$input_folder" ]]; then
        echo "Error: Folder '$input_folder' does not exist."
        return 1
    fi

    # Check if there are MP3 files
    local mp3_count=$(ls "$input_folder"/*.mp3 2>/dev/null | wc -l)
    if [[ $mp3_count -eq 0 ]]; then
        echo "Error: No MP3 files found in '$input_folder'."
        return 1
    fi

    echo "Found $mp3_count MP3 files in '$input_folder'"

    # Create concat list with natural sort (handles Psalms1, Psalms2, ..., Psalms10, Psalms11, etc.)
    > "$temp_list"
    for f in $(ls "$input_folder"/*.mp3 | sort -V); do
        echo "file '$(realpath "$f")'" >> "$temp_list"
    done

    echo "Concatenating files..."
    echo "First file: $(head -1 "$temp_list" | sed "s/file '//;s/'//")"
    echo "Last file:  $(tail -1 "$temp_list" | sed "s/file '//;s/'//")"

    # Concatenate using ffmpeg concat demuxer
    ffmpeg -f concat -safe 0 -i "$temp_list" -c copy "$output_file" -y

    if [[ $? -eq 0 ]]; then
        echo ""
        echo "Success! Combined $mp3_count files into '$output_file'"
        echo "Output size: $(du -h "$output_file" | cut -f1)"
    else
        echo "Error: Failed to concatenate MP3 files."
        rm -f "$temp_list"
        return 1
    fi

    rm -f "$temp_list"
}

# Run if called directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    concatAllMp3sInFolder "$@"
fi
