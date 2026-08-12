import os
import argparse

import fitz  # pymupdf


def render_pdf_to_images(input_path, output_folder, page_num=None, dpi=300):
    """
    Render PDF pages as image files for display.

    Args:
        input_path (str): Path to a PDF file or folder containing PDF files
        output_folder (str): Path to folder where image files will be saved
        page_num (int): 1-based page number to render; None renders all pages
        dpi (int): Resolution for rendering (default: 300)
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")

    if os.path.isfile(input_path):
        if input_path.lower().endswith('.pdf'):
            process_pdf_file(input_path, output_folder, page_num, dpi)
        else:
            print(f"Input file is not a PDF: {input_path}")
    else:
        pdf_files = [f for f in os.listdir(input_path) if f.lower().endswith('.pdf')]

        if not pdf_files:
            print(f"No PDF files found in {input_path}")
            return

        print(f"Found {len(pdf_files)} PDF files to process")

        for pdf_file in pdf_files:
            file_path = os.path.join(input_path, pdf_file)
            process_pdf_file(file_path, output_folder, page_num, dpi)


def process_pdf_file(pdf_path, output_folder, page_num=None, dpi=300):
    """
    Render pages from a single PDF and save each as a JPG image.

    Args:
        pdf_path (str): Path to the PDF file
        output_folder (str): Folder where rendered images will be saved
        page_num (int): 1-based page number to render; None renders all pages
        dpi (int): Resolution for rendering
    """
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]

    print(f"Processing: {filename}")

    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        if page_num is not None:
            if page_num < 1 or page_num > total_pages:
                print(f"  Error: page {page_num} out of range (PDF has {total_pages} pages)")
                doc.close()
                return
            pages_to_render = [(page_num - 1, doc[page_num - 1])]
            print(f"  Rendering page {page_num} of {total_pages} at {dpi} DPI")
        else:
            pages_to_render = list(enumerate(doc))
            print(f"  Rendering {total_pages} pages at {dpi} DPI")

        for pg_index, page in pages_to_render:
            pix = page.get_pixmap(dpi=dpi)
            image_filename = f"{filename_without_ext}_pg{pg_index+1:02d}.jpg"
            output_path = os.path.join(output_folder, image_filename)
            pix.save(output_path)
            print(f"  Saved: {image_filename}")

        doc.close()

    except Exception as e:
        print(f"  Error processing {filename}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Render PDF pages as JPG images for display')
    parser.add_argument('-i', '--input', default='.',
                        help='Input PDF file or folder containing PDF files (default: current directory)')
    parser.add_argument('-o', '--output', default='./extracted_images_from_pdf',
                        help='Output folder for image files (default: ./extracted_images_from_pdf)')
    parser.add_argument('-p', '--page', type=int, default=None,
                        help='Page number to render (1-based); omit to render all pages')
    parser.add_argument('-d', '--dpi', type=int, default=300,
                        help='Resolution for rendering (default: 300)')

    args = parser.parse_args()

    render_pdf_to_images(args.input, args.output, args.page, args.dpi)

    print("Processing complete.")


if __name__ == "__main__":
    main()
