import os
import argparse
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

def extract_pdf_pages_individually(input_path, output_folder):
    """
    Extract text from a PDF file with each page saved as a separate text file.
    
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
            process_pdf_file_by_page(input_path, output_folder)
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
            process_pdf_file_by_page(file_path, output_folder)

def process_pdf_file_by_page(pdf_path, output_folder):
    """Process a single PDF file and save each page as a separate text file"""
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    print(f"Processing: {filename}")
    
    try:
        # Extract pages using pdfminer
        pages = list(extract_pages(pdf_path))
        print(f"  Found {len(pages)} pages")
        
        # Process each page
        for page_num, page_layout in enumerate(pages):
            # Create page text filename with padded number (e.g., file_pg01.txt)
            page_filename = f"{filename_without_ext}_pg{page_num+1:02d}.txt"
            output_path = os.path.join(output_folder, page_filename)
            
            # Extract text from the page
            text = ""
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text += element.get_text()
            
            # Save extracted text to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
                
            print(f"  Saved page {page_num+1} to: {page_filename}")
            
    except Exception as e:
        print(f"  Error processing {filename}: {str(e)}")

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Extract each page from PDF files as separate text files')
    parser.add_argument('-i', '--input', default='.', 
                      help='Input PDF file or folder containing PDF files (default: current directory)')
    parser.add_argument('-o', '--output', default='./extracted_txt_from_pdf', 
                      help='Output folder for text files (default: ./extracted_txt_from_pdf)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process PDF files
    extract_pdf_pages_individually(args.input, args.output)
    
    print("Processing complete.")

if __name__ == "__main__":
    main()
