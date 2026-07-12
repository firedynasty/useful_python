#!/usr/bin/env python3
"""
Script to add a text caption to an image
"""

import os
from PIL import Image, ImageDraw, ImageFont
import argparse
import textwrap

def add_caption_to_image(image_path, caption, output_path=None, strip_height=None, font_size=48, max_width=None):
    """Add a text caption to an image in a strip underneath"""
    
    # Open the image
    img = Image.open(image_path)
    width, height = img.size
    
    # Resize the image if max_width is specified
    if max_width is not None and width > max_width:
        ratio = max_width / width
        new_width = max_width
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = img.size
    
    # Determine output path if not specified
    if output_path is None:
        directory, filename = os.path.split(image_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(directory, f"{name}_captioned{ext}")
    
    # Try to use a nice font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Wrap text based on image width and estimate height needed
    margin = 20
    max_caption_width = width - (2 * margin)
    wrapped_text = textwrap.fill(caption, width=max_caption_width // (font_size // 2))
    text_lines = wrapped_text.count('\n') + 1
    
    # Calculate strip height if not specified
    if strip_height is None:
        line_height = font_size + 4  # Add a bit of padding between lines
        strip_height = (text_lines * line_height) + (2 * margin)
        
    # Create new image with extra space
    new_img = Image.new('RGB', (width, height + strip_height), 'white')
    new_img.paste(img, (0, 0))
    
    # Draw the caption
    draw = ImageDraw.Draw(new_img)
    
    # Position text in the strip
    text_y = height + margin
    
    # Draw text line by line to center each line
    for line in wrapped_text.split('\n'):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        
        draw.text((text_x, text_y), line, fill='black', font=font)
        text_y += font_size + 4  # Move to next line
    
    # Save the image
    new_img.save(output_path)
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Add a caption to an image')
    parser.add_argument('image', help='Image file to caption')
    parser.add_argument('caption', help='Text to use as caption')
    parser.add_argument('--output', '-o', help='Output file path (default: adds _captioned to original filename)')
    parser.add_argument('--strip-height', '-sh', type=int, help='Height of caption strip in pixels (auto-calculated by default)')
    parser.add_argument('--font-size', '-s', type=int, default=48, help='Font size for caption (default: 48)')
    parser.add_argument('--max-width', '-w', type=int, help='Maximum width of the image in pixels (resizes if larger)')
    
    args = parser.parse_args()
    
    try:
        output_path = add_caption_to_image(
            args.image, 
            args.caption, 
            args.output, 
            args.strip_height, 
            args.font_size,
            args.max_width
        )
        print(f"✓ Created captioned image: {output_path}")
    except Exception as e:
        print(f"✗ Error processing {args.image}: {str(e)}")
    
if __name__ == "__main__":
    main()
