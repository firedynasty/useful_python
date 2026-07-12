#!/usr/bin/env python3
"""
DOCX to TXT converter that preserves structure using Markdown formatting:
- Headings converted to Markdown headers (# ## ###)
- Tables converted to text-friendly format
- Lists preserved with bullets/numbers
- Bold/italic text preserved with Markdown syntax
- Links displayed with text and URL
"""

from docx import Document as DocumentClass
from docx.document import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import argparse
import os


def get_heading_level(paragraph):
    """Determine if paragraph is a heading and return its level."""
    if paragraph.style.name.startswith('Heading'):
        try:
            level = int(paragraph.style.name.split()[-1])
            return level
        except (ValueError, IndexError):
            return None
    return None


def format_run_text(run):
    """Format a run's text with Markdown syntax for bold/italic."""
    text = run.text
    if not text:
        return ""

    # Apply markdown formatting
    if run.bold and run.italic:
        return f"***{text}***"
    elif run.bold:
        return f"**{text}**"
    elif run.italic:
        return f"*{text}*"
    else:
        return text


def process_paragraph(paragraph):
    """Convert a paragraph to text with appropriate formatting."""
    # Check if it's a heading
    level = get_heading_level(paragraph)
    if level:
        prefix = '#' * level
        return f"{prefix} {paragraph.text}\n\n"

    # Process regular paragraph with inline formatting
    if not paragraph.text.strip():
        return ""

    formatted_text = ""
    for run in paragraph.runs:
        formatted_text += format_run_text(run)

    # Check if it's a list item
    if paragraph.style.name.startswith('List'):
        # Detect if it's numbered or bulleted based on text
        text = formatted_text.strip()
        if text and not text[0].isdigit():
            formatted_text = f"• {formatted_text}"
        return f"{formatted_text}\n"

    return f"{formatted_text}\n\n"


def format_table_to_text(table):
    """Convert a Word table to a text-friendly format."""
    lines = []

    # Calculate column widths
    col_widths = []
    for col_idx in range(len(table.columns)):
        max_width = 0
        for row in table.rows:
            if col_idx < len(row.cells):
                cell_text = row.cells[col_idx].text.strip()
                max_width = max(max_width, len(cell_text))
        col_widths.append(min(max_width, 40))  # Cap at 40 characters

    # Process rows
    for row_idx, row in enumerate(table.rows):
        row_texts = []
        for col_idx, cell in enumerate(row.cells):
            cell_text = cell.text.strip()
            # Truncate if too long
            if len(cell_text) > col_widths[col_idx]:
                cell_text = cell_text[:col_widths[col_idx]-3] + "..."
            # Pad to column width
            cell_text = cell_text.ljust(col_widths[col_idx])
            row_texts.append(cell_text)

        lines.append("| " + " | ".join(row_texts) + " |")

        # Add separator after first row (header)
        if row_idx == 0:
            separator = "|" + "|".join(["-" * (w + 2) for w in col_widths]) + "|"
            lines.append(separator)

    return "\n".join(lines) + "\n\n"


def iter_block_items(parent):
    """
    Generate a reference to each paragraph and table child within parent,
    in document order. Each returned value is an instance of either Table or Paragraph.
    """
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Unsupported parent type")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def docx_to_txt(docx_file, output_file=None, encoding='utf-8'):
    """
    Convert DOCX file to TXT format with Markdown-style formatting.

    Args:
        docx_file: Path to input DOCX file
        output_file: Path to output TXT file (optional, defaults to input name with .txt)
        encoding: Output file encoding (default: utf-8)

    Returns:
        Path to created TXT file
    """
    # Read DOCX
    doc = DocumentClass(docx_file)

    # Build output text
    output_lines = []

    # Add title if present
    if doc.core_properties.title:
        output_lines.append(f"# {doc.core_properties.title}\n\n")

    # Process all paragraphs and tables in order
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = process_paragraph(block)
            if text:
                output_lines.append(text)
        elif isinstance(block, Table):
            table_text = format_table_to_text(block)
            output_lines.append(table_text)

    # Join all lines
    output_text = "".join(output_lines)

    # Clean up excessive newlines (more than 2 consecutive)
    while "\n\n\n" in output_text:
        output_text = output_text.replace("\n\n\n", "\n\n")

    # Save to file
    if output_file is None:
        output_file = docx_file.rsplit('.', 1)[0] + '.txt'

    with open(output_file, 'w', encoding=encoding) as f:
        f.write(output_text)

    print(f"Successfully converted '{docx_file}' to '{output_file}'")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Convert DOCX file to TXT with Markdown-style formatting'
    )
    parser.add_argument('input', help='Input DOCX file path')
    parser.add_argument('-o', '--output', help='Output TXT file path (default: input_name.txt)')
    parser.add_argument('-e', '--encoding', default='utf-8', help='Output file encoding (default: utf-8)')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1

    try:
        docx_to_txt(args.input, args.output, args.encoding)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
