# Text-to-Speech Feature Documentation

This document explains how the text-to-speech system works in `clipboardreader.html`, specifically when the speech toggle is ON (green slider) and how the Play/Pause button functions.

## Overview

The app has two modes controlled by a toggle:
- **Pacer Mode (Silent)**: Word-by-word highlighting without audio
- **Speech Mode**: Word-by-word highlighting WITH text-to-speech audio

When the toggle slider (`speechToggle`) is ON (checked), the system uses the browser's Web Speech API to read text aloud while synchronizing word highlighting.

---

## Key Components

### 1. Language Selection Radio Buttons (Optional Multi-Language Support)

```html
<!-- Language Selection (Example: Mandarin/Cantonese for Chinese apps) -->
<div class="radio-group">
    <label>Select Language:</label>
    <label class="radio-label">
        <input type="radio" name="language" value="zh-CN" id="mandarinRadio" checked>
        <span>🇨🇳 Mandarin</span>
    </label>
    <label class="radio-label">
        <input type="radio" name="language" value="zh-HK" id="cantoneseRadio">
        <span>🇭🇰 Cantonese</span>
    </label>
</div>
```

**CSS for Radio Button Styling:**

```css
.radio-group {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 1.5rem;
}

.radio-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
}

.radio-label input[type="radio"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
}
```

### 2. Toggle Slider HTML Structure

```html
<div class="toggle-container" style="background-color: #e6f3ff;">
    <span style="font-weight: bold; font-size: 12px;">📖 Pacer (Silent)</span>
    <label class="switch">
        <input type="checkbox" id="speechToggle">
        <span class="slider" style="background-color: #4CAF50;"></span>
    </label>
    <span style="font-weight: bold; font-size: 12px;">🔊 Speech</span>
</div>
```

### 3. Toggle Slider CSS

```css
/* Toggle slider styles */
.switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #4CAF50;
    transition: .4s;
    border-radius: 24px;
}

.slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

input:checked + .slider {
    background-color: #ff6b6b;
}

input:checked + .slider:before {
    transform: translateX(26px);
}
```

### 4. Play/Pause Button HTML

```html
<button class="success-button" id="playButton" style="margin-left: 0.5rem; min-width: 140px;">
    ▶️ Play (esc/ent)
</button>
```

When playing, it transforms to:

```html
<button class="secondary-button" id="playButton" style="margin-left: 0.5rem; min-width: 140px;">
    ⏸️ Pause (esc/ent)
</button>
```

### 5. Button CSS Styles

```css
.success-button {
    background-color: #10B981;
}

.success-button:hover {
    background-color: #059669;
}

.secondary-button {
    background-color: #6B7280;
}

.secondary-button:hover {
    background-color: #4B5563;
}
```

---

## JavaScript Implementation

### Class Properties

```javascript
class ClipboardTextToSpeech {
    constructor() {
        // Speech mode - starts in pacer mode (checkbox unchecked)
        this.speechMode = false;

        // Playback state
        this.isPlaying = false;
        this.isPaused = false;
        this.utterance = null;

        // Timing properties
        this.sentenceStartTime = null;
        this.actualTimingAdjustment = 1.0;
        this.wordHighlightTimer = null;
        this.pacerTimeout = null;

        // UI elements
        this.playButton = document.getElementById('playButton');
        this.speedSelect = document.getElementById('speedSelect');

        // Language selection (optional for multi-language support)
        this.languageRadio1 = document.getElementById('mandarinRadio');  // Or language1Radio
        this.languageRadio2 = document.getElementById('cantoneseRadio'); // Or language2Radio

        // Sentence tracking
        this.sentences = [];
        this.currentSentenceIndex = 0;
        this.currentWordIndex = 0;
        this.words = [];
    }
}
```

### Event Listeners Setup

```javascript
initializeEventListeners() {
    // Speech mode toggle
    document.getElementById('speechToggle').addEventListener('change', (e) => {
        this.speechMode = e.target.checked;
        console.log('Playback mode:', this.speechMode ? 'Speech Mode' : 'Pacer Mode (Silent)');
    });

    // Language selection event listeners (optional for multi-language support)
    this.languageRadio1.addEventListener('change', () => {
        if (this.languageRadio1.checked) {
            console.log('🔄 Switched to Language 1 (e.g., Mandarin zh-CN)');
            this.updateStatus('Switched to Language 1');

            // If currently playing, restart from current sentence with new voice
            if (this.isPlaying) {
                this.stop();
                setTimeout(() => {
                    this.play();
                }, 100);
            }
        }
    });

    this.languageRadio2.addEventListener('change', () => {
        if (this.languageRadio2.checked) {
            console.log('🔄 Switched to Language 2 (e.g., Cantonese zh-HK)');
            this.updateStatus('Switched to Language 2');

            // If currently playing, restart from current sentence with new voice
            if (this.isPlaying) {
                this.stop();
                setTimeout(() => {
                    this.play();
                }, 100);
            }
        }
    });

    // Playback controls
    this.playButton.addEventListener('click', () => this.togglePlayPause());
}
```

### Play/Pause Toggle Logic

```javascript
togglePlayPause() {
    if (this.isPlaying) {
        // Currently playing, so pause and stop
        this.pause();
        this.stop();
    } else {
        // Not playing, so start playing
        this.play();
    }
}

play() {
    if (!this.words.length) {
        this.updateStatus('Please enter some text first');
        return;
    }

    if (!this.sentences || this.sentences.length === 0) {
        this.updateStatus('No sentences found to read');
        return;
    }

    if (this.isPaused) {
        this.resumeReading();
    } else {
        this.startReading();
    }
}

startReading() {
    // Ensure any previous speech is completely stopped
    this.stop();

    // Small delay to ensure cleanup is complete
    setTimeout(() => {
        this.isPlaying = true;
        this.isPaused = false;
        this.updateButtonStates();
        this.speakCurrentWord(); // This calls speakCurrentSentence()
    }, 100);
}

pause() {
    if (this.isPlaying) {
        window.speechSynthesis.pause();
        this.isPaused = true;
        this.updateButtonStates();
        this.updateStatus('Paused');
    }
}

stop() {
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Clear all timers
    if (this.wordHighlightTimer) {
        clearInterval(this.wordHighlightTimer);
        this.wordHighlightTimer = null;
    }

    if (this.pacerTimeout) {
        clearTimeout(this.pacerTimeout);
        this.pacerTimeout = null;
    }

    // Clear any pending utterance
    if (this.utterance) {
        this.utterance.onend = null;
        this.utterance.onerror = null;
        this.utterance = null;
    }

    // Reset state
    this.isPlaying = false;
    this.isPaused = false;
    this.clearHighlights();
    this.updateButtonStates();
}

updateButtonStates() {
    if (this.isPlaying) {
        this.playButton.textContent = '⏸️ Pause (esc/ent)';
        this.playButton.classList.remove('success-button');
        this.playButton.classList.add('secondary-button');
    } else {
        this.playButton.textContent = '▶️ Play (esc/ent)';
        this.playButton.classList.remove('secondary-button');
        this.playButton.classList.add('success-button');
    }
    this.stopButton.disabled = !this.isPlaying;
}
```

---

## Core Text-to-Speech Logic (When Toggle is ON)

### Main Speaking Method

```javascript
speakCurrentSentence() {
    if (this.currentSentenceIndex >= this.sentences.length) {
        this.onReadingComplete();
        return;
    }

    const sentence = this.sentences[this.currentSentenceIndex];

    this.updateSentenceIndicator();
    this.updateProgress();
    this.updateStatus(`Reading sentence ${this.currentSentenceIndex + 1} of ${this.sentences.length}`);

    // Track sentence start time for timing analysis
    this.sentenceStartTime = performance.now();

    // Check if we're in pacer mode (silent) or speech mode
    if (!this.speechMode) {
        // Pacer mode - only highlighting, no speech
        this.pacerOnlySentence(sentence);
        return;
    }

    // SPEECH MODE - Start word highlighting and audio
    this.startWordHighlighting(sentence);

    // Clean text for speech synthesis
    const cleanedText = this.cleanTextForSpeech(sentence.text);

    // Add sentence number prefix
    const sentenceNumber = this.currentSentenceIndex + 1;
    const textToSpeak = `${sentenceNumber}. ${cleanedText}`;

    // Create speech utterance
    this.utterance = new SpeechSynthesisUtterance(textToSpeak);
    this.utterance.rate = parseFloat(this.speedSelect.value);
    this.utterance.pitch = 1;
    this.utterance.volume = 1;
    this.utterance.lang = 'en-US';

    // Language selection: Get selected language from radio buttons (if using multi-language)
    // For single language apps, just set this.utterance.lang = 'en-US' directly
    let selectedLang = 'en-US'; // Default

    // Example for multi-language support (Mandarin/Cantonese)
    if (this.languageRadio1 && this.languageRadio2) {
        selectedLang = this.languageRadio1.checked ? 'zh-CN' : 'zh-HK';
    }

    this.utterance.lang = selectedLang;

    // Voice selection with language filtering
    const voices = speechSynthesis.getVoices();
    console.log('🔊 Total voices available:', voices.length);

    if (voices.length > 0) {
        // Try to find Google voices first with EXACT language match
        let selectedVoice = voices.find(voice =>
            voice.lang === selectedLang && voice.name.includes('Google')
        );
        console.log('🔍 Google voice search for', selectedLang, ':', selectedVoice ? selectedVoice.name : 'NOT FOUND');

        // If no exact Google voice, try Enhanced/Premium voices with EXACT match
        if (!selectedVoice) {
            selectedVoice = voices.find(voice =>
                voice.lang === selectedLang &&
                (voice.name.includes('Enhanced') || voice.name.includes('Premium'))
            );
            console.log('🔍 Enhanced/Premium voice search:', selectedVoice ? selectedVoice.name : 'NOT FOUND');
        }

        // Fall back to any voice with EXACT language match
        if (!selectedVoice) {
            selectedVoice = voices.find(voice => voice.lang === selectedLang);
            console.log('🔍 Any exact match voice search:', selectedVoice ? selectedVoice.name : 'NOT FOUND');
        }

        // Last resort: startsWith match (for variations like zh-CN-Liaoning)
        if (!selectedVoice) {
            selectedVoice = voices.find(voice => voice.lang.startsWith(selectedLang));
            console.log('🔍 StartsWith match voice search:', selectedVoice ? selectedVoice.name : 'NOT FOUND');
        }

        if (selectedVoice) {
            this.utterance.voice = selectedVoice;
            console.log('✅ Using voice:', selectedVoice.name, selectedVoice.lang);
        } else {
            console.log('❌ No matching voice found, using default');
        }
    }

    // When sentence finishes
    this.utterance.onend = () => {
        // Analyze timing accuracy for future adjustments
        if (this.sentenceStartTime) {
            this.analyzeTimingAccuracy(sentence);
        }

        // Clear word highlighting timer
        if (this.wordHighlightTimer) {
            clearInterval(this.wordHighlightTimer);
            this.wordHighlightTimer = null;
        }

        if (this.isPlaying && !this.isPaused) {
            this.currentSentenceIndex++;

            // Small delay between sentences
            setTimeout(() => {
                if (this.isPlaying && !this.isPaused) {
                    this.speakCurrentSentence();
                }
            }, 300);
        }
    };

    this.utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);

        // Clear word highlighting timer on error
        if (this.wordHighlightTimer) {
            clearInterval(this.wordHighlightTimer);
            this.wordHighlightTimer = null;
        }

        this.updateStatus(`Speech error - trying to continue`);
        // Try to continue despite the error
        if (this.isPlaying && !this.isPaused) {
            this.currentSentenceIndex++;
            setTimeout(() => {
                if (this.isPlaying && !this.isPaused) {
                    this.speakCurrentSentence();
                }
            }, 500);
        }
    };

    // Cancel any existing speech before starting new one
    speechSynthesis.cancel();

    // Wait to ensure complete cleanup
    setTimeout(() => {
        if (this.isPlaying && !this.isPaused && this.utterance) {
            speechSynthesis.speak(this.utterance);
        }
    }, 150);
}
```

---

## Word Highlighting Synchronization

The system synchronizes word highlighting with speech using calculated timing:

```javascript
startWordHighlighting(sentence) {
    // Clear any existing highlighting timer
    if (this.wordHighlightTimer) {
        clearInterval(this.wordHighlightTimer);
        this.wordHighlightTimer = null;
    }

    // Timing calculation based on actual speech performance
    const baseWordsPerMinute = 176; // Calibrated from real testing at 1x speed
    const currentRate = parseFloat(this.speedSelect.value);
    const actualWordsPerMinute = baseWordsPerMinute * currentRate;
    let millisecondsPerWord = (60 * 1000) / actualWordsPerMinute;

    // Apply learned timing adjustment from previous sentences
    millisecondsPerWord *= this.actualTimingAdjustment;

    // Account for processing delays
    const sentenceStartupDelay = 150; // Time for TTS to begin speaking
    const wordProcessingAdjustment = 0.85; // Compensate for cumulative drift
    const adjustedMillisecondsPerWord = millisecondsPerWord * wordProcessingAdjustment;

    const wordsInSentence = sentence.endWordIndex - sentence.startWordIndex + 1;
    let currentWordInSentence = 0;

    // Start highlighting with initial delay to sync with speech start
    setTimeout(() => {
        if (!this.isPlaying || this.isPaused) return;

        // Highlight first word immediately when speech starts
        const globalWordIndex = sentence.startWordIndex + currentWordInSentence;
        this.highlightWord(globalWordIndex);
        currentWordInSentence++;

        // Continue with remaining words
        this.wordHighlightTimer = setInterval(() => {
            if (!this.isPlaying || this.isPaused || currentWordInSentence >= wordsInSentence) {
                if (this.wordHighlightTimer) {
                    clearInterval(this.wordHighlightTimer);
                    this.wordHighlightTimer = null;
                }
                return;
            }

            const globalWordIndex = sentence.startWordIndex + currentWordInSentence;
            this.highlightWord(globalWordIndex);
            currentWordInSentence++;
        }, adjustedMillisecondsPerWord);

    }, sentenceStartupDelay);
}

highlightWord(wordIndex) {
    this.clearHighlights();

    // Highlight in main reading area
    const wordElements = this.readingArea.querySelectorAll('.word');
    if (wordElements[wordIndex]) {
        wordElements[wordIndex].classList.add('current');
        this.currentWordIndex = wordIndex;

        // Auto-scroll if not visible
        const rect = wordElements[wordIndex].getBoundingClientRect();
        const isVisible = (
            rect.top >= 0 &&
            rect.bottom <= window.innerHeight
        );

        if (!isVisible) {
            wordElements[wordIndex].scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'nearest'
            });
        }
    }
}

clearHighlights() {
    const wordElements = this.readingArea.querySelectorAll('.word');
    wordElements.forEach(el => {
        el.classList.remove('current', 'highlight');
    });
}
```

---

## Pacer Mode (Silent Mode - Toggle OFF)

When the toggle is OFF, the system only highlights words without speaking:

```javascript
pacerOnlySentence(sentence) {
    // Clear any existing pacer timeout first
    if (this.pacerTimeout) {
        clearTimeout(this.pacerTimeout);
        this.pacerTimeout = null;
    }

    // Start word highlighting for pacer mode (uses same highlighting logic)
    this.startWordHighlighting(sentence);

    // Calculate sentence duration using SAME timing logic as speech mode
    const baseWordsPerMinute = 176;
    const currentRate = parseFloat(this.speedSelect.value);
    const actualWordsPerMinute = baseWordsPerMinute * currentRate;
    let millisecondsPerWord = (60 * 1000) / actualWordsPerMinute;

    millisecondsPerWord *= this.actualTimingAdjustment;
    const wordProcessingAdjustment = 0.85;
    const adjustedMillisecondsPerWord = millisecondsPerWord * wordProcessingAdjustment;

    const wordsInSentence = sentence.endWordIndex - sentence.startWordIndex + 1;
    const sentenceStartupDelay = 150;

    // Calculate total highlighting time
    const highlightingDuration = sentenceStartupDelay + (wordsInSentence * adjustedMillisecondsPerWord);
    const totalDuration = highlightingDuration + 300; // Add delay between sentences

    // Set timeout to move to next sentence after highlighting completes
    this.pacerTimeout = setTimeout(() => {
        this.pacerTimeout = null;

        // Clear word highlighting timer
        if (this.wordHighlightTimer) {
            clearInterval(this.wordHighlightTimer);
            this.wordHighlightTimer = null;
        }

        if (this.isPlaying && !this.isPaused) {
            this.currentSentenceIndex++;

            if (this.isPlaying && !this.isPaused) {
                this.speakCurrentSentence(); // Continues to next sentence
            }
        }
    }, totalDuration);
}
```

---

## Key Features Summary

### 1. **Two-Mode System**
- **Pacer Mode**: Visual highlighting only (silent reading practice)
- **Speech Mode**: Visual highlighting + Audio text-to-speech

### 2. **Smart Timing Synchronization**
- Base rate: 176 words per minute at 1x speed
- Adjustable playback speed via dropdown
- Adaptive timing adjustment based on actual speech performance
- Accounts for TTS startup delay (150ms) and processing drift (0.85x adjustment)

### 3. **Professional Voice Selection**
- Prioritizes high-quality voices: Enhanced → Premium → Google → Default
- Automatically selects best available English voice
- Configurable rate, pitch, and volume

### 4. **Sentence-by-Sentence Processing**
- Splits text into sentences for natural speech flow
- Adds sentence number prefix for context
- Small delay between sentences (300ms)
- Automatic progression through all sentences

### 5. **Interactive UI**
- Play/Pause button with visual state changes (green ▶️ / gray ⏸️)
- Toggle slider for switching between modes
- Real-time progress tracking
- Keyboard shortcuts support

### 6. **Error Handling**
- Graceful recovery from speech synthesis errors
- Automatic cleanup of timers and resources
- Prevents memory leaks with proper state management

---

## Browser API Used

### Web Speech API
- `window.speechSynthesis` - Main speech synthesis interface
- `speechSynthesis.getVoices()` - Get available voices
- `speechSynthesis.speak()` - Speak text
- `speechSynthesis.cancel()` - Stop speech
- `speechSynthesis.pause()` - Pause speech
- `speechSynthesis.resume()` - Resume paused speech
- `SpeechSynthesisUtterance` - Individual speech request object

### Performance API
- `performance.now()` - High-resolution timing for synchronization

---

## Multi-Language Support Implementation

### Overview

The language selection feature allows users to switch between different language voices (e.g., Mandarin Chinese vs. Cantonese Chinese, or English US vs. English UK). This is particularly useful for:

- **Language learning apps** - Switch between different language variants
- **Multi-dialect support** - Same written language, different pronunciation (Mandarin/Cantonese)
- **Regional accent preferences** - Different English accents (US/UK/AU)

### Implementation Steps

#### 1. Add Language Selection HTML

```html
<!-- Add this BEFORE the toggle slider -->
<div class="radio-group">
    <label>選擇語言 | Select Language:</label>
    <label class="radio-label">
        <input type="radio" name="chineseLanguage" value="zh-CN" id="mandarinRadio" checked>
        <span>🇨🇳 普通話 Mandarin</span>
    </label>
    <label class="radio-label">
        <input type="radio" name="chineseLanguage" value="zh-HK" id="cantoneseRadio">
        <span>🇭🇰 粵語 Cantonese</span>
    </label>
</div>
```

**Key Points:**
- Both radio inputs must share the same `name` attribute for mutual exclusivity
- Use `value` attribute to store the language code (e.g., 'zh-CN', 'zh-HK', 'en-US', 'en-GB')
- Set one radio button as `checked` by default

#### 2. Add CSS Styling (from section 1 above)

Copy the `.radio-group` and `.radio-label` styles from the CSS section above.

#### 3. Update Constructor

```javascript
constructor() {
    // ... existing properties ...

    // Language selection radio buttons
    this.mandarinRadio = document.getElementById('mandarinRadio');
    this.cantoneseRadio = document.getElementById('cantoneseRadio');

    // ... rest of constructor ...
}
```

#### 4. Add Event Listeners for Language Changes

```javascript
initializeEventListeners() {
    // ... existing listeners ...

    // Language radio button change handlers
    this.mandarinRadio.addEventListener('change', () => {
        if (this.mandarinRadio.checked) {
            console.log('🔄 Switched to Mandarin (zh-CN)');
            this.updateStatus('切換至普通話 Switched to Mandarin');

            // Restart playback with new voice if currently playing
            if (this.isPlaying) {
                this.stop();
                setTimeout(() => this.play(), 100);
            }
        }
    });

    this.cantoneseRadio.addEventListener('change', () => {
        if (this.cantoneseRadio.checked) {
            console.log('🔄 Switched to Cantonese (zh-HK)');
            this.updateStatus('切換至粵語 Switched to Cantonese');

            // Restart playback with new voice if currently playing
            if (this.isPlaying) {
                this.stop();
                setTimeout(() => this.play(), 100);
            }
        }
    });
}
```

**Important:** When language changes during playback:
1. Stop current speech (`this.stop()`)
2. Wait 100ms for cleanup
3. Restart from current position (`this.play()`)

#### 5. Update Voice Selection in `speakCurrentSentence()`

Replace the static `this.utterance.lang = 'en-US'` with dynamic language selection:

```javascript
speakCurrentSentence() {
    // ... existing code ...

    // Create speech utterance
    this.utterance = new SpeechSynthesisUtterance(textToSpeak);
    this.utterance.rate = parseFloat(this.speedSelect.value);
    this.utterance.pitch = 1;
    this.utterance.volume = 1;

    // DYNAMIC LANGUAGE SELECTION
    const selectedLang = this.mandarinRadio.checked ? 'zh-CN' : 'zh-HK';
    this.utterance.lang = selectedLang;

    console.log('🎤 Selected language:', selectedLang);

    // Voice selection with language-specific filtering
    const voices = speechSynthesis.getVoices();
    console.log('🔊 Total voices available:', voices.length);

    if (voices.length > 0) {
        // Priority 1: Google voices with EXACT language match
        let selectedVoice = voices.find(voice =>
            voice.lang === selectedLang && voice.name.includes('Google')
        );

        // Priority 2: Enhanced/Premium voices with EXACT match
        if (!selectedVoice) {
            selectedVoice = voices.find(voice =>
                voice.lang === selectedLang &&
                (voice.name.includes('Enhanced') || voice.name.includes('Premium'))
            );
        }

        // Priority 3: Any EXACT language match
        if (!selectedVoice) {
            selectedVoice = voices.find(voice => voice.lang === selectedLang);
        }

        // Priority 4: StartsWith match (for regional variants)
        if (!selectedVoice) {
            selectedVoice = voices.find(voice => voice.lang.startsWith(selectedLang));
        }

        if (selectedVoice) {
            this.utterance.voice = selectedVoice;
            console.log('✅ Using voice:', selectedVoice.name, selectedVoice.lang);
        } else {
            console.log('❌ No matching voice, using browser default');
        }
    }

    // ... rest of speech synthesis code ...
}
```

### Voice Selection Priority Logic

The system uses a **4-tier fallback strategy** to find the best available voice:

1. **Google voices** (exact match) - High quality, cloud-based
2. **Enhanced/Premium voices** (exact match) - System-provided premium voices
3. **Any voice with exact language code** - Standard system voices
4. **StartsWith match** - Catches regional variants (e.g., zh-CN-Liaoning)

**Example language codes:**
- Mandarin Chinese: `zh-CN`
- Cantonese Chinese: `zh-HK`
- English US: `en-US`
- English UK: `en-GB`
- English Australia: `en-AU`
- Spanish Spain: `es-ES`
- Spanish Mexico: `es-MX`

### Common Use Cases

#### Example 1: Chinese (Mandarin/Cantonese)

```javascript
// HTML
<input type="radio" name="chineseLang" value="zh-CN" id="mandarinRadio" checked>
<input type="radio" name="chineseLang" value="zh-HK" id="cantoneseRadio">

// JavaScript
const selectedLang = this.mandarinRadio.checked ? 'zh-CN' : 'zh-HK';
this.utterance.lang = selectedLang;
```

#### Example 2: English (US/UK)

```javascript
// HTML
<input type="radio" name="englishLang" value="en-US" id="usRadio" checked>
<input type="radio" name="englishLang" value="en-GB" id="ukRadio">

// JavaScript
const selectedLang = this.usRadio.checked ? 'en-US' : 'en-GB';
this.utterance.lang = selectedLang;
```

#### Example 3: Spanish (Spain/Mexico)

```javascript
// HTML
<input type="radio" name="spanishLang" value="es-ES" id="spainRadio" checked>
<input type="radio" name="spanishLang" value="es-MX" id="mexicoRadio">

// JavaScript
const selectedLang = this.spainRadio.checked ? 'es-ES' : 'es-MX';
this.utterance.lang = selectedLang;
```

### Testing Language Selection

To verify language selection is working:

1. **Log available voices:**
   ```javascript
   const voices = speechSynthesis.getVoices();
   console.log('All voices:', voices.map(v => `${v.name} (${v.lang})`));
   ```

2. **Check selected voice:**
   ```javascript
   console.log('Selected voice:', this.utterance.voice?.name, this.utterance.voice?.lang);
   ```

3. **Test during playback:**
   - Start playing text
   - Switch language radio button
   - Verify speech restarts with new accent/language

### Browser Compatibility Notes

- **Chrome/Edge**: Best support, includes Google voices
- **Safari/iOS**: Excellent Enhanced voices for many languages
- **Firefox**: Limited voice selection, may only have 1-2 voices per language

Voice availability varies by:
- Operating system (macOS, Windows, iOS, Android)
- Browser type and version
- Installed language packs

## Implementation Checklist for Other Apps

To implement this feature in another app:

### Basic Speech Features
1. ✅ Add toggle slider HTML with checkbox input
2. ✅ Add CSS styles for toggle slider (.switch, .slider, transitions)
3. ✅ Add Play/Pause button with dynamic class switching
4. ✅ Add button CSS (.success-button, .secondary-button)
5. ✅ Set up speech mode state variable (`this.speechMode`)
6. ✅ Add event listener for toggle change
7. ✅ Add event listener for play button click
8. ✅ Implement `speakCurrentSentence()` with mode check
9. ✅ Implement `startWordHighlighting()` for synchronized visual feedback
10. ✅ Implement `pacerOnlySentence()` for silent mode
11. ✅ Implement play/pause/stop state management
12. ✅ Implement `updateButtonStates()` for UI updates
13. ✅ Add text preprocessing (sentence splitting, cleaning)
14. ✅ Add voice selection logic
15. ✅ Add error handling for speech synthesis
16. ✅ Test timing synchronization and adjust constants

### Multi-Language Features (Optional)
17. ✅ Add language selection radio button HTML
18. ✅ Add CSS styles for radio groups (.radio-group, .radio-label)
19. ✅ Add radio button references in constructor
20. ✅ Add event listeners for radio button changes
21. ✅ Update `speakCurrentSentence()` with dynamic language selection
22. ✅ Implement 4-tier voice selection fallback logic
23. ✅ Add restart-on-language-change functionality
24. ✅ Test with multiple language codes
25. ✅ Add logging for voice debugging

---

## Notes

- The system uses **sentence-level** processing rather than word-by-word TTS for better speech quality
- Timing is **pre-calculated** based on word count and playback speed for smooth highlighting
- The `actualTimingAdjustment` property allows the system to **learn** from actual speech timing and improve synchronization
- Both modes (pacer and speech) use the **same highlighting logic** for consistency
- The 150ms startup delay accounts for browser TTS initialization time
- The 0.85x adjustment factor compensates for cumulative timing drift over longer sentences
