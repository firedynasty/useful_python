-- VLC Play/Pause Toggle (F8)
tell application "VLC"
    if it is running then
        activate
    end if
end tell

tell application "System Events"
    tell process "VLC"
        keystroke space
    end tell
end tell
