#!/bin/bash
# Cloud Sync Functions - Google Drive & Dropbox via rclone
# Source this file in .zshrc: source ~/Documents/technical/46-python/sendToGoogleDrive/cloudsync.sh

# Helper: convert Google Drive URL to rclone path
_gdrive_path() {
    local input="$1"

    # Google Drive folder URL → extract folder ID
    if [[ "$input" == *"drive.google.com/drive/folders/"* ]]; then
        local folder_id="${input##*/drive/folders/}"
        folder_id="${folder_id%%\?*}"  # strip query params
        echo "--drive-root-folder-id=$folder_id"
        return 0
    fi

    # Google Drive file URL
    if [[ "$input" == *"drive.google.com/file/d/"* ]]; then
        local file_id="${input##*/file/d/}"
        file_id="${file_id%%/*}"
        echo "--drive-root-folder-id=$file_id"
        return 0
    fi

    # Already a path
    return 1
}

# Helper: convert Dropbox URL to rclone path (same logic as your todropbox)
_dropbox_path() {
    local url="$1"

    if [[ "$url" == *"/home/"* ]]; then
        echo "/${url#*/home/}"
    elif [[ "$url" == "dropbox:"* ]]; then
        echo "${url#dropbox:}"
    elif [[ "$url" == /* ]]; then
        echo "$url"
    else
        echo "/$url"
    fi
}

# ============================================================
# GOOGLE DRIVE
# ============================================================

# Copy local folder/file TO Google Drive
# Usage: togdrive ./folder "remote/path"
#        togdrive ./folder "https://drive.google.com/drive/folders/ABC123"
togdrive() {
    local source="$1"
    local dest="$2"

    if [[ -z "$source" || -z "$dest" ]]; then
        echo "Usage: togdrive <local-source> <gdrive-path-or-url>"
        return 1
    fi

    local extra_flag
    extra_flag=$(_gdrive_path "$dest")
    if [[ $? -eq 0 ]]; then
        echo "$(date): Copying $source -> gdrive: (folder ID from URL)"
        /opt/homebrew/bin/rclone copy"$source" "gdrive:" $extra_flag --progress
    else
        echo "$(date): Copying $source -> gdrive:$dest"
        /opt/homebrew/bin/rclone copy"$source" "gdrive:$dest" --progress
    fi
    echo "$(date): Done"
}

# Download FROM Google Drive to local
# Usage: fromgdrive "remote/path" ./local
#        fromgdrive "remote/path" .
#        fromgdrive "remote/path"              (defaults to current dir)
#        fromgdrive "https://drive.google.com/drive/folders/ABC123" ./local
fromgdrive() {
    local source="$1"
    local dest="${2:-.}"

    if [[ -z "$source" ]]; then
        echo "Usage: fromgdrive <gdrive-path-or-url> [local-dest]"
        echo "  dest defaults to current directory (.)"
        return 1
    fi

    local extra_flag
    extra_flag=$(_gdrive_path "$source")
    if [[ $? -eq 0 ]]; then
        echo "$(date): Downloading gdrive: (folder ID from URL) -> $dest"
        /opt/homebrew/bin/rclone copy"gdrive:" "$dest" $extra_flag --progress
    else
        echo "$(date): Downloading gdrive:$source -> $dest"
        /opt/homebrew/bin/rclone copy"gdrive:$source" "$dest" --progress
    fi
    echo "$(date): Done"
}

# Sync local folder TO Google Drive (mirror - deletes files on Drive not in local)
# Usage: gdsync ./folder "remote/path"
#        gdsync ./folder "https://drive.google.com/drive/folders/ABC123"
gdsync() {
    local source="$1"
    local dest="$2"

    if [[ -z "$source" || -z "$dest" ]]; then
        echo "Usage: gdsync <local-source> <gdrive-path-or-url>"
        echo "  WARNING: sync deletes files on destination not in source"
        return 1
    fi

    local extra_flag
    extra_flag=$(_gdrive_path "$dest")
    if [[ $? -eq 0 ]]; then
        echo "WARNING: This will delete files on Drive not present locally"
        echo "$(date): Syncing $source -> gdrive: (folder ID from URL)"
        /opt/homebrew/bin/rclone sync"$source" "gdrive:" $extra_flag --progress
    else
        echo "WARNING: This will delete files on Drive not present locally"
        echo "$(date): Syncing $source -> gdrive:$dest"
        /opt/homebrew/bin/rclone sync"$source" "gdrive:$dest" --progress
    fi
    echo "$(date): Done"
}

# Sync FROM Google Drive to local (mirror - deletes local files not on Drive)
# Usage: gdsyncdown "remote/path" ./local
#        gdsyncdown "remote/path" .
#        gdsyncdown "remote/path"                 (defaults to current dir)
#        gdsyncdown "https://drive.google.com/drive/folders/ABC123" .
gdsyncdown() {
    local source="$1"
    local dest="${2:-.}"

    if [[ -z "$source" ]]; then
        echo "Usage: gdsyncdown <gdrive-path-or-url> [local-dest]"
        echo "  dest defaults to current directory (.)"
        echo "  WARNING: sync deletes local files not on Drive"
        return 1
    fi

    local extra_flag
    extra_flag=$(_gdrive_path "$source")
    if [[ $? -eq 0 ]]; then
        echo "WARNING: This will delete local files in $dest not present on Drive"
        echo "$(date): Syncing gdrive: (folder ID from URL) -> $dest"
        /opt/homebrew/bin/rclone sync"gdrive:" "$dest" $extra_flag --progress
    else
        echo "WARNING: This will delete local files in $dest not present on Drive"
        echo "$(date): Syncing gdrive:$source -> $dest"
        /opt/homebrew/bin/rclone sync"gdrive:$source" "$dest" --progress
    fi
    echo "$(date): Done"
}

# List Google Drive folder contents
# Usage: gdls "remote/path"
#        gdls                        (lists root)
#        gdls "https://drive.google.com/drive/folders/ABC123"
gdls() {
    local path="${1:-}"

    if [[ -z "$path" ]]; then
        /opt/homebrew/bin/rclone lsdgdrive: --max-depth 1
        return
    fi

    local extra_flag
    extra_flag=$(_gdrive_path "$path")
    if [[ $? -eq 0 ]]; then
        /opt/homebrew/bin/rclone ls"gdrive:" $extra_flag
    else
        # Show dirs then files
        /opt/homebrew/bin/rclone lsd"gdrive:$path" 2>/dev/null
        /opt/homebrew/bin/rclone ls"gdrive:$path" 2>/dev/null
    fi
}

# ============================================================
# DROPBOX (mirrors the Google Drive commands)
# ============================================================

# Copy local folder/file TO Dropbox
# Usage: todbx ./folder "remote/path"
#        todbx ./folder "https://www.dropbox.com/home/chess"
todbx() {
    local source="$1"
    local dest="$2"

    if [[ -z "$source" || -z "$dest" ]]; then
        echo "Usage: todbx <local-source> <dropbox-path-or-url>"
        return 1
    fi

    local dropbox_path
    dropbox_path=$(_dropbox_path "$dest")

    echo "$(date): Copying $source -> dropbox:$dropbox_path"
    /opt/homebrew/bin/rclone copy"$source" "dropbox:$dropbox_path" --progress
    echo "$(date): Done"
}

# Download FROM Dropbox to local
# Usage: fromdbx "remote/path" ./local
#        fromdbx "remote/path" .
#        fromdbx "remote/path"              (defaults to current dir)
#        fromdbx "https://www.dropbox.com/home/chess" ./local
fromdbx() {
    local source="$1"
    local dest="${2:-.}"

    if [[ -z "$source" ]]; then
        echo "Usage: fromdbx <dropbox-path-or-url> [local-dest]"
        echo "  dest defaults to current directory (.)"
        return 1
    fi

    local dropbox_path
    dropbox_path=$(_dropbox_path "$source")

    echo "$(date): Downloading dropbox:$dropbox_path -> $dest"
    /opt/homebrew/bin/rclone copy"dropbox:$dropbox_path" "$dest" --progress
    echo "$(date): Done"
}

# Sync FROM Dropbox to local (mirror - deletes local files not on Dropbox)
# Usage: dbsyncdown "remote/path" ./local
#        dbsyncdown "remote/path"                 (defaults to current dir)
#        dbsyncdown "https://www.dropbox.com/home/chess" .
dbsyncdown() {
    local source="$1"
    local dest="${2:-.}"

    if [[ -z "$source" ]]; then
        echo "Usage: dbsyncdown <dropbox-path-or-url> [local-dest]"
        echo "  dest defaults to current directory (.)"
        echo "  WARNING: sync deletes local files not on Dropbox"
        return 1
    fi

    local dropbox_path
    dropbox_path=$(_dropbox_path "$source")

    echo "WARNING: This will delete local files in $dest not present on Dropbox"
    echo "$(date): Syncing dropbox:$dropbox_path -> $dest"
    /opt/homebrew/bin/rclone sync"dropbox:$dropbox_path" "$dest" --progress
    echo "$(date): Done"
}

# Sync local folder TO Dropbox (mirror - deletes files on Dropbox not in local)
# Usage: dbsync ./folder "remote/path"
#        dbsync ./folder "https://www.dropbox.com/home/chess"
dbsync() {
    local source="$1"
    local dest="$2"

    if [[ -z "$source" || -z "$dest" ]]; then
        echo "Usage: dbsync <local-source> <dropbox-path-or-url>"
        echo "  WARNING: sync deletes files on destination not in source"
        return 1
    fi

    local dropbox_path
    dropbox_path=$(_dropbox_path "$dest")

    echo "WARNING: This will delete files on Dropbox not present locally"
    echo "$(date): Syncing $source -> dropbox:$dropbox_path"
    /opt/homebrew/bin/rclone sync"$source" "dropbox:$dropbox_path" --progress
    echo "$(date): Done"
}

# List Dropbox folder contents
# Usage: dbls "remote/path"
#        dbls                        (lists root)
#        dbls "https://www.dropbox.com/home/chess"
dbls() {
    local path="${1:-}"

    if [[ -z "$path" ]]; then
        /opt/homebrew/bin/rclone lsddropbox: --max-depth 1
        return
    fi

    local dropbox_path
    dropbox_path=$(_dropbox_path "$path")

    /opt/homebrew/bin/rclone lsd"dropbox:$dropbox_path" 2>/dev/null
    /opt/homebrew/bin/rclone ls"dropbox:$dropbox_path" 2>/dev/null
}

# ============================================================
# TREE TO CLIPBOARD (for pasting into Claude chat, etc.)
# ============================================================

# Copy local folder tree to clipboard
# Usage: treetoclip ~/notes/basketball/_presorted
treetoclip() {
    ls -R "${1:-.}" | /usr/bin/pbcopy
    echo "Folder structure copied to clipboard"
}

# Copy Google Drive folder tree to clipboard
# Usage: gdtreetoclip "Documents/reading"
#        gdtreetoclip "https://drive.google.com/drive/folders/ABC123"
gdtreetoclip() {
    local path="${1:-}"
    local extra_flag
    extra_flag=$(_gdrive_path "$path")
    if [[ $? -eq 0 ]]; then
        /opt/homebrew/bin/rclone tree "gdrive:" $extra_flag | /usr/bin/pbcopy
    else
        /opt/homebrew/bin/rclone tree "gdrive:$path" | /usr/bin/pbcopy
    fi
    echo "Google Drive tree copied to clipboard"
}

# Copy Dropbox folder tree to clipboard
# Usage: dbtreetoclip "chess"
#        dbtreetoclip "https://www.dropbox.com/home/chess"
dbtreetoclip() {
    local path="${1:-}"
    local dropbox_path
    dropbox_path=$(_dropbox_path "$path")
    /opt/homebrew/bin/rclone tree "dropbox:$dropbox_path" | /usr/bin/pbcopy
    echo "Dropbox tree copied to clipboard"
}
