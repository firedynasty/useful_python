on run {input, parameters}
    set clipPath to (the clipboard as text)

    -- Trim whitespace
    set clipPath to do shell script "echo " & quoted form of clipPath & " | xargs"

    if clipPath is "" then
        display notification "Clipboard is empty" with title "Go To Path"
        return input
    end if

    -- Check if path exists
    set pathExists to do shell script "test -e " & quoted form of clipPath & " && echo 'yes' || echo 'no'"

    if pathExists is "no" then
        display notification clipPath with title "Path not found"
        return input
    end if

    -- If it's a file, open its parent folder and select it
    set isDir to do shell script "test -d " & quoted form of clipPath & " && echo 'yes' || echo 'no'"

    if isDir is "yes" then
        tell application "Finder"
            activate
            set target of front Finder window to (POSIX file clipPath as alias)
        end tell
    else
        tell application "Finder"
            activate
            reveal (POSIX file clipPath as alias)
        end tell
    end if

    display notification clipPath with title "Navigated to Path"
    return input
end run
