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
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from pathlib import Path

def fix_xml_chars(text, verbose=False):
    """Fix common XML character issues"""
    if verbose:
        print("🔧 Fixing XML special characters...")
    
    original_text = text
    
    # Replace unescaped ampersands (but not already escaped ones)
    # This regex replaces & that are not followed by amp;, lt;, gt;, quot;, or apos;
    text = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', r'&amp;', text)
    
    # Count changes made
    ampersand_fixes = len(re.findall(r'&amp;', text)) - len(re.findall(r'&amp;', original_text))
    
    if verbose and ampersand_fixes > 0:
        print(f"   ✅ Fixed {ampersand_fixes} unescaped ampersand(s) (&)")
    elif verbose:
        print("   ✅ No XML character fixes needed")
    
    return text

def parse_and_debug_xml(xml_content):
    """Parse XML and debug the structure"""
    try:
        print("\n🔍 DEBUGGING XML STRUCTURE:")
        print("=" * 50)
        
        # Parse the XML
        root = ET.fromstring(xml_content)
        
        # Print namespace info
        print(f"Root element: {root.tag}")
        print(f"Root attributes: {root.attrib}")
        
        # Find all topics recursively
        def find_topics(element, level=0):
            indent = "  " * level
            
            # Check if this is a topic element
            if element.tag.endswith('topic'):
                topic_id = element.get('id', 'no-id')
                
                # Find title
                title_elem = element.find('.//{urn:xmind:xmap:xmlns:content:2.0}title')
                if title_elem is not None:
                    title = title_elem.text or 'No Title'
                else:
                    title = 'No Title Found'
                
                print(f"{indent}📋 TOPIC: '{title}' (ID: {topic_id})")
                
                # Count children topics
                children_topics = element.findall('.//{urn:xmind:xmap:xmlns:content:2.0}topic')
                direct_children = len([t for t in element.find('.//{urn:xmind:xmap:xmlns:content:2.0}topics') or [] if t.tag.endswith('topic')])
                
                print(f"{indent}   └─ Children topics found: {direct_children}")
            
            # Recursively check all children
            for child in element:
                find_topics(child, level + 1)
        
        find_topics(root)
        
        # Additional structure analysis
        print("\n📊 STRUCTURE SUMMARY:")
        print("-" * 30)
        
        # Find all sheets
        sheets = root.findall('.//{urn:xmind:xmap:xmlns:content:2.0}sheet')
        print(f"Total sheets found: {len(sheets)}")
        
        # Find all topics
        all_topics = root.findall('.//{urn:xmind:xmap:xmlns:content:2.0}topic')
        print(f"Total topics found: {len(all_topics)}")
        
        # Find all titles
        all_titles = root.findall('.//{urn:xmind:xmap:xmlns:content:2.0}title')
        print(f"Total titles found: {len(all_titles)}")
        
        print("\n📝 ALL TITLES FOUND:")
        for i, title in enumerate(all_titles, 1):
            print(f"  {i}. '{title.text or 'Empty Title'}'")
        
        print("=" * 50)
        return True
        
    except ET.ParseError as e:
        print(f"❌ XML Parse Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Debug Error: {e}")
        return False
def create_xmind_from_xml(xml_content, output_filename, debug=False):
    """Convert XML content to XMind file"""
    
    if debug:
        print("\n🔧 CREATING XMIND FILE:")
        print("-" * 30)
        parse_and_debug_xml(xml_content)
    
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
    
    if debug:
        print(f"\n📦 Creating ZIP file with {len(files)} files:")
        for filename in files.keys():
            print(f"  - {filename}")
    
    # Create ZIP file with .xmind extension
    try:
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, content in files.items():
                zf.writestr(file_path, content)
                if debug:
                    print(f"  ✅ Added {file_path} ({len(content)} bytes)")
        
        print(f"✅ Successfully created XMind file: {output_filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating XMind file: {e}")
        return False

def read_xml_file(input_filename, fix_chars=True, verbose=False):
    """Read XML content from input file and optionally fix XML characters"""
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Validate that it contains XML content
        if not content.startswith('<?xml'):
            print(f"⚠️  Warning: File doesn't appear to start with XML declaration")
        
        if 'xmap-content' not in content:
            print(f"⚠️  Warning: File doesn't appear to contain XMind XML content")
        
        print(f"📖 Successfully read {len(content)} characters from {input_filename}")
        
        # Fix XML characters if requested
        if fix_chars:
            original_length = len(content)
            content = fix_xml_chars(content, verbose)
            if len(content) != original_length and verbose:
                print(f"📝 Content length changed from {original_length} to {len(content)} characters after fixes")
        
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
        description='Convert XML content from a text file to XMind format (with automatic XML character fixing)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python generate_mind_map2.py career_planning.txt
  python generate_mind_map2.py my_mindmap.xml -v
  python generate_mind_map2.py "path/to/mindmap content.txt" --debug

Features:
  • Automatically fixes unescaped XML characters (& → &amp;)
  • Validates XML structure before processing
  • Debug mode shows detailed topic structure
  • Verbose output for troubleshooting
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
    
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable detailed debugging output (shows all topics found)'
    )
    
    parser.add_argument(
        '--no-fix-chars',
        action='store_true',
        help='Disable automatic XML character fixing (not recommended)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' does not exist")
        sys.exit(1)
    
    # Read XML content from input file
    fix_chars = not args.no_fix_chars
    xml_content = read_xml_file(args.input_file, fix_chars=fix_chars, verbose=args.verbose or args.debug)
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
    success = create_xmind_from_xml(xml_content, output_filename, debug=args.debug)
    
    if success:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"   Input:  {args.input_file}")
        print(f"   Output: {output_filename}")
        print(f"\nYou can now open '{output_filename}' in XMind software.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()