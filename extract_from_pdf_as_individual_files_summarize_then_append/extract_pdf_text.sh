#!/bin/bash

EXTRACT_PDF_PY="/Users/stanleytan/Documents/25-technical/46-python/extract_from_pdf_as_individual_files_summarize_then_append/extract_pdf_to_one_txt_file.py"

getpdftext() {
    if [[ -z "$1" ]]; then
        echo "Usage: getpdftext <file.pdf> [output_dir]"
        echo ""
        echo "Examples:"
        echo "  getpdftext document.pdf           # saves document.txt in current dir"
        echo "  getpdftext document.pdf ~/output   # saves to ~/output/document.txt"
        return 1
    fi

    local output_dir="${2:-.}"
    python "$EXTRACT_PDF_PY" -i "$1" -o "$output_dir"
}
