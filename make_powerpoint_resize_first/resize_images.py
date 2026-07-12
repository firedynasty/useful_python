#!/usr/bin/env python3
"""
Batch resize images from a folder to 1920x1080 and save to a new folder.
Crops out the top presentation bar, maintains aspect ratio, and centers on canvas.
"""
from PIL import Image
import os
import sys
import subprocess

def crop_top_bar(input_path, temp_path, crop_pixels=120):
    """
    Use PIL to crop the top bar from the image.
    Default crop is 30 pixels from top.
    """
    try:
        # Open the image
        img = Image.open(input_path)
        width, height = img.size

        # Crop from (left, top, right, bottom)
        # Remove crop_pixels from the top
        cropped = img.crop((0, crop_pixels, width, height))

        # Save the cropped image
        cropped.save(temp_path)
        return True
    except Exception as e:
        print(f"  Crop error: {e}")
        return False

def resize_image_to_1920x1080(input_path, output_path):
    """
    Resize an image to fit within 1920x1080, maintaining aspect ratio.
    Centers the image on a black 1920x1080 canvas.
    """
    # Target dimensions
    target_width = 1920
    target_height = 1080
    
    # Open the image
    img = Image.open(input_path)
    
    # Get original dimensions
    orig_width, orig_height = img.size
    
    # Calculate scaling to fit within 1920x1080 (maintains aspect ratio)
    width_scale = target_width / orig_width
    height_scale = target_height / orig_height
    scale = min(width_scale, height_scale)
    
    # Calculate new dimensions
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)
    
    # Resize the image
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create a new black canvas at 1920x1080
    canvas = Image.new('RGB', (target_width, target_height), (0, 0, 0))
    
    # Calculate position to center the resized image
    x = (target_width - new_width) // 2
    y = (target_height - new_height) // 2
    
    # Paste the resized image onto the canvas
    canvas.paste(img_resized, (x, y))
    
    # Save the result
    canvas.save(output_path, quality=95)

def get_image_files(folder_path):
    """Get all image files from the specified folder."""
    supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
    
    image_files = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(supported_formats):
            image_files.append(filename)
    
    return image_files

def batch_resize_images(input_folder, output_folder, crop_pixels=120):
    """Resize all images from input folder to 1920x1080 and save to output folder."""
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")
    
    # Create temp folder for cropped images
    temp_folder = os.path.join(output_folder, '.temp')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    # Get all image files
    image_files = get_image_files(input_folder)
    
    if not image_files:
        print(f"No image files found in {input_folder}")
        return False
    
    print(f"Found {len(image_files)} images to process")
    print(f"Cropping {crop_pixels}px from top, then resizing to 1920x1080")
    print()
    
    # Process each image
    success_count = 0
    for i, filename in enumerate(image_files, 1):
        input_path = os.path.join(input_folder, filename)
        temp_path = os.path.join(temp_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        # Convert to PNG for better quality
        if filename.lower().endswith(('.jpg', '.jpeg')):
            output_path = os.path.splitext(output_path)[0] + '.png'
            temp_path = os.path.splitext(temp_path)[0] + '.png'
        
        try:
            print(f"[{i}/{len(image_files)}] Processing: {filename}")
            
            # Step 1: Crop top bar with ImageMagick
            if not crop_top_bar(input_path, temp_path, crop_pixels):
                print(f"  ✗ Failed to crop")
                continue
            
            # Step 2: Resize to 1920x1080
            resize_image_to_1920x1080(temp_path, output_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            success_count += 1
            print(f"  ✓ Saved to {output_path}")
        except Exception as e:
            print(f"  ✗ Error processing {filename}: {e}")
            continue
    
    # Remove temp folder
    try:
        os.rmdir(temp_folder)
    except:
        pass
    
    print()
    print(f"Successfully processed {success_count}/{len(image_files)} images")
    print(f"Output saved to: {output_folder}")
    return True

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 3:
        print("Usage: python resize_images.py <input_folder> <output_folder> [crop_pixels]")
        print("\nArguments:")
        print("  input_folder   - Folder containing images to process")
        print("  output_folder  - Folder to save processed images")
        print("  crop_pixels    - Optional: Pixels to crop from top (default: 120)")
        print("\nExamples:")
        print("  python resize_images.py ./nov1 ./nov1_resized")
        print("  python resize_images.py ./nov1 ./nov1_resized 40")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    crop_pixels = int(sys.argv[3]) if len(sys.argv) >= 4 else 120
    
    if not os.path.isdir(input_folder):
        print(f"Error: {input_folder} is not a valid directory")
        sys.exit(1)
    
    if input_folder == output_folder:
        print("Error: Input and output folders must be different")
        sys.exit(1)
    
    # Batch resize images
    success = batch_resize_images(input_folder, output_folder, crop_pixels)
    
    if success:
        print("\nDone! ✓")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
