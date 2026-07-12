# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a browser-based text-to-speech application that reads text with synchronized word-by-word highlighting. It's designed as a single HTML file with embedded CSS and JavaScript, making it easy to deploy and run anywhere with just a web browser.

## Architecture

The application is built as a **self-contained single-page application** with:

### Core Architecture Pattern
- **Single File Design**: Everything is contained in `index.html` - HTML structure, CSS styling, and JavaScript functionality
- **Class-based JavaScript**: Main functionality is encapsulated in the `ClipboardTextToSpeech` class
- **Browser API Integration**: Heavy use of Web Speech API (`speechSynthesis`) and Clipboard API

### Key Components

1. **Text Processing Pipeline**:
   - Automatic Kindle citation removal
   - Number prefix filtering (toggleable)
   - Text segmentation into paragraphs → sentences → words
   - HTML generation for word-by-word highlighting

2. **Speech Synthesis System**:
   - Sentence-by-sentence speech processing
   - Real-time timing analysis and adjustment
   - Voice selection optimization (Enhanced → Premium → Google → Default)
   - Adaptive word highlighting sync

3. **User Interface**:
   - Main reading area with clickable word navigation
   - Popup reading view for full-screen experience
   - Clipboard integration with automatic paste
   - Speed controls and playback buttons

## Key Technical Features

### Text-to-Speech Timing Synchronization
The application uses sophisticated timing analysis to sync word highlighting with actual speech:
- **Base Rate**: 176 WPM at 1x speed (calibrated from real testing)
- **Dynamic Adjustment**: Learns from actual speech timing and adjusts future highlighting
- **Timing Analysis**: Uses `performance.now()` to measure actual speech duration vs expected

### Content Processing
- **Smart Cleaning**: Removes Kindle citations using pattern matching
- **Selective Number Removal**: Toggle between keeping/skipping numbered content
- **Sentence Segmentation**: Splits text on sentence boundaries (`.!?`) for natural speech flow

### State Management
- Maintains reading position across pause/resume cycles
- Tracks current word, sentence, and progress through the text
- Synchronizes highlighting between main view and popup view

## Development Commands

This is a static HTML application with no build process or dependencies. To work with it:

### Running the Application
```bash
# Serve locally (optional - can also open directly in browser)
python -m http.server 8000
# Then open http://localhost:8000

# Or simply open index.html directly in any modern browser
open index.html
```

### Testing
No automated tests are present. Testing is done manually by:
1. Loading different text content types
2. Testing speech synthesis across different browsers
3. Verifying word highlighting synchronization
4. Testing clipboard integration

## Key Implementation Details

### Speech Synthesis Voice Selection Logic
The application prioritizes voices in this order:
1. Enhanced voices (macOS/iOS premium voices)
2. Premium voices (Google Cloud voices)
3. Google voices (free Google voices)
4. Any English voice
5. System default

### Timing Adjustment Algorithm
- Measures actual speech duration vs expected duration
- Calculates timing adjustment factor with dampening (30% of calculated difference)
- Clamps adjustment between 0.7x and 1.5x to prevent overcorrection
- Applies learned adjustment to future sentences

### Word Highlighting System
- Generates clickable word spans with data attributes
- Uses interval-based highlighting with calculated timing
- Accounts for TTS startup delay (150ms)
- Applies word processing adjustment (0.85x) to compensate for drift

## Browser Compatibility

Requires modern browsers with support for:
- Web Speech API (`speechSynthesis`)
- Clipboard API (`navigator.clipboard`)
- ES6 Classes and modern JavaScript features
- CSS Flexbox and modern styling

Works best on:
- Chrome/Chromium (best speech synthesis)
- Safari (excellent on macOS/iOS)
- Firefox (limited voice selection)