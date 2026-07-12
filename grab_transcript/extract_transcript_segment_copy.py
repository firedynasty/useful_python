#!/usr/bin/env python3
"""
Extract transcript segments one minute before and after a specified time.
Usage: python extract_transcript_segment.py transcript.txt 1:23 [custom_question]
"""

import sys
import re
from typing import List, Tuple

def parse_time(time_str: str) -> int:
    """Convert time string to seconds. 
    Format: M:SS or MM:SS (minutes:seconds) or H:MM:SS or HH:MM:SS (hours:minutes:seconds)
    """
    parts = time_str.split(':')
    if len(parts) == 2:
        # One colon: minutes:seconds
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # Two colons: hours:minutes:seconds
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")

def seconds_to_time(seconds: int) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def extract_transcript_entries(filename: str) -> List[Tuple[int, str, str]]:
    """Parse transcript file and return list of (timestamp_seconds, text, original_format) tuples."""
    entries = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_time = None
    current_text = ""
    current_format = ""
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('##'):
            continue
            
        # Check if line is a timestamp
        time_match = re.match(r'^(\d+:\d+(?::\d+)?)\s*$', line)
        if time_match:
            # Save previous entry if exists
            if current_time is not None and current_text:
                entries.append((current_time, current_text.strip(), current_format))
            
            # Start new entry
            current_format = time_match.group(1)  # Now captures full timestamp
            current_time = parse_time(current_format)
            current_text = ""
        else:
            # This is content text
            if current_text:
                current_text += " "
            current_text += line
    
    # Add last entry
    if current_time is not None and current_text:
        entries.append((current_time, current_text.strip(), current_format))
    
    return entries

def find_segment(entries: List[Tuple[int, str, str]], target_time: int, target_format: str, window: int = 60) -> List[Tuple[int, str]]:
    """Find transcript entries within window seconds before target time, filtering by format."""
    start_time = max(0, target_time - window)
    end_time = target_time
    
    # Determine if target is in minutes:seconds (1 colon) or hours:minutes:seconds (2 colons)
    target_has_hours = target_format.count(':') == 2
    
    segment = []
    for timestamp, text, original_format in entries:
        # Only include entries that match the target format
        entry_has_hours = original_format.count(':') == 2
        if target_has_hours != entry_has_hours:
            continue
            
        if start_time <= timestamp <= end_time:
            segment.append((timestamp, text))
    
    return segment

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python extract_transcript_segment.py transcript.txt MM:SS [custom_question]")
        print("Example: python extract_transcript_segment.py transcript.txt 1:23")
        print('Example: python extract_transcript_segment.py transcript.txt 1:23 "What are the main themes?"')
        sys.exit(1)
    
    filename = sys.argv[1]
    target_time_str = sys.argv[2]
    custom_question = sys.argv[3] if len(sys.argv) == 4 else None
    
    try:
        target_time = parse_time(target_time_str)
        entries = extract_transcript_entries(filename)
        segment = find_segment(entries, target_time, target_time_str)
        
        if not segment:
            print(f"No transcript entries found around {target_time_str}")
            return
        
        print(f"Transcript segment 1 minute before {target_time_str}:")
        print("=" * 60)
        
        # Group entries by timestamp to show each timestamp separately
        current_timestamp = None
        for timestamp, text in segment:
            if timestamp != current_timestamp:
                if current_timestamp is not None:
                    print()  # Add blank line between timestamps
                print(f"{seconds_to_time(timestamp)}")
                current_timestamp = timestamp
            print(f"{text}")
        
        print("=" * 60)
        # Count unique timestamps
        unique_timestamps = len(set(timestamp for timestamp, _ in segment))
        print(f"Found {len(segment)} entries across {unique_timestamps} timestamps from {seconds_to_time(segment[0][0])} to {seconds_to_time(segment[-1][0])}")
        
        # Combine all text without timestamps and append the question (if provided)
        combined_text = " ".join(text for _, text in segment)
        if custom_question:
            combined_text_with_question = combined_text + "\n\n" + custom_question
        else:
            combined_text_with_question = combined_text + "\n\nBased on what I've shared so far, what key points should I be listening for in the rest of the video?"
        
        print(combined_text_with_question)
        
        # Copy to clipboard (with the question included)
        try:
            import pyperclip
            pyperclip.copy(combined_text_with_question)
            print("\n[Text with question copied to clipboard]")
        except ImportError:
            print("\n[pyperclip not available - install with: pip install pyperclip]")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)

if __name__ == "__main__":
    main()
