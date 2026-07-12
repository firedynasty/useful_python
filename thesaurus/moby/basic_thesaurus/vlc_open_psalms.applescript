-- Open Psalms in VLC (F9)
set psalmFile to "/Users/stanleytan/Documents/25-technical/46-python/play_bible/psalms_complete.mp3"

tell application "VLC"
    activate
    open psalmFile
end tell
