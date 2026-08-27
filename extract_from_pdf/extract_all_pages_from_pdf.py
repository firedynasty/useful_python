import os
import argparse
import subprocess
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

def extract_pdf_pages_individually(input_path, output_folder=None, clipboard=False):
    """
    Extract text from a PDF file with each page saved as a separate text file,
    or copied to the clipboard.

    Args:
        input_path (str): Path to PDF file or folder containing PDF files
        output_folder (str): Path to folder where text files will be saved
        clipboard (bool): If True, copy all extracted text to clipboard instead of saving files
    """
    all_text = []

    # Check if input path is a file or directory
    if not clipboard and output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")

    if os.path.isfile(input_path):
        if input_path.lower().endswith('.pdf'):
            all_text = process_pdf_file_by_page(input_path, output_folder, clipboard)
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
            all_text.extend(process_pdf_file_by_page(file_path, output_folder, clipboard))

    if clipboard:
        combined = "\n".join(all_text)
        subprocess.run(["pbcopy"], input=combined.encode(), check=True)
        print(f"Copied to clipboard ({len(combined)} chars)")

def process_pdf_file_by_page(pdf_path, output_folder=None, clipboard=False):
    """Process a single PDF file and save each page as a separate text file,
    or return page texts for clipboard mode.

    Returns:
        list[str]: Extracted page texts (only used in clipboard mode)
    """
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]
    page_texts = []

    print(f"Processing: {filename}")

    try:
        pages = list(extract_pages(pdf_path))
        print(f"  Found {len(pages)} pages")

        for page_num, page_layout in enumerate(pages):
            text = ""
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text += element.get_text()

            if clipboard:
                page_texts.append(text)
                print(f"  Extracted page {page_num+1}")
            else:
                page_filename = f"{filename_without_ext}_pg{page_num+1:02d}.txt"
                output_path = os.path.join(output_folder, page_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"  Saved page {page_num+1} to: {page_filename}")

    except Exception as e:
        print(f"  Error processing {filename}: {str(e)}")

    return page_texts

def main():
    parser = argparse.ArgumentParser(description='Extract each page from PDF files as separate text files')
    parser.add_argument('-i', '--input', default='.',
                      help='Input PDF file or folder containing PDF files (default: current directory)')
    parser.add_argument('-o', '--output', default='./extracted_txt_from_pdf',
                      help='Output folder for text files (default: ./extracted_txt_from_pdf)')
    parser.add_argument('--clipboard', action='store_true',
                      help='Copy all extracted text to clipboard instead of saving files')

    args = parser.parse_args()

    extract_pdf_pages_individually(args.input, None if args.clipboard else args.output, args.clipboard)

    print("Processing complete.")

if __name__ == "__main__":
    main()
