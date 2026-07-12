#!/usr/bin/env python3
"""
Automated script to process all images with captions from captions.txt
"""

import os
import sys
import argparse
from script_to_add_caption import add_caption_to_image

def process_all_images(captions_file, images_dir=None, output_dir=None, font_size=36):
    # Check if captions file exists
    if not os.path.exists(captions_file):
        print(f"Error: {captions_file} not found")
        return
    
    # If images_dir is provided but output_dir is not, use images_dir as the output directory
    if images_dir and not output_dir:
        output_dir = images_dir
    # Default output directory if neither is provided
    elif not output_dir:
        output_dir = "captioned_images"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read captions file
    with open(captions_file, "r") as file:
        caption_lines = file.readlines()
    
    processed_count = 0
    errors_count = 0
    
    # Process each line
    for line in caption_lines:
        line = line.strip()
        if not line or ":" not in line:
            continue
        
        # Split the line to get image name and caption
        parts = line.split(":", 1)  # Split on first colon only
        if len(parts) != 2:
            continue
        
        image_name = parts[0].strip()
        caption = parts[1].strip()
        
        # Ensure image name has .png extension
        if not image_name.endswith(".png"):
            image_name += ".png"
        
        # Set the correct image path based on images_dir
        if images_dir:
            image_path = os.path.join(images_dir, image_name)
        else:
            image_path = image_name
        
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"Warning: Image {image_path} not found")
            errors_count += 1
            continue
        
        # Define output path - keep original filename but in output directory
        output_filename = f"{os.path.splitext(image_name)[0]}_captioned.png"
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            # Add caption to image
            add_caption_to_image(
                image_path=image_path,
                caption=caption,
                output_path=output_path,
                font_size=font_size
            )
            print(f"✓ Processed: {image_path} -> {output_path}")
            processed_count += 1
        except Exception as e:
            print(f"✗ Error processing {image_path}: {str(e)}")
            errors_count += 1
    
    print(f"\nSummary: Processed {processed_count} images with {errors_count} errors")

def main():
    parser = argparse.ArgumentParser(description='Process images with captions from a text file')
    parser.add_argument('captions_file', help='Path to the captions file')
    parser.add_argument('-f', '--folder', dest='images_dir', help='Directory containing the images')
    parser.add_argument('-o', '--output', dest='output_dir', 
                        help='Output directory for captioned images (default: same as images directory)')
    parser.add_argument('-s', '--font-size', dest='font_size', type=int, default=36,
                        help='Font size for captions (default: 36)')
    
    args = parser.parse_args()
    
    process_all_images(
        captions_file=args.captions_file,
        images_dir=args.images_dir,
        output_dir=args.output_dir,
        font_size=args.font_size
    )

if __name__ == "__main__":
    main()