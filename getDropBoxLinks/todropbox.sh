#!/bin/bash
# Copy source to a Dropbox URL
# Usage:
#   todropbox . https://www.dropbox.com/home/notes/resume/resume-versions
#   todropbox ./folder https://www.dropbox.com/home/chess
todropbox() {
    local source="$1"
    local url="$2"

    if [[ -z "$source" || -z "$url" ]]; then
        echo "Usage: todropbox <source-dir> <dropbox-url>"
        return 1
    fi

    # Convert Dropbox URL to rclone path
    local dropbox_path
    if [[ "$url" == *"/home/"* ]]; then
        dropbox_path="dropbox:/${url#*/home/}"
    elif [[ "$url" == "dropbox:"* ]]; then
        dropbox_path="$url"
    elif [[ "$url" == /* ]]; then
        dropbox_path="dropbox:$url"
    else
        dropbox_path="dropbox:/$url"
    fi

    echo "$(date): Copying $source -> $dropbox_path"
    rclone copy "$source" "$dropbox_path"
    echo "$(date): Done"
}
