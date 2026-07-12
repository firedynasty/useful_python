import os
import argparse

from PIL import Image
import pytesseract

def extract_images_to_single_file(input_path, output_file):
    """
    Extract text from images in a folder using OCR and save to a single text file.

    Args:
        input_path (str): Path to folder containing image files
        output_file (str): Path to output text file
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

    print(f"Found {len(image_files)} image files to process")

    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Process all images and accumulate text
    all_text = ""
    for i, image_file in enumerate(image_files):
        image_path = os.path.join(input_path, image_file)
        print(f"Processing ({i+1}/{len(image_files)}): {image_file}")

        try:
            # Open image and extract text using OCR
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)

            # Add page separator
            if i > 0:
                all_text += f"\n{'='*50}\nPAGE {i + 1} - {image_file}\n{'='*50}\n\n"
            else:
                all_text += f"PAGE 1 - {image_file}\n{'='*50}\n\n"

            all_text += text

        except Exception as e:
            print(f"  Error processing {image_file}: {str(e)}")

    # Save all extracted text to single file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(all_text)

    print(f"\nSaved extracted text to: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Extract text from images using OCR into a single text file'
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input folder containing image files')
    parser.add_argument('-o', '--output', default='./extracted_text.txt',
                        help='Output text file (default: ./extracted_text.txt)')

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: Input path is not a directory: {args.input}")
        return

    extract_images_to_single_file(args.input, args.output)
    print("Processing complete.")

if __name__ == "__main__":
    main()
