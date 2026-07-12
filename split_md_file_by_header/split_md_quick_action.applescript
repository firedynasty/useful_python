on run {input, parameters}
    if (count of input) > 0 then
        set shellScript to ""
        set pyScript to "/Users/stanleytan/Documents/technical/python/split_md_file_by_header/split_md.py"

        repeat with selectedFile in input
            set filePath to POSIX path of selectedFile

            -- Output directory = same folder as the input file, named after the file (without extension)
            set outputDir to do shell script "echo " & quoted form of filePath & " | sed 's/\\.[^.]*$//'"

            set shellScript to shellScript & "python3 " & quoted form of pyScript & " " & quoted form of filePath & " " & quoted form of outputDir & ";" & linefeed
        end repeat

        tell application "Terminal"
            activate
            do script shellScript in front window
        end tell
    else
        display dialog "No files were selected." buttons {"OK"} default button "OK"
    end if
end run
