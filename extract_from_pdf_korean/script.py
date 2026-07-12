import os
import argparse
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextBoxHorizontal, LTTextLineHorizontal, LTChar
from pdfminer.layout import LTPage
import pandas as pd
import re

def extract_table_from_pdf(pdf_path, output_folder):
    """
    Extract tables from PDF file preserving cell-by-cell, row-by-row structure
    
    Args:
        pdf_path (str): Path to PDF file
        output_folder (str): Path to folder where extracted tables will be saved
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")
    
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    print(f"Processing: {filename}")
    
    try:
        # Extract pages
        pages = list(extract_pages(pdf_path))
        print(f"Found {len(pages)} pages")
        
        all_data = []
        
        # Process each page
        for page_num, page_layout in enumerate(pages, 1):
            print(f"Processing page {page_num}")
            
            # Collect text elements with their positions
            text_elements = []
            
            for element in page_layout:
                if isinstance(element, LTTextBoxHorizontal):
                    for text_line in element:
                        if isinstance(text_line, LTTextLineHorizontal):
                            text = text_line.get_text().strip()
                            if text:  # Skip empty lines
                                # Get position (x0, y0, x1, y1)
                                x0, y0, x1, y1 = text_line.bbox
                                # Store with normalized y-coordinate (PDF coordinates start from bottom)
                                text_elements.append((text, x0, -y0))  # Negate y for sorting
            
            # Sort by y position (rows) then x position (columns)
            # First sort by x (column order within each row)
            text_elements.sort(key=lambda x: x[1])
            # Then sort by y (row order from top to bottom)
            text_elements.sort(key=lambda x: x[2])
            
            # Group elements into rows based on similar y-coordinates
            rows = []
            current_row = []
            last_y = None
            
            y_threshold = 5  # Tolerance for considering text elements to be in the same row
            
            for text, x, y in text_elements:
                if last_y is None or abs(y - last_y) <= y_threshold:
                    current_row.append(text)
                else:
                    rows.append(current_row)
                    current_row = [text]
                last_y = y
            
            if current_row:
                rows.append(current_row)
            
            # Add rows to data
            for row in rows:
                all_data.append(row)
            
            # Create page CSV filename
            csv_filename = f"{filename_without_ext}_page{page_num}.csv"
            output_path = os.path.join(output_folder, csv_filename)
            
            # Convert to DataFrame and save to CSV
            try:
                df = pd.DataFrame(rows)
                df.to_csv(output_path, index=False, header=False, encoding='utf-8')
                print(f"Saved table from page {page_num} to: {csv_filename}")
            except Exception as e:
                print(f"Error saving CSV for page {page_num}: {str(e)}")
        
        # Save all pages combined
        combined_csv = os.path.join(output_folder, f"{filename_without_ext}_all_pages.csv")
        df_all = pd.DataFrame(all_data)
        df_all.to_csv(combined_csv, index=False, header=False, encoding='utf-8')
        print(f"Saved combined table to: {os.path.basename(combined_csv)}")
        
        # Also save as structured text
        txt_filename = f"{filename_without_ext}_structured.txt"
        output_txt_path = os.path.join(output_folder, txt_filename)
        
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            for row in all_data:
                f.write('\t'.join(row) + '\n')
        
        print(f"Saved structured text to: {txt_filename}")
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")


def extract_hangul_table(pdf_path, output_folder):
    """
    Specialized function to extract Hangul tables with better structure preservation
    
    Args:
        pdf_path (str): Path to PDF file
        output_folder (str): Path to folder where extracted tables will be saved
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")
    
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    print(f"Processing Hangul table: {filename}")
    
    # Dictionary to store tables by page
    page_tables = {}
    
    try:
        # Extract pages
        pages = list(extract_pages(pdf_path))
        
        # Process each page
        for page_num, page_layout in enumerate(pages, 1):
            # Get page size
            page_width = page_layout.width
            page_height = page_layout.height
            
            # Collect text elements with their positions
            text_elements = []
            
            for element in page_layout:
                if isinstance(element, LTTextBoxHorizontal):
                    for text_line in element:
                        if isinstance(text_line, LTTextLineHorizontal):
                            text = text_line.get_text().strip()
                            if text:  # Skip empty lines
                                # Get position (x0, y0, x1, y1)
                                x0, y0, x1, y1 = text_line.bbox
                                # Store position info
                                text_elements.append({
                                    'text': text,
                                    'x0': x0,
                                    'y0': page_height - y1,  # Convert to top-down coordinate system
                                    'x1': x1,
                                    'y1': page_height - y0   # Convert to top-down coordinate system
                                })
            
            # Sort text elements by y-position (top to bottom)
            text_elements.sort(key=lambda x: x['y0'])
            
            # Group elements by rows
            rows = []
            current_row = []
            current_y = None
            y_threshold = 12  # Adjust based on the table's row spacing
            
            for elem in text_elements:
                if current_y is None:
                    current_row.append(elem)
                    current_y = elem['y0']
                elif abs(elem['y0'] - current_y) <= y_threshold:
                    current_row.append(elem)
                else:
                    # Sort the current row by x position
                    current_row.sort(key=lambda x: x['x0'])
                    rows.append(current_row)
                    current_row = [elem]
                    current_y = elem['y0']
            
            if current_row:
                current_row.sort(key=lambda x: x['x0'])
                rows.append(current_row)
            
            # Structure the data as a 2D array
            structured_rows = []
            for row in rows:
                structured_row = [elem['text'] for elem in row]
                structured_rows.append(structured_row)
            
            # Store the structured data for this page
            page_tables[page_num] = structured_rows
            
            # Save individual page data
            csv_filename = f"{filename_without_ext}_hangul_page{page_num}.csv"
            output_path = os.path.join(output_folder, csv_filename)
            
            df = pd.DataFrame(structured_rows)
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"Saved Hangul table from page {page_num} to: {csv_filename}")
            
            # Save as structured text too
            txt_filename = f"{filename_without_ext}_hangul_page{page_num}.txt"
            txt_path = os.path.join(output_folder, txt_filename)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                for row in structured_rows:
                    f.write('\t'.join(row) + '\n')
        
        # Save combined data
        all_rows = []
        for page_num in sorted(page_tables.keys()):
            all_rows.extend(page_tables[page_num])
        
        combined_csv = os.path.join(output_folder, f"{filename_without_ext}_hangul_all.csv")
        df_all = pd.DataFrame(all_rows)
        df_all.to_csv(combined_csv, index=False, encoding='utf-8')
        print(f"Saved combined Hangul tables to: {os.path.basename(combined_csv)}")
        
    except Exception as e:
        print(f"Error processing Hangul table {filename}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Extract tables from PDF files preserving structure')
    parser.add_argument('-i', '--input', required=True, 
                      help='Input PDF file containing tables')
    parser.add_argument('-o', '--output', default='./extracted_tables', 
                      help='Output folder for extracted tables (default: ./extracted_tables)')
    parser.add_argument('--hangul', action='store_true',
                      help='Use specialized Hangul table extraction')
    
    args = parser.parse_args()
    
    if args.hangul:
        extract_hangul_table(args.input, args.output)
    else:
        extract_table_from_pdf(args.input, args.output)
    
    print("Processing complete.")

if __name__ == "__main__":
    main()
