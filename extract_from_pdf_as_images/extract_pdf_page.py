import argparse
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

def extract_pdf_page(pdf_path, page_number):
    """
    Extract text from a specific page of a PDF file using pdfminer.six.
    
    Args:
        pdf_path (str): Path to the PDF file
        page_number (int): Page number to extract (0-indexed)
        
    Returns:
        str: Extracted text from the specified page
    """
    try:
        # Extract pages using pdfminer
        pages = list(extract_pages(pdf_path))
        
        # Check if the page number is valid
        total_pages = len(pages)
        if page_number < 0 or page_number >= total_pages:
            return f"Error: Page number {page_number} is out of range. The PDF has {total_pages} pages (0-{total_pages-1})."
        
        # Get the specified page
        page_layout = pages[page_number]
        
        # Extract text from the page
        text = ""
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text += element.get_text()
        
        return text
    
    except FileNotFoundError:
        return f"Error: File '{pdf_path}' not found."
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Extract text from a specific page of a PDF file.')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('page_number', type=int, help='Page number to extract (0-indexed)')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Extract text from the specified page
    extracted_text = extract_pdf_page(args.pdf_path, args.page_number)
    
    # Output the extracted text
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            print(f"Text extracted and saved to {args.output}")
        except Exception as e:
            print(f"Error saving to file: {str(e)}")
            print(extracted_text)
    else:
        print(extracted_text)

if __name__ == "__main__":
    main()
