#!/usr/bin/env python3
"""
QR Code Generator Script
Creates QR codes from URLs or text provided as command line arguments.

Usage:
    python qr_generator.py "https://example.com"
    python qr_generator.py "https://example.com" --output myqr.png
    python qr_generator.py "Some text" --size 15 --border 2
"""

import argparse
import qrcode
import sys
import os
from urllib.parse import urlparse

def is_valid_url(url):
    """Check if the provided string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def add_protocol_if_missing(url):
    """Add https:// if no protocol is specified."""
    if not url.startswith(('http://', 'https://')):
        return f"https://{url}"
    return url

def generate_qr_code(data, output_file="qrcode.png", box_size=10, border=4):
    """Generate QR code and save to file."""
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Controls size (1 is smallest)
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        
        # Add data and generate
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save image
        img.save(output_file)
        
        return True, f"QR code saved as: {output_file}"
        
    except Exception as e:
        return False, f"Error generating QR code: {str(e)}"

def main():
    parser = argparse.ArgumentParser(
        description="Generate QR codes from URLs or text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python qr_generator.py "https://google.com"
  python qr_generator.py "google.com" -o google_qr.png
  python qr_generator.py "Hello World" --size 15 --border 2
        """
    )
    
    parser.add_argument(
        "data", 
        help="URL or text to encode in QR code"
    )
    
    parser.add_argument(
        "-o", "--output", 
        default="qrcode.png",
        help="Output filename (default: qrcode.png)"
    )
    
    parser.add_argument(
        "-s", "--size", 
        type=int, 
        default=10,
        help="Box size for QR code (default: 10)"
    )
    
    parser.add_argument(
        "-b", "--border", 
        type=int, 
        default=4,
        help="Border size (default: 4)"
    )
    
    parser.add_argument(
        "--auto-protocol", 
        action="store_true",
        help="Automatically add https:// to URLs without protocol"
    )
    
    args = parser.parse_args()
    
    # Process the input data
    data = args.data
    
    # If it looks like a URL without protocol, optionally add one
    if args.auto_protocol and not data.startswith(('http://', 'https://', 'ftp://')):
        if '.' in data and ' ' not in data:  # Simple heuristic for URLs
            data = add_protocol_if_missing(data)
            print(f"Added protocol: {data}")
    
    # Validate output directory exists
    output_dir = os.path.dirname(args.output) if os.path.dirname(args.output) else "."
    if not os.path.exists(output_dir):
        print(f"Error: Directory '{output_dir}' does not exist")
        sys.exit(1)
    
    # Generate QR code
    print(f"Generating QR code for: {data}")
    success, message = generate_qr_code(
        data, 
        args.output, 
        args.size, 
        args.border
    )
    
    if success:
        print(message)
        file_size = os.path.getsize(args.output)
        print(f"File size: {file_size} bytes")
    else:
        print(message)
        sys.exit(1)

if __name__ == "__main__":
    main()
