#!/usr/bin/env python3
"""
Simple script to add numbers to images for printing
"""

import os
from PIL import Image, ImageDraw, ImageFont
import glob
import argparse

def add_number_to_image(image_path, number, output_path, style='strip'):
    """Add a number to an image in different styles"""
    
    # Open the image
    img = Image.open(image_path)
    
    if style == 'strip':
        # Add a white strip at bottom with number
        width, height = img.size
        strip_height = 50
        
        # Create new image with extra space
        new_img = Image.new('RGB', (width, height + strip_height), 'white')
        new_img.paste(img, (0, 0))
        
        # Draw the number
        draw = ImageDraw.Draw(new_img)
        
        # Try to use a nice font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
        
        text = str(number)
        # Center the text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        text_y = height + 10
        
        draw.text((text_x, text_y), text, fill='black', font=font)
        new_img.save(output_path)
        
    elif style == 'corner':
        # Add number in bottom-right corner
        draw = ImageDraw.Draw(img)
        
        # Create semi-transparent background
        box_size = 50
        margin = 10
        x = img.width - box_size - margin
        y = img.height - box_size - margin
        
        # Draw white rectangle
        draw.rectangle([x, y, x + box_size, y + box_size], fill='white')
        
        # Draw number
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        except:
            font = ImageFont.load_default()
        
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x + (box_size - text_width) // 2
        text_y = y + (box_size - text_height) // 2
        
        draw.text((text_x, text_y), text, fill='black', font=font)
        img.save(output_path)
        
    elif style == 'overlay':
        # Add large semi-transparent number overlay
        draw = ImageDraw.Draw(img, 'RGBA')
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
        except:
            font = ImageFont.load_default()
        
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (img.width - text_width) // 2
        text_y = (img.height - text_height) // 2
        
        # Draw semi-transparent white background
        padding = 20
        draw.rectangle(
            [text_x - padding, text_y - padding, 
             text_x + text_width + padding, text_y + text_height + padding],
            fill=(255, 255, 255, 180)
        )
        
        # Draw the number
        draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)
        img.save(output_path)

def main():
    parser = argparse.ArgumentParser(description='Add numbers to images for printing')
    parser.add_argument('--directory', default='.', help='Directory containing images')
    parser.add_argument('--pattern', default='*.jpg', help='File pattern to match (e.g., *.jpg, *.png)')
    parser.add_argument('--style', choices=['strip', 'corner', 'overlay'], default='strip',
                        help='Numbering style: strip (bottom strip), corner (bottom-right), overlay (center)')
    parser.add_argument('--prefix', default='numbered_', help='Prefix for output files')
    parser.add_argument('--start', type=int, default=1, help='Starting number')
    
    args = parser.parse_args()
    
    # Get all matching files
    image_files = glob.glob(os.path.join(args.directory, args.pattern))
    image_files.sort()  # Sort for consistent ordering
    
    if not image_files:
        print(f"No files found matching pattern '{args.pattern}' in directory '{args.directory}'")
        return
    
    print(f"Found {len(image_files)} images to process...")
    
    # Process each image
    for i, image_path in enumerate(image_files, start=args.start):
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{args.prefix}{i:03d}_{name}{ext}"
        output_path = os.path.join(args.directory, output_filename)
        
        try:
            add_number_to_image(image_path, i, output_path, args.style)
            print(f"✓ Processed: {filename} -> {output_filename}")
        except Exception as e:
            print(f"✗ Error processing {filename}: {str(e)}")
    
    print(f"\nDone! Processed {len(image_files)} images.")

if __name__ == "__main__":
    main()
