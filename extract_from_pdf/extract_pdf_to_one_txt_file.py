import os
import argparse
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

def extract_pdf_to_single_file(input_path, output_folder):
    """
    Extract text from a PDF file with all pages saved as a single text file.
    
    Args:
        input_path (str): Path to PDF file or folder containing PDF files
        output_folder (str): Path to folder where text files will be saved
    """
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")
    
    # Check if input path is a file or directory
    if os.path.isfile(input_path):
        # Process single file
        if input_path.lower().endswith('.pdf'):
            process_pdf_file_single(input_path, output_folder)
        else:
            print(f"Input file is not a PDF: {input_path}")
    else:
        # Process all PDFs in directory
        pdf_files = [f for f in os.listdir(input_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF files found in {input_path}")
            return
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF file
        for pdf_file in pdf_files:
            file_path = os.path.join(input_path, pdf_file)
            process_pdf_file_single(file_path, output_folder)

def process_pdf_file_single(pdf_path, output_folder):
    """Process a single PDF file and save all pages as one text file"""
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    print(f"Processing: {filename}")
    
    try:
        # Extract pages using pdfminer
        pages = list(extract_pages(pdf_path))
        print(f"  Found {len(pages)} pages")
        
        # Create single text filename
        text_filename = f"{filename_without_ext}.txt"
        output_path = os.path.join(output_folder, text_filename)
        
        # Extract text from all pages
        all_text = ""
        for page_num, page_layout in enumerate(pages):
            # Add page separator (optional - you can remove if not needed)
            if page_num > 0:
                all_text += f"\n{'='*50}\nPAGE {page_num + 1}\n{'='*50}\n\n"
            
            # Extract text from the page
            page_text = ""
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_text += element.get_text()
            
            all_text += page_text
            print(f"  Processed page {page_num+1}")
        
        # Save all extracted text to single file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(all_text)
            
        print(f"  Saved all {len(pages)} pages to: {text_filename}")
            
    except Exception as e:
        print(f"  Error processing {filename}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Extract all pages from PDF files into single text files')
    parser.add_argument('-i', '--input', default='.',
                      help='Input PDF file or folder containing PDF files (default: current directory)')
    parser.add_argument('-o', '--output', default='./extracted_txt_from_pdf',
                      help='Output folder for text files (default: ./extracted_txt_from_pdf)')
    parser.add_argument('-f', '--output-file',
                      help='Write all extracted text to this specific file path (overrides -o)')

    args = parser.parse_args()

    if args.output_file:
        output_path = os.path.expanduser(args.output_file)
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Collect all text then write to the single specified file
        all_text = []
        input_path = args.input
        if os.path.isfile(input_path):
            pdfs = [input_path] if input_path.lower().endswith('.pdf') else []
        else:
            pdfs = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.lower().endswith('.pdf')]

        for pdf_path in pdfs:
            print(f"Processing: {os.path.basename(pdf_path)}")
            try:
                pages = list(extract_pages(pdf_path))
                print(f"  Found {len(pages)} pages")
                for page_num, page_layout in enumerate(pages):
                    if all_text or page_num > 0:
                        all_text.append(f"\n{'='*50}\nPAGE {page_num + 1}\n{'='*50}\n")
                    page_text = ""
                    for element in page_layout:
                        if isinstance(element, LTTextContainer):
                            page_text += element.get_text()
                    all_text.append(page_text)
                    print(f"  Processed page {page_num+1}")
            except Exception as e:
                print(f"  Error processing {os.path.basename(pdf_path)}: {str(e)}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_text))
        print(f"Saved to: {output_path}")
    else:
        extract_pdf_to_single_file(args.input, args.output)

    print("Processing complete.")

if __name__ == "__main__":
    main()
