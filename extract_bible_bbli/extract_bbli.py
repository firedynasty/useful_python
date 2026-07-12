#!/usr/bin/env python3
"""
E-Sword .bbli Extractor - Extract Bible text to individual chapter files
Usage: python extract_bbli.py adb1905.bbli
"""

import sqlite3
import os
import sys
import re

def clean_text(text):
    """Remove HTML tags and clean up text"""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_bible(bbli_file, output_dir="ADB1905_chapters"):
    """Extract all chapters from .bbli file"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Connect to SQLite database
    print(f"📖 Opening {bbli_file}...")
    conn = sqlite3.connect(bbli_file)
    cursor = conn.cursor()
    
    # Show available tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📊 Found tables: {[t[0] for t in tables]}")
    
    # Try to find the verse table (common names: Bible, Verses, Scripture, etc.)
    verse_table = None
    for table_name in ['Bible', 'Verses', 'Scripture', 'bible', 'verses']:
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            verse_table = table_name
            print(f"✅ Using table: {verse_table}")
            break
        except:
            continue
    
    if not verse_table:
        print("❌ Could not find verse table. Showing all tables:")
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"\nTable: {table[0]}")
            print(f"Columns: {[col[1] for col in columns]}")
        conn.close()
        return
    
    # Show column structure
    cursor.execute(f"PRAGMA table_info({verse_table})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"📋 Columns: {column_names}")
    
    # Query all verses (adjust column names based on what we find)
    # Common patterns: Book, Chapter, Verse, Scripture/Text
    try:
        query = f"SELECT * FROM {verse_table} ORDER BY Book, Chapter, Verse"
        cursor.execute(query)
        
        current_book = None
        current_chapter = None
        chapter_verses = []
        
        books_processed = set()
        chapters_saved = 0
        
        print(f"\n📚 Extracting chapters...\n")
        
        for row in cursor.fetchall():
            # Adjust indices based on your column structure
            # Common structure: (Book, Chapter, Verse, Text)
            book_num = row[0]
            chapter_num = row[1]
            verse_num = row[2]
            verse_text = clean_text(row[3] if len(row) > 3 else row[-1])
            
            # When we move to a new chapter, save the previous one
            if book_num != current_book or chapter_num != current_chapter:
                if chapter_verses:
                    save_chapter(output_dir, current_book, current_chapter, chapter_verses)
                    chapters_saved += 1
                    if chapters_saved % 10 == 0:
                        print(f"   Saved {chapters_saved} chapters...")
                
                chapter_verses = []
                current_book = book_num
                current_chapter = chapter_num
                books_processed.add(book_num)
            
            # Add verse to current chapter
            chapter_verses.append(f"[{verse_num}] {verse_text}")
        
        # Save the last chapter
        if chapter_verses:
            save_chapter(output_dir, current_book, current_chapter, chapter_verses)
            chapters_saved += 1
        
        print(f"\n✅ Complete!")
        print(f"   Books processed: {len(books_processed)}")
        print(f"   Chapters saved: {chapters_saved}")
        print(f"   Output directory: {output_dir}/")
        
    except Exception as e:
        print(f"❌ Error extracting verses: {e}")
        print("\nTrying alternate column names...")
        
        # Show sample data to help debug
        cursor.execute(f"SELECT * FROM {verse_table} LIMIT 5")
        print("\nSample rows:")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"Row {i}: {row}")
    
    conn.close()

def save_chapter(output_dir, book_num, chapter_num, verses):
    """Save a chapter to a text file"""
    
    # Book names mapping
    book_names = {
        1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
        6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1Samuel", 10: "2Samuel",
        11: "1Kings", 12: "2Kings", 13: "1Chronicles", 14: "2Chronicles",
        15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms",
        20: "Proverbs", 21: "Ecclesiastes", 22: "SongOfSolomon", 23: "Isaiah",
        24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
        28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
        33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
        38: "Zechariah", 39: "Malachi",
        40: "Matthew", 41: "Mark", 42: "Luke", 43: "John", 44: "Acts",
        45: "Romans", 46: "1Corinthians", 47: "2Corinthians", 48: "Galatians",
        49: "Ephesians", 50: "Philippians", 51: "Colossians", 52: "1Thessalonians",
        53: "2Thessalonians", 54: "1Timothy", 55: "2Timothy", 56: "Titus",
        57: "Philemon", 58: "Hebrews", 59: "James", 60: "1Peter", 61: "2Peter",
        62: "1John", 63: "2John", 64: "3John", 65: "Jude", 66: "Revelation"
    }
    
    book_name = book_names.get(book_num, f"Book{book_num}")
    
    # Create filename
    filename = f"{book_name}_Chapter_{str(chapter_num).zfill(3)}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Write chapter to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Ang Dating Biblia (1905)\n")
        f.write(f"{book_name} - Kabanata {chapter_num}\n")
        f.write("=" * 60 + "\n\n")
        f.write("\n".join(verses))

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_bbli.py <path_to_bbli_file>")
        print("Example: python extract_bbli.py adb1905.bbli")
        sys.exit(1)
    
    bbli_file = sys.argv[1]
    
    if not os.path.exists(bbli_file):
        print(f"❌ Error: File '{bbli_file}' not found!")
        sys.exit(1)
    
    print("=" * 60)
    print("  📖 E-Sword .bbli Extractor")
    print("=" * 60)
    print()
    
    extract_bible(bbli_file)

if __name__ == "__main__":
    main()
