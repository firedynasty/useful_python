#!/usr/bin/env python3
"""
XML to XMind Converter

This script converts XML content from a text file to an XMind (.xmind) file.
The output file will have the same base name as the input file but with .xmind extension.

Usage:
    python xml_to_xmind.py input_file.txt
    python xml_to_xmind.py career_planning.txt
"""

import zipfile
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

def create_xmind_from_xml(xml_content, output_filename):
    """Convert XML content to XMind file"""
    
    # Required files for XMind format
    files = {
        'content.xml': xml_content.encode('utf-8'),
        'META-INF/manifest.xml': '''<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
    <file-entry full-path="content.xml" media-type="text/xml"/>
</manifest>'''.encode('utf-8'),
        'meta.xml': f'''<?xml version="1.0" encoding="UTF-8"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
    <Author>XML to XMind Converter</Author>
    <Create-Time>{datetime.now().isoformat()}</Create-Time>
</meta>'''.encode('utf-8')
    }
    
    # Create ZIP file with .xmind extension
    try:
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, content in files.items():
                zf.writestr(file_path, content)
        
        print(f"✅ Successfully created XMind file: {output_filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating XMind file: {e}")
        return False

def read_xml_file(input_filename):
    """Read XML content from input file"""
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Validate that it contains XML content
        if not content.startswith('<?xml'):
            print(f"⚠️  Warning: File doesn't appear to start with XML declaration")
        
        if 'xmap-content' not in content:
            print(f"⚠️  Warning: File doesn't appear to contain XMind XML content")
        
        print(f"📖 Successfully read {len(content)} characters from {input_filename}")
        return content
        
    except FileNotFoundError:
        print(f"❌ Error: File '{input_filename}' not found")
        return None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def get_output_filename(input_filename):
    """Generate output filename based on input filename"""
    # Use pathlib for cross-platform path handling
    input_path = Path(input_filename)
    
    # Get the stem (filename without extension) and add .xmind
    output_filename = input_path.stem + '.xmind'
    
    return output_filename

def main():
    """Main function to handle command line arguments and conversion"""
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Convert XML content from a text file to XMind format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python xml_to_xmind.py career_planning.txt
  python xml_to_xmind.py my_mindmap.xml
  python xml_to_xmind.py "path/to/mindmap content.txt"
        '''
    )
    
    parser.add_argument(
        'input_file',
        help='Input text file containing XML content'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output filename (optional, defaults to input filename with .xmind extension)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' does not exist")
        sys.exit(1)
    
    # Read XML content from input file
    xml_content = read_xml_file(args.input_file)
    if xml_content is None:
        sys.exit(1)
    
    # Determine output filename
    if args.output:
        output_filename = args.output
        # Ensure it has .xmind extension
        if not output_filename.lower().endswith('.xmind'):
            output_filename += '.xmind'
    else:
        output_filename = get_output_filename(args.input_file)
    
    if args.verbose:
        print(f"📝 Input file: {args.input_file}")
        print(f"📝 Output file: {output_filename}")
        print(f"📝 XML content preview: {xml_content[:200]}...")
    
    # Create XMind file
    success = create_xmind_from_xml(xml_content, output_filename)
    
    if success:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"   Input:  {args.input_file}")
        print(f"   Output: {output_filename}")
        print(f"\nYou can now open '{output_filename}' in XMind software.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()