import argparse
import sys
from pathlib import Path


def extract_page_as_image(pdf_path: str, page_number: int, output_path: str = None, dpi: int = 150) -> str:
    """
    Render a specific PDF page and save it as an image file.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): Page number to extract (0-indexed).
        output_path (str): Output image path. Defaults to <pdf_stem>_page<N>.png.
        dpi (int): Resolution in dots per inch (higher = sharper but larger file).

    Returns:
        str: Path to the saved image, or an error message.
    """
    try:
        import fitz  # pymupdf
    except ImportError:
        return "Error: pymupdf is not installed. Run: pip install pymupdf"

    try:
        doc = fitz.open(pdf_path)
    except FileNotFoundError:
        return f"Error: File '{pdf_path}' not found."
    except Exception as e:
        return f"Error opening PDF: {e}"

    total_pages = len(doc)
    if page_number < 0 or page_number >= total_pages:
        doc.close()
        return (
            f"Error: Page {page_number} is out of range. "
            f"PDF has {total_pages} page(s) (0–{total_pages - 1})."
        )

    page = doc[page_number]

    # Scale matrix: 72 dpi is the PDF default, so multiply by dpi/72
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    doc.close()

    if output_path is None:
        stem = Path(pdf_path).stem
        output_path = f"{stem}_page{page_number}.png"

    pix.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Render a PDF page and save it as an image (PNG by default)."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "page_number",
        type=int,
        help="Page number to extract (0-indexed, so page 1 = 0)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output image path (e.g. page1.png). Extension sets the format.",
        default=None,
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Resolution in DPI (default: 150). Use 300 for print-quality.",
    )

    args = parser.parse_args()
    result = extract_page_as_image(args.pdf_path, args.page_number, args.output, args.dpi)

    if result.startswith("Error"):
        print(result, file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Saved: {result}")


if __name__ == "__main__":
    main()
