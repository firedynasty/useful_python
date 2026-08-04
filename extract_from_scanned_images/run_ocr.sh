#!/bin/zsh
source ~/.zshrc
/Users/stanleytan/anaconda3/bin/python /Users/stanleytan/Documents/technical/python/extract_from_scanned_images/screenshot_text_to_clipboard.py
osascript -e 'display notification "Text copied to clipboard" with title "Screenshot OCR"'
