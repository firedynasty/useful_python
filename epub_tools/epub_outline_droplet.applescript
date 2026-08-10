on open droppedItems
    if (count of droppedItems) = 0 then return

    set epubPath to POSIX path of (item 1 of droppedItems)
    set scriptPath to "/Users/stanleytan/Documents/technical/python/ebooks/epub_to_outline.py"
    set python3Path to "/Users/stanleytan/anaconda3/bin/python3"
    set lastInputFile to "/Users/stanleytan/.epub_outline_last"

    -- Read last input if it exists
    set lastInput to "list"
    try
        set lastInput to do shell script "cat " & quoted form of lastInputFile
    end try

    set userInput to text returned of (display dialog "Chapter number to open, or 'list' to see all chapters:" ¬
        default answer lastInput ¬
        buttons {"Cancel", "Open"} ¬
        default button "Open" ¬
        with title "EPUB → Outline")

    -- Save for next time
    do shell script "echo " & quoted form of userInput & " > " & quoted form of lastInputFile

    if userInput is "list" then
        set shellCmd to python3Path & " " & quoted form of scriptPath & " " & quoted form of epubPath & " --list"
    else
        set shellCmd to python3Path & " " & quoted form of scriptPath & " " & quoted form of epubPath & " " & userInput
    end if

    tell application "Terminal"
        activate
        do script shellCmd in front window
    end tell
end open
