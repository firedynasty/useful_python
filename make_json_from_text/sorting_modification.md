# File Sorting Modification

## Problem
The original script sorted text files alphabetically, which caused page numbers to be ordered incorrectly:
- "pg1", "pg2", "pg3", ..., "pg10", "pg100", "pg101", ...

This alphabetical sorting placed "pg10" after "pg1" but before "pg2", and placed "pg100" before "pg11".

## Solution
Modified the code to implement natural sorting by:

1. Added a custom sorting function `extract_page_number` that:
   - Extracts numeric page numbers from filenames using regex
   - Converts the extracted numbers to integers for proper numeric comparison
   - Returns the original filename as fallback for non-matching files

2. Applied this sorting function to both text and CSV files via the `key` parameter of the `sorted()` function

## Code Changes

### Custom Sorting Function:
```python
def extract_page_number(filename):
    match = re.search(r'pg(\d+)', filename)
    if match:
        # Convert to integer for proper numeric sorting
        return int(match.group(1))
    return filename
```

### Modified Sorting Logic:
```python
# Before:
for file_name in sorted(txt_files):
    # Processing logic

# After:
for file_name in sorted(txt_files, key=extract_page_number):
    # Processing logic
```

## Result
Files are now sorted correctly by page number:
- "pg1", "pg2", ..., "pg9", "pg10", "pg11", ..., "pg99", "pg100", "pg101"

This ensures that the JSON output maintains the correct sequence of the source material.

## Usage
Run the script as before:
```
python process_texts.py -i extracted -o vocabulary_data.js
```

The output file will now have properly ordered entries.