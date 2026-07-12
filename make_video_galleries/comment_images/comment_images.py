#!/usr/bin/env python3
"""
Add a comment overlay to an image with dark blue background and white text.
"""
from PIL import Image, ImageDraw, ImageFont
import sys
import os

def add_comment_overlay(input_path, output_path, comment_text,
                       position='bottom', height=250,
                       bg_color=(0, 51, 102), text_color=(255, 255, 255),
                       font_size=135):
    """
    Add a comment overlay to an image.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
        comment_text: Text to display in overlay
        position: 'top' or 'bottom' (default: 'bottom')
        height: Height of overlay bar in pixels (default: 250)
        bg_color: RGB tuple for background color (default: dark blue)
        text_color: RGB tuple for text color (default: white)
        font_size: Size of text (default: 135)
    """
    # Open the image and apply EXIF orientation
    img = Image.open(input_path)

    # Apply EXIF orientation if present
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass  # If no EXIF data or error, continue with original

    width, height_img = img.size
    
    # Create new image with extra space for overlay
    new_height = height_img + height
    new_img = Image.new('RGB', (width, new_height), bg_color)
    
    # Paste original image
    if position == 'bottom':
        new_img.paste(img, (0, 0))
        text_y_start = height_img
    else:  # top
        new_img.paste(img, (0, height))
        text_y_start = 0
    
    # Draw the overlay bar
    draw = ImageDraw.Draw(new_img)
    
    # Try to load a nice font, fall back to default if not available
    try:
        # Try common macOS fonts
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/Library/Fonts/Arial.ttf", font_size)
        except:
            # Fall back to default
            font = ImageFont.load_default()
    
    # Get text bounding box for centering
    # Support multi-line text by using the multiline text method
    spacing = 4  # Line spacing in pixels
    bbox = draw.multiline_textbbox((0, 0), comment_text, font=font, spacing=spacing)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position to center text
    text_x = (width - text_width) // 2
    text_y = text_y_start + (height - text_height) // 2

    # Draw the text (supports \n for line breaks)
    draw.multiline_text((text_x, text_y), comment_text, fill=text_color, font=font, align='center', spacing=spacing)
    
    # Save the result
    new_img.save(output_path, quality=95)

def main():
    if len(sys.argv) < 4:
        print("Usage: python add_comment.py <input_image> <output_image> <comment_text> [position] [height]")
        print("\nArguments:")
        print("  input_image   - Path to input image")
        print("  output_image  - Path to save output image")
        print("  comment_text  - Text to display in overlay (use quotes for multi-word)")
        print("  position      - Optional: 'top' or 'bottom' (default: bottom)")
        print("  height        - Optional: Height of overlay bar in pixels (default: 100)")
        print("\nExamples:")
        print('  python add_comment.py input.png output.png "This is a comment"')
        print('  python add_comment.py input.png output.png "Note from pastor" top 120')
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    comment_text = sys.argv[3]
    position = sys.argv[4] if len(sys.argv) >= 5 else 'bottom'
    overlay_height = int(sys.argv[5]) if len(sys.argv) >= 6 else 250
    
    if not os.path.isfile(input_path):
        print(f"Error: {input_path} not found")
        sys.exit(1)
    
    try:
        add_comment_overlay(input_path, output_path, comment_text, 
                          position=position, height=overlay_height)
        print(f"✓ Comment overlay added successfully!")
        print(f"  Saved to: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
