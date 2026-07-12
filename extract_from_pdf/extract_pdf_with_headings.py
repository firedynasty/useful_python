import os
import argparse
from collections import Counter

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno


def get_line_font_info(element):
    """
    Extract font size and boldness info from a text element.

    Args:
        element: A pdfminer LTTextContainer element

    Returns:
        tuple: (max_font_size, is_bold)
    """
    sizes = []
    is_bold = False

    for text_line in element:
        if hasattr(text_line, '__iter__'):
            for char in text_line:
                if isinstance(char, LTChar):
                    sizes.append(char.size)
                    fontname = char.fontname.lower()
                    if 'bold' in fontname or 'heavy' in fontname or 'black' in fontname:
                        is_bold = True

    max_size = max(sizes) if sizes else 12.0
    return max_size, is_bold


def is_heading(element, heading_threshold=14.0, body_font_size=12.0):
    """
    Determine if a text element is a heading based on font characteristics.

    Args:
        element: A pdfminer LTTextContainer element
        heading_threshold: Minimum font size to consider as heading
        body_font_size: Detected body font size for relative comparison

    Returns:
        bool: True if element appears to be a heading
    """
    text = element.get_text().strip()

    # Skip empty text
    if not text:
        return False

    # Skip very long text (likely not a heading)
    if len(text) > 100:
        return False

    # Skip bullet points and list items
    if text.startswith(('•', '●', '○', '■', '□', '-', '–', '—', '*')):
        return False

    # Skip lines that look like sentences (end with period and have many words)
    if text.endswith('.') and len(text.split()) > 10:
        return False

    # Skip if mostly numbers or special chars (page numbers, etc.)
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count < 3:
        return False

    # Skip "Example:" type labels
    if text.lower().startswith('example'):
        return False

    max_size, is_bold = get_line_font_info(element)

    # Must be significantly larger than body text (at least 2pt larger)
    size_ratio = max_size / body_font_size if body_font_size > 0 else 1.0

    # Heading if significantly larger than body text
    if max_size >= heading_threshold and size_ratio >= 1.15:
        return True

    # Bold text that's at least as big as body can be heading (for subheadings)
    if is_bold and max_size >= body_font_size and len(text) < 60:
        return True

    return False


def detect_body_font_size(pages):
    """
    Detect the most common font size (body text) in the document.

    Args:
        pages: List of pdfminer page layouts

    Returns:
        float: The most common font size
    """
    font_sizes = Counter()

    for page_layout in pages:
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if hasattr(text_line, '__iter__'):
                        for char in text_line:
                            if isinstance(char, LTChar):
                                # Round to 1 decimal place for grouping
                                size = round(char.size, 1)
                                font_sizes[size] += 1

    if font_sizes:
        # Return the most common font size
        most_common = font_sizes.most_common(1)[0][0]
        return most_common
    return 12.0


def extract_pdf_with_headings(input_path, output_path, heading_threshold=14.0):
    """
    Extract text from PDF with heading-based section markers.

    Args:
        input_path: Path to PDF file
        output_path: Path for output text file
        heading_threshold: Font size threshold for heading detection
    """
    print(f"Processing: {input_path}")

    sections = []
    current_section = {"title": None, "content": []}
    heading_count = 0

    try:
        pages = list(extract_pages(input_path))
        print(f"Found {len(pages)} pages")

        # Detect body font size first
        body_font_size = detect_body_font_size(pages)
        print(f"Detected body font size: {body_font_size}pt")
        print(f"Heading threshold: {heading_threshold}pt (must be >{body_font_size * 1.15:.1f}pt)")

        for page_num, page_layout in enumerate(pages):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if not text:
                        continue

                    if is_heading(element, heading_threshold, body_font_size):
                        # Save previous section if it has content
                        if current_section["title"] or current_section["content"]:
                            sections.append(current_section)

                        # Start new section
                        # Clean up heading text (remove newlines, extra spaces)
                        clean_title = ' '.join(text.split())
                        current_section = {"title": clean_title, "content": []}
                        heading_count += 1
                        print(f"  [Heading] {clean_title[:60]}...")
                    else:
                        current_section["content"].append(text)

            print(f"  Processed page {page_num + 1}")

        # Don't forget the last section
        if current_section["title"] or current_section["content"]:
            sections.append(current_section)

        print(f"\nDetected {heading_count} headings")

        # Format output with numbered sections for RAG compatibility
        output_lines = []
        section_num = 0
        for section in sections:
            if section["title"]:
                section_num += 1
                output_lines.append(f"\n{section_num}. {section['title']}\n")

            content = "\n".join(section["content"])
            output_lines.append(content)

        final_output = "\n".join(output_lines)

        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_output)

        print(f"Saved to: {output_path}")
        print(f"Total sections: {len(sections)}")

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Extract PDF with heading-based section markers for RAG'
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input PDF file')
    parser.add_argument('-o', '--output', default=None,
                        help='Output text file (default: same name as input with .txt)')
    parser.add_argument('-t', '--threshold', type=float, default=14.0,
                        help='Font size threshold for heading detection (default: 14.0)')

    args = parser.parse_args()

    # Default output path
    if args.output is None:
        basename = os.path.splitext(os.path.basename(args.input))[0]
        args.output = f"{basename}_headings.txt"

    extract_pdf_with_headings(args.input, args.output, args.threshold)
    print("\nProcessing complete.")


if __name__ == "__main__":
    main()
