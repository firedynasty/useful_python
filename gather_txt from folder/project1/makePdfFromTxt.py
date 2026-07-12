import os
import argparse
import glob
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_pdf_from_folder(folder_path, output_file, recursive=False):
    """Create a PDF from .txt and .png files in a folder, sorted by name"""
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return

    # Find all .txt and .png files
    files = []
    
    if recursive:
        # Walk through all subfolders
        for root, dirs, filenames in os.walk(folder_path):
            txt_files = glob.glob(os.path.join(root, "*.txt"))
            png_files = glob.glob(os.path.join(root, "*.png"))
            files.extend(txt_files)
            files.extend(png_files)
    else:
        # Just process the top-level folder
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        png_files = glob.glob(os.path.join(folder_path, "*.png"))
        files.extend(txt_files)
        files.extend(png_files)
    
    # Sort files by name
    files.sort()
    
    if not files:
        print(f"No .txt or .png files found in '{folder_path}'.")
        return
        
    print(f"Found {len(files)} file(s) to process.")
    
    # Create PDF
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create a custom style for text file content - doubled font size
    text_style = ParagraphStyle(
        'TextFileStyle',
        parent=styles['Normal'],
        fontSize=14,  # Doubled from 10 to 20
        leading=12,   # Doubled from 12 to 24
        spaceAfter=12 # Doubled spacing after paragraphs as well
    )
    
    # Create a custom style for file headers - increased size
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,  # Increased from 14 to 24
        textColor=colors.blue,
        spaceAfter=6 # Doubled spacing
    )
    
    # List to hold PDF elements
    elements = []
    
    # Process each file
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")
        
        # Add file name as header
        elements.append(Paragraph(filename, header_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.txt':
            # Process text file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    text = f.read()
                    
                # Break text into paragraphs and add to PDF
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    if para.strip():  # Skip empty paragraphs
                        elements.append(Paragraph(para.replace('\n', '<br/>'), text_style))
                        
            except Exception as e:
                error_msg = f"Error processing {filename}: {str(e)}"
                print(error_msg)
                elements.append(Paragraph(error_msg, styles['Normal']))
                
        elif file_ext == '.png':
            # Process image file
            try:
                # Get image dimensions
                img = Image.open(file_path)
                width, height = img.size
                
                # Scale image to fit page width while maintaining aspect ratio
                max_width = 6.5 * inch  # Letter page width minus margins
                if width > max_width:
                    scale_factor = max_width / width
                    img_width = max_width
                    img_height = height * scale_factor
                else:
                    img_width = width
                    img_height = height
                
                # Add image to PDF
                img_obj = RLImage(file_path, width=img_width, height=img_height)
                elements.append(img_obj)
                
            except Exception as e:
                error_msg = f"Error processing image {filename}: {str(e)}"
                print(error_msg)
                elements.append(Paragraph(error_msg, styles['Normal']))
        
        # Add space between files
        elements.append(Spacer(1, 0.5 * inch))
    
    # Build PDF
    doc.build(elements)
    print(f"PDF created: {output_file}")
    return output_file

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create a PDF from .txt and .png files in a folder')
    parser.add_argument('folder', help='Folder containing .txt and .png files')
    parser.add_argument('-o', '--output', default='output.pdf', 
                        help='Output PDF file (default: output.pdf)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process subfolders recursively')
    
    args = parser.parse_args()
    
    # Create PDF
    create_pdf_from_folder(args.folder, args.output, args.recursive)
    
if __name__ == "__main__":
    main()
