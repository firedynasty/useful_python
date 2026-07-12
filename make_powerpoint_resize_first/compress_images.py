#!/usr/bin/env python3
"""
Compress images to reduce file size without changing dimensions.
Fast compression using JPEG quality setting.
"""
from PIL import Image
import os
import sys

def compress_image(input_path, output_path, quality=85):
    """Compress an image to JPEG with specified quality."""
    img = Image.open(input_path)

    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Save as JPEG with compression
    img.save(output_path, 'JPEG', quality=quality, optimize=True)

def get_image_files(folder_path):
    """Get all image files from the specified folder."""
    supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')

    image_files = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(supported_formats):
            image_files.append(filename)

    return image_files

def format_size(bytes_size):
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"

def batch_compress(input_folder, output_folder, quality=85):
    """Compress all images from input folder and save to output folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    image_files = get_image_files(input_folder)

    if not image_files:
        print(f"No image files found in {input_folder}")
        return False

    print(f"Found {len(image_files)} images to compress")
    print(f"Quality: {quality}%")
    print()

    total_original = 0
    total_compressed = 0
    success_count = 0

    for i, filename in enumerate(image_files, 1):
        input_path = os.path.join(input_folder, filename)

        # Output as .jpg
        output_filename = os.path.splitext(filename)[0] + '.jpg'
        output_path = os.path.join(output_folder, output_filename)

        try:
            original_size = os.path.getsize(input_path)
            total_original += original_size

            compress_image(input_path, output_path, quality)

            compressed_size = os.path.getsize(output_path)
            total_compressed += compressed_size

            reduction = (1 - compressed_size / original_size) * 100

            print(f"[{i}/{len(image_files)}] {filename}")
            print(f"    {format_size(original_size)} -> {format_size(compressed_size)} ({reduction:.0f}% smaller)")

            success_count += 1
        except Exception as e:
            print(f"[{i}/{len(image_files)}] {filename} - Error: {e}")

    print()
    print(f"Processed {success_count}/{len(image_files)} images")
    print(f"Total: {format_size(total_original)} -> {format_size(total_compressed)}")
    if total_original > 0:
        print(f"Overall reduction: {(1 - total_compressed / total_original) * 100:.0f}%")
    print(f"Output: {output_folder}")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python compress_images.py <input_folder> <output_folder> [quality]")
        print()
        print("Arguments:")
        print("  input_folder   - Folder containing images")
        print("  output_folder  - Folder to save compressed images")
        print("  quality        - JPEG quality 1-100 (default: 85)")
        print()
        print("Examples:")
        print("  python compress_images.py ./screenshots ./compressed")
        print("  python compress_images.py ./screenshots ./compressed 80")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    quality = int(sys.argv[3]) if len(sys.argv) >= 4 else 85

    if not os.path.isdir(input_folder):
        print(f"Error: {input_folder} is not a valid directory")
        sys.exit(1)

    if input_folder == output_folder:
        print("Error: Input and output folders must be different")
        sys.exit(1)

    batch_compress(input_folder, output_folder, quality)

if __name__ == "__main__":
    main()
