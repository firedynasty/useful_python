import os
import argparse
import time

from PIL import Image
import pytesseract

def extract_images_to_single_file(input_path, output_file, lang='eng', start_page=1):
    """
    Extract text from images in a folder using OCR and save to a single text file.
    Writes incrementally to preserve progress if interrupted.

    Args:
        input_path (str): Path to folder containing image files
        output_file (str): Path to output text file
        lang (str): Tesseract language code(s). Examples:
                    'eng' - English only
                    'chi_sim' - Simplified Chinese
                    'chi_tra' - Traditional Chinese
                    'chi_sim+eng' - Simplified Chinese and English
                    'chi_tra+eng' - Traditional Chinese and English
        start_page (int): Starting page number for labeling (default: 1)
    """
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.webp')

    # Get all image files and sort them naturally
    image_files = sorted([
        f for f in os.listdir(input_path)
        if f.lower().endswith(image_extensions)
    ])

    if not image_files:
        print(f"No image files found in {input_path}")
        return

    total_files = len(image_files)
    end_page = start_page + total_files - 1
    print(f"Found {total_files} image files to process")
    print(f"Page numbers: {start_page} to {end_page}")
    print(f"Using OCR language(s): {lang}")
    print(f"Output file: {output_file}")
    print("-" * 50)

    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Track timing for estimates
    start_time = time.time()
    processed_count = 0
    error_count = 0

    # Open file and write incrementally
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, image_file in enumerate(image_files):
            image_path = os.path.join(input_path, image_file)
            page_start = time.time()

            try:
                # Open image and extract text using OCR
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image, lang=lang)

                # Write page separator
                page_num = start_page + i
                if i > 0:
                    f.write(f"\n{'='*50}\nPAGE {page_num} - {image_file}\n{'='*50}\n\n")
                else:
                    f.write(f"PAGE {page_num} - {image_file}\n{'='*50}\n\n")

                # Write text immediately
                f.write(text)
                f.flush()  # Ensure written to disk

                processed_count += 1
                page_time = time.time() - page_start

                # Calculate progress and time estimate
                elapsed = time.time() - start_time
                avg_time = elapsed / (i + 1)
                remaining = avg_time * (total_files - i - 1)
                remaining_min = int(remaining // 60)
                remaining_sec = int(remaining % 60)

                print(f"[{i+1}/{total_files}] {image_file} - {page_time:.1f}s "
                      f"(~{remaining_min}m {remaining_sec}s remaining)")

            except Exception as e:
                error_count += 1
                print(f"[{i+1}/{total_files}] ERROR {image_file}: {str(e)}")

    # Summary
    total_time = time.time() - start_time
    total_min = int(total_time // 60)
    total_sec = int(total_time % 60)

    print("-" * 50)
    print(f"Complete! Processed {processed_count}/{total_files} pages in {total_min}m {total_sec}s")
    if error_count > 0:
        print(f"Errors: {error_count}")
    print(f"Saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Extract text from images using OCR into a single text file'
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input folder containing image files')
    parser.add_argument('-o', '--output', default='./extracted_text.txt',
                        help='Output text file (default: ./extracted_text.txt)')
    parser.add_argument('-l', '--lang', default='chi_sim+eng',
                        help='Tesseract language(s). Examples: eng, chi_sim, chi_tra, '
                             'chi_sim+eng, chi_tra+eng (default: chi_sim+eng)')
    parser.add_argument('-s', '--start', type=int, default=1,
                        help='Starting page number for labeling (default: 1)')

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: Input path is not a directory: {args.input}")
        return

    extract_images_to_single_file(args.input, args.output, args.lang, args.start)

if __name__ == "__main__":
    main()
