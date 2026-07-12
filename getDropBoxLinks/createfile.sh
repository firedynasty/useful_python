#!/bin/bash
# Create a .md file from clipboard and upload to Dropbox via rclone
# Usage:
#   createfile https://www.dropbox.com/home/notes/resume
#   createfile dropbox:/notes/resume
#   createfile /notes/resume
createfile() {
    local url="$1"

    if [[ -z "$url" ]]; then
        echo "Usage: createfile <dropbox-url>"
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

    # Generate filename with date and time (matches AppleScript format)
    local the_date
    the_date=$(date '+%Y-%m-%d at %-l.%M.%S %p')
    local filename="Screenshot ${the_date}.md"

    # Create temp directory and file from clipboard
    local tmpdir
    tmpdir=$(mktemp -d)
    local tmpfile="${tmpdir}/${filename}"

    pbpaste > "$tmpfile"

    if [[ ! -s "$tmpfile" ]]; then
        echo "Error: Clipboard is empty"
        rm -rf "$tmpdir"
        return 1
    fi

    # Upload to Dropbox via rclone
    echo "Uploading: ${filename}"
    echo "      To: ${dropbox_path}"
    rclone copy "$tmpfile" "$dropbox_path"
    local rc=$?

    # Cleanup
    rm -rf "$tmpdir"

    if [[ $rc -eq 0 ]]; then
        echo "Done: ${dropbox_path}/${filename}"
    else
        echo "Error: rclone failed (exit code $rc)"
        return $rc
    fi
}
