on run {input, parameters}
    if (count of input) is 0 then
        display dialog "No files were selected." buttons {"OK"} default button "OK"
        return
    end if

    set pyScript to "/Users/stanleytan/Documents/technical/python/extract_from_pdf/extract_pdf_to_one_txt_file.py"
    set shellScript to ""

    repeat with selectedFile in input
        set filePath to POSIX path of selectedFile
        set fileFolder to do shell script "dirname " & quoted form of filePath
        set shellScript to shellScript & "/Users/stanleytan/anaconda3/bin/python3 " & quoted form of pyScript & " -i " & quoted form of filePath & " -o " & quoted form of fileFolder & " ; "
    end repeat

    tell application "Terminal"
        activate
        do script shellScript in front window
    end tell
end run
