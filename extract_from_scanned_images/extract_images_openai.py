#!/usr/bin/env python3
"""
Extract text from images or PDFs using OpenAI GPT-4o-mini vision.

Usage:
    python extract_images_openai.py ./folder_of_images
    python extract_images_openai.py ./document.pdf
    python extract_images_openai.py ./photo.jpeg

Output saved to ~/downloads/extracted_YYYY-MM-DD_HHMMSS.txt

Requires:
    export OPENAI_API_KEY="sk-..."
    pip install openai Pillow pdf2image
    brew install poppler  (needed for PDF support)
"""

import argparse
import base64
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import openai
from PIL import Image


IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.webp')


def image_to_base64(image_path: str) -> tuple[str, str]:
    """Convert image to base64 string and return with media type."""
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif',
        '.webp': 'image/webp', '.bmp': 'image/png',
        '.tiff': 'image/png', '.tif': 'image/png',
    }

    # For formats not natively supported, convert to PNG
    if ext in ('.bmp', '.tiff', '.tif'):
        from io import BytesIO
        img = Image.open(image_path)
        buf = BytesIO()
        img.save(buf, format='PNG')
        return base64.standard_b64encode(buf.getvalue()).decode('utf-8'), 'image/png'

    media_type = media_types.get(ext, 'image/jpeg')
    with open(image_path, 'rb') as f:
        return base64.standard_b64encode(f.read()).decode('utf-8'), media_type


def extract_text_from_image(client, image_path: str) -> str:
    """Send image to GPT-4o-mini and extract text."""
    b64_data, media_type = image_to_base64(image_path)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{b64_data}"
                    }
                },
                {
                    "type": "text",
                    "text": "Extract all the text from this image exactly as written. Preserve paragraphs and formatting. Output only the extracted text, nothing else."
                }
            ]
        }]
    )

    return response.choices[0].message.content


def process_images(client, input_path: str, output_file: str):
    """Process a folder of images."""
    image_files = sorted([
        f for f in os.listdir(input_path)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    ])

    if not image_files:
        print(f"No image files found in {input_path}")
        sys.exit(1)

    print(f"Input:  {input_path}/ ({len(image_files)} images)")
    print(f"Output: {output_file}")
    print(f"Model:  gpt-4o-mini")
    print("-" * 50)

    start_time = time.time()

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, image_file in enumerate(image_files):
            image_path = os.path.join(input_path, image_file)
            page_start = time.time()

            try:
                text = extract_text_from_image(client, image_path)

                if i > 0:
                    f.write(f"\n{'='*50}\nPAGE {i+1} - {image_file}\n{'='*50}\n\n")
                else:
                    f.write(f"PAGE 1 - {image_file}\n{'='*50}\n\n")

                f.write(text)
                f.flush()

                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                remaining = avg * (len(image_files) - i - 1)
                page_time = time.time() - page_start

                print(f"[{i+1}/{len(image_files)}] {image_file} - {page_time:.1f}s "
                      f"(~{int(remaining//60)}m {int(remaining%60)}s remaining)")

            except Exception as e:
                print(f"[{i+1}/{len(image_files)}] ERROR {image_file}: {e}")

    total = time.time() - start_time
    print("-" * 50)
    print(f"Done! {len(image_files)} pages in {int(total//60)}m {int(total%60)}s")
    print(f"Saved: {output_file}")


def process_single_image(client, image_path: str, output_file: str):
    """Process a single image file."""
    image_name = os.path.basename(image_path)
    print(f"Input:  {image_path}")
    print(f"Output: {output_file}")
    print(f"Model:  gpt-4o-mini")
    print("-" * 50)

    start_time = time.time()

    try:
        text = extract_text_from_image(client, image_path)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{image_name}\n{'='*50}\n\n")
            f.write(text)

        page_time = time.time() - start_time
        print(f"Extracted text from {image_name} - {page_time:.1f}s")

    except Exception as e:
        print(f"ERROR processing {image_name}: {e}")

    total = time.time() - start_time
    print("-" * 50)
    print(f"Done in {int(total//60)}m {int(total%60)}s")
    print(f"Saved: {output_file}")


def process_pdf(client, pdf_path: str, output_file: str):
    """Process a PDF by converting pages to images and sending each to GPT-4o-mini."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("Error: pdf2image not installed")
        print("Run: pip install pdf2image")
        print("Also requires: brew install poppler")
        sys.exit(1)

    pdf_name = os.path.basename(pdf_path)
    print(f"Input:  {pdf_path}")
    print(f"Output: {output_file}")
    print(f"Model:  gpt-4o-mini")
    print("Converting PDF pages to images...")

    pages = convert_from_path(pdf_path)
    print(f"Found {len(pages)} pages")
    print("-" * 50)

    start_time = time.time()

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, page_img in enumerate(pages):
            page_start = time.time()

            try:
                # Convert PIL image to base64 PNG
                from io import BytesIO
                buf = BytesIO()
                page_img.save(buf, format='PNG')
                b64_data = base64.standard_b64encode(buf.getvalue()).decode('utf-8')

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "Extract all the text from this image exactly as written. Preserve paragraphs and formatting. Output only the extracted text, nothing else."
                            }
                        ]
                    }]
                )

                text = response.choices[0].message.content

                if i > 0:
                    f.write(f"\n{'='*50}\nPAGE {i+1}\n{'='*50}\n\n")
                else:
                    f.write(f"{pdf_name} - PAGE 1\n{'='*50}\n\n")

                f.write(text)
                f.flush()

                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                remaining = avg * (len(pages) - i - 1)
                page_time = time.time() - page_start

                print(f"[{i+1}/{len(pages)}] Page {i+1} - {page_time:.1f}s "
                      f"(~{int(remaining//60)}m {int(remaining%60)}s remaining)")

            except Exception as e:
                print(f"[{i+1}/{len(pages)}] ERROR Page {i+1}: {e}")

    total = time.time() - start_time
    print("-" * 50)
    print(f"Done! {len(pages)} pages in {int(total//60)}m {int(total%60)}s")
    print(f"Saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract text from images or PDFs using OpenAI GPT-4o-mini vision'
    )
    parser.add_argument('input', help='Input folder of images, a PDF file, or a single image file')

    args = parser.parse_args()
    input_path = args.input.rstrip('/')

    is_pdf = input_path.lower().endswith('.pdf') and os.path.isfile(input_path)
    is_image = input_path.lower().endswith(IMAGE_EXTENSIONS) and os.path.isfile(input_path)
    is_dir = os.path.isdir(input_path)

    if not is_pdf and not is_image and not is_dir:
        print(f"Error: {input_path} is not a directory, PDF, or image file")
        sys.exit(1)

    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not set")
        print("Run: export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    # Output file with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    output_file = os.path.expanduser(f"~/downloads/extracted_{timestamp}.txt")

    client = openai.OpenAI()

    if is_pdf:
        process_pdf(client, input_path, output_file)
    elif is_image:
        process_single_image(client, input_path, output_file)
    else:
        process_images(client, input_path, output_file)


if __name__ == "__main__":
    main()
