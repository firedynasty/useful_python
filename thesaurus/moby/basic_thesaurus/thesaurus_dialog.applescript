-- Thesaurus Dialog for Karabiner Integration
-- Shows a prompt, runs thesaurus lookup, displays scrollable list

-- Configuration
set pythonPath to "/usr/bin/python3"
set scriptPath to "/Users/stanleytan/Documents/25-technical/46-python/thesaurus/moby/basic_thesaurus/thesaurus_quick.py"

-- Show input dialog
try
    set dialogResult to display dialog "Enter a word:" default answer "" buttons {"Cancel", "Look Up"} default button "Look Up" with title "Thesaurus"
    set searchWord to text returned of dialogResult
on error
    return
end try

if searchWord is "" then
    return
end if

-- Run thesaurus lookup
try
    set thesaurusResult to do shell script pythonPath & " " & quoted form of scriptPath & " --list " & quoted form of searchWord

    -- Convert comma-separated result to list
    set AppleScript's text item delimiters to ", "
    set synonymList to text items of thesaurusResult
    set AppleScript's text item delimiters to ""

    if (count of synonymList) is 0 then
        display notification "No synonyms found" with title "Thesaurus"
        return
    end if

    -- Show scrollable list
    choose from list synonymList with title "Synonyms for '" & searchWord & "'" OK button name "Return" cancel button name "Cancel"

on error errMsg
    display notification errMsg with title "Thesaurus Error"
end try
