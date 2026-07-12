#!/usr/bin/env python3
"""
TXT to Markdown converter with smart formatting:
- Preserves paragraph structure
- Detects and converts common text patterns to Markdown
- Handles line-based headers (underlined with = or -)
- Preserves blank lines for readability
- Smart detection of lists and numbered items
"""

import argparse
import os
import re


def detect_underline_heading(current_line, next_line):
    """
    Detect if current line is a heading based on next line being underline.

    Returns:
        (is_heading, level) where level is 1 for === and 2 for ---
    """
    if not current_line or not next_line:
        return False, 0

    current = current_line.strip()
    next_stripped = next_line.strip()

    # Check for heading underlines
    if len(current) > 0 and len(next_stripped) > 0:
        # Level 1: ===
        if all(c == '=' for c in next_stripped) and len(next_stripped) >= 3:
            return True, 1
        # Level 2: ---
        if all(c == '-' for c in next_stripped) and len(next_stripped) >= 3:
            return True, 2

    return False, 0


def detect_list_item(line):
    """
    Detect if line is a list item.

    Returns:
        (is_list, formatted_line) - formatted_line has proper markdown bullet/number
    """
    stripped = line.strip()

    # Bulleted list patterns: -, *, •, ○, ▪, ▫
    bullet_pattern = r'^[\-\*\•\○\▪\▫]\s+(.+)$'
    match = re.match(bullet_pattern, stripped)
    if match:
        return True, f"- {match.group(1)}"

    # Numbered list pattern: 1. or 1)
    numbered_pattern = r'^(\d+)[\.\)]\s+(.+)$'
    match = re.match(numbered_pattern, stripped)
    if match:
        return True, f"{match.group(1)}. {match.group(2)}"

    return False, line


def detect_all_caps_heading(line):
    """
    Detect if line is all caps (potential heading).
    Only considers lines with 3+ words.

    Returns:
        (is_heading, level) - level is always 2 for all-caps
    """
    stripped = line.strip()

    # Must have letters
    if not any(c.isalpha() for c in stripped):
        return False, 0

    # Extract alphabetic characters and spaces
    alpha_text = ''.join(c for c in stripped if c.isalpha() or c.isspace())

    # Check if all alphabetic chars are uppercase
    if alpha_text and alpha_text.isupper() and len(alpha_text.split()) >= 3:
        return True, 2

    return False, 0


def txt_to_md(txt_file, output_file=None, encoding='utf-8', smart_format=True):
    """
    Convert TXT file to Markdown (.md) format.

    Args:
        txt_file: Path to input TXT file
        output_file: Path to output MD file (optional, defaults to input name with .md)
        encoding: File encoding (default: utf-8)
        smart_format: Enable smart formatting detection (default: True)

    Returns:
        Path to created MD file
    """
    # Read the text file
    with open(txt_file, 'r', encoding=encoding, errors='replace') as f:
        lines = f.readlines()

    output_lines = []
    i = 0

    while i < len(lines):
        current_line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else None

        # Skip empty lines but preserve them in output
        if not current_line.strip():
            output_lines.append('\n')
            i += 1
            continue

        processed = False

        if smart_format:
            # Check for underlined headings
            is_heading, level = detect_underline_heading(current_line, next_line)
            if is_heading:
                heading_text = current_line.strip()
                output_lines.append(f"{'#' * level} {heading_text}\n\n")
                i += 2  # Skip both the heading and underline
                processed = True

            # Check for all-caps headings
            if not processed:
                is_heading, level = detect_all_caps_heading(current_line)
                if is_heading:
                    heading_text = current_line.strip()
                    output_lines.append(f"{'#' * level} {heading_text}\n\n")
                    i += 1
                    processed = True

            # Check for list items
            if not processed:
                is_list, formatted = detect_list_item(current_line)
                if is_list:
                    output_lines.append(f"{formatted}\n")
                    i += 1
                    processed = True

        # Regular line processing
        if not processed:
            # Preserve the line as-is but ensure proper spacing
            stripped = current_line.strip()
            if stripped:
                output_lines.append(f"{stripped}\n\n")
            i += 1

    # Join all lines
    output_text = "".join(output_lines)

    # Clean up excessive newlines (more than 2 consecutive)
    while "\n\n\n" in output_text:
        output_text = output_text.replace("\n\n\n", "\n\n")

    # Ensure file ends with single newline
    output_text = output_text.rstrip() + '\n'

    # Save to file
    if output_file is None:
        # Replace .txt extension with .md, or add .md if no extension
        base_name = txt_file.rsplit('.', 1)[0] if '.' in txt_file else txt_file
        output_file = base_name + '.md'

    with open(output_file, 'w', encoding=encoding) as f:
        f.write(output_text)

    print(f"Successfully converted '{txt_file}' to '{output_file}'")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Convert TXT file to Markdown (.md) format'
    )
    parser.add_argument('input', help='Input TXT file path')
    parser.add_argument('-o', '--output', help='Output MD file path (default: input_name.md)')
    parser.add_argument('-e', '--encoding', default='utf-8', help='File encoding (default: utf-8)')
    parser.add_argument('--no-smart-format', action='store_true',
                       help='Disable smart formatting (preserve text as-is)')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1

    try:
        txt_to_md(
            args.input,
            args.output,
            args.encoding,
            smart_format=not args.no_smart_format
        )
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
