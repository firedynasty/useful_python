import os
import argparse
import glob
import subprocess
import tempfile
import shutil
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfMerger

def create_pdf_from_folder(folder_path, output_file, recursive=False, libreoffice_path=None):
    """Create a PDF from .txt, .png, and .docx files in a folder, sorted by name"""
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return

    # Find all .txt, .png, and .docx files
    files = []
    
    if recursive:
        # Walk through all subfolders
        for root, dirs, filenames in os.walk(folder_path):
            txt_files = glob.glob(os.path.join(root, "*.txt"))
            png_files = glob.glob(os.path.join(root, "*.png"))
            docx_files = glob.glob(os.path.join(root, "*.docx"))
            files.extend(txt_files)
            files.extend(png_files)
            files.extend(docx_files)
    else:
        # Just process the top-level folder
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        png_files = glob.glob(os.path.join(folder_path, "*.png"))
        docx_files = glob.glob(os.path.join(folder_path, "*.docx"))
        files.extend(txt_files)
        files.extend(png_files)
        files.extend(docx_files)
    
    # Sort files by name
    files.sort()
    
    if not files:
        print(f"No .txt, .png, or .docx files found in '{folder_path}'.")
        return
        
    print(f"Found {len(files)} file(s) to process.")
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    
    # List to hold temporary PDF files
    temp_pdfs = []
    
    # Count for naming temporary files
    file_count = 0
    
    # Process each file
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.docx':
            # Process docx file using LibreOffice
            try:
                # Check if LibreOffice path was provided
                if not libreoffice_path:
                    # Try to find LibreOffice executable based on OS
                    if os.name == 'nt':  # Windows
                        possible_paths = [
                            r'C:\Program Files\LibreOffice\program\soffice.exe',
                            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                libreoffice_path = path
                                break
                    else:  # Linux/Mac
                        for path in ['/usr/bin/libreoffice', '/usr/bin/soffice', 
                                    '/Applications/LibreOffice.app/Contents/MacOS/soffice']:
                            if os.path.exists(path):
                                libreoffice_path = path
                                break
                
                if not libreoffice_path:
                    print("LibreOffice not found. Please specify the path with --libreoffice-path")
                    # Fall back to processing as text
                    print(f"Falling back to text extraction for {filename}")
                    # Create a text content PDF
                    temp_pdf = os.path.join(temp_dir, f"{file_count:03d}_{filename}.pdf")
                    create_text_pdf(file_path, temp_pdf)
                    temp_pdfs.append(temp_pdf)
                else:
                    # Use LibreOffice to convert to PDF
                    temp_pdf = os.path.join(temp_dir, f"{file_count:03d}_{filename}.pdf")
                    cmd = [
                        libreoffice_path,
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', temp_dir,
                        file_path
                    ]
                    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Rename the file with our counter-based naming scheme
                    lo_output = os.path.join(temp_dir, os.path.splitext(filename)[0] + '.pdf')
                    if os.path.exists(lo_output):
                        os.rename(lo_output, temp_pdf)
                        temp_pdfs.append(temp_pdf)
                    else:
                        print(f"LibreOffice conversion failed for {filename}")
                        print(f"Error: {process.stderr.decode('utf-8', errors='replace')}")
                        # Fall back to text extraction
                        create_text_pdf(file_path, temp_pdf)
                        temp_pdfs.append(temp_pdf)
            
            except Exception as e:
                print(f"Error processing DOCX {filename}: {str(e)}")
                # Create error PDF
                temp_pdf = os.path.join(temp_dir, f"{file_count:03d}_{filename}_error.pdf")
                create_error_pdf(filename, str(e), temp_pdf)
                temp_pdfs.append(temp_pdf)
        
        elif file_ext == '.txt' or file_ext == '.png':
            # Process text and image files with ReportLab
            temp_pdf = os.path.join(temp_dir, f"{file_count:03d}_{filename}.pdf")
            
            if file_ext == '.txt':
                create_text_pdf(file_path, temp_pdf)
            else:  # .png
                create_image_pdf(file_path, temp_pdf)
                
            temp_pdfs.append(temp_pdf)
        
        file_count += 1
    
    # Merge all PDFs into a single output file
    if temp_pdfs:
        merger = PdfMerger()
        for pdf in temp_pdfs:
            try:
                merger.append(pdf)
            except Exception as e:
                print(f"Error merging {pdf}: {str(e)}")
        
        merger.write(output_file)
        merger.close()
        print(f"PDF created: {output_file}")
    else:
        print("No PDFs were created.")
    
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    
    return output_file


def create_text_pdf(text_file, output_pdf):
    """Create a PDF from a text file"""
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create a custom style for text file content - doubled font size
    text_style = ParagraphStyle(
        'TextFileStyle',
        parent=styles['Normal'],
        fontSize=20,  # Doubled from 10 to 20
        leading=24,   # Doubled from 12 to 24
        spaceAfter=24 # Doubled spacing after paragraphs as well
    )
    
    # Create a custom style for file headers - increased size
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=24,  # Increased from 14 to 24
        textColor=colors.blue,
        spaceAfter=12 # Doubled spacing
    )
    
    # List to hold PDF elements
    elements = []
    
    # Add file name as header
    filename = os.path.basename(text_file)
    elements.append(Paragraph(filename, header_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Process text file
    try:
        with open(text_file, 'r', encoding='utf-8', errors='replace') as f:
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
    
    # Build PDF
    doc.build(elements)


def create_image_pdf(image_file, output_pdf):
    """Create a PDF from an image file"""
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create a custom style for file headers - increased size
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=24,  # Increased from 14 to 24
        textColor=colors.blue,
        spaceAfter=12 # Doubled spacing
    )
    
    # List to hold PDF elements
    elements = []
    
    # Add file name as header
    filename = os.path.basename(image_file)
    elements.append(Paragraph(filename, header_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Process image file
    try:
        # Get image dimensions
        img = Image.open(image_file)
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
        img_obj = RLImage(image_file, width=img_width, height=img_height)
        elements.append(img_obj)
        
    except Exception as e:
        error_msg = f"Error processing image {filename}: {str(e)}"
        print(error_msg)
        elements.append(Paragraph(error_msg, styles['Normal']))
    
    # Build PDF
    doc.build(elements)


def create_error_pdf(filename, error_message, output_pdf):
    """Create a PDF with an error message"""
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create a custom style for error messages
    error_style = ParagraphStyle(
        'ErrorStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.red,
        spaceAfter=12
    )
    
    # List to hold PDF elements
    elements = []
    
    # Add file name as header
    elements.append(Paragraph(f"Error processing: {filename}", styles['Heading2']))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Add error message
    elements.append(Paragraph(f"Error: {error_message}", error_style))
    
    # Build PDF
    doc.build(elements)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create a PDF from .txt, .png, and .docx files in a folder')
    parser.add_argument('folder', help='Folder containing files to process')
    parser.add_argument('-o', '--output', default='output.pdf', 
                        help='Output PDF file (default: output.pdf)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process subfolders recursively')
    parser.add_argument('--libreoffice-path', 
                        help='Path to LibreOffice executable for converting DOCX files')
    
    args = parser.parse_args()
    
    # Create PDF
    create_pdf_from_folder(args.folder, args.output, args.recursive, args.libreoffice_path)
    
if __name__ == "__main__":
    main()
