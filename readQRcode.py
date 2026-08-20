#!/usr/bin/env python3
"""
Read a QR code from an image file and copy the result to clipboard.
If the QR code is a QR Bridge URL, decodes the base64 hash and copies the content.

Usage:
    python readQRcode.py <image_file>
    python readQRcode.py  # uses readQRcode.png in same directory
    python readQRcode.py --decode <url>  # decode a QR Bridge URL directly
"""

import sys
import subprocess
import base64
from pathlib import Path


def decode_qr_bridge_url(url: str) -> str | None:
    """If url is a QR Bridge URL with a base64 hash, return the decoded content."""
    if '#' not in url:
        return None
    fragment = url.split('#', 1)[1]
    if not fragment:
        return None
    try:
        # Add padding if needed
        padded = fragment + '=' * (-len(fragment) % 4)
        decoded = base64.b64decode(padded).decode('utf-8')
        return decoded
    except Exception:
        return None


def copy_to_clipboard(text: str) -> None:
    subprocess.run("pbcopy", input=text.encode(), check=True)


def decode_qr_pyzbar(image_path: str) -> list[str]:
    from pyzbar.pyzbar import decode
    from PIL import Image

    img = Image.open(image_path)
    results = decode(img)
    return [code.data.decode("utf-8") for code in results]


def decode_qr_opencv(image_path: str) -> list[str]:
    import cv2

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)
    return [data] if data else []


def main():
    # Direct URL decode mode: python readQRcode.py --decode <url>
    if len(sys.argv) > 1 and sys.argv[1] == '--decode':
        url = sys.argv[2] if len(sys.argv) > 2 else ''
        if not url:
            print("Usage: python readQRcode.py --decode <qr_bridge_url>")
            sys.exit(1)
        content = decode_qr_bridge_url(url)
        if content:
            copy_to_clipboard(content)
            print(content)
        else:
            copy_to_clipboard(url)
            print(url)
        return

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = Path(__file__).parent / "readQRcode.png"

    image_path = str(image_path)

    if not Path(image_path).exists():
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    results = []

    # Try pyzbar first, fall back to OpenCV
    try:
        results = decode_qr_pyzbar(image_path)
        method = "pyzbar"
    except ImportError:
        try:
            results = decode_qr_opencv(image_path)
            method = "opencv"
        except ImportError:
            print("No QR decoder found. Install one of:")
            print("  pip install pyzbar pillow  (also: brew install zbar)")
            print("  pip install opencv-python")
            sys.exit(1)

    if not results:
        print("No QR code found in image.")
        sys.exit(1)

    print(f"Decoded via {method}:")
    for raw in results:
        content = decode_qr_bridge_url(raw)
        if content:
            print(f"  {content}")
            copy_to_clipboard(content)
        else:
            print(f"  {raw}")
            copy_to_clipboard(raw)


if __name__ == "__main__":
    main()
