# Claude Guidelines for PDF Extraction Codebase

## Running Commands
- Run single script: `python extract_pdf_page.py <pdf_path> <page_number> [-o <output_file>]`
- Extract all pages: `python extract_all_pages_from_pdf.py [-i <input_path>] [-o <output_folder>]`
- Install dependencies: `pip install pdfminer.six`

## Code Style
- Imports: Standard library first, then third-party, separated by line
- Docstrings: Use Google-style docstrings with Args/Returns sections
- Error handling: Use try/except with specific exception types
- Naming: snake_case for functions/variables, descriptive names
- Types: Include type hints in docstrings
- Formatting: 4-space indentation, 88-char line length (matches Black)
- Functions: Single responsibility principle, clear input/output
- File operations: Use context managers (with statements)
- Command-line: Use argparse with descriptive help messages
- Comments: Use for explaining "why" not "what"